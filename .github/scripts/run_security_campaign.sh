#!/usr/bin/env bash
# Controller-owned sequential ten-session campaign.
# Kilo never dispatches another Kilo session; this script owns the sequence.
set +e

EHB_WORKER_DIR="${RUNNER_TEMP:?}/ehb-worker"
CAMPAIGN_CONTEXT="${RUNNER_TEMP:?}/ehb-campaign-context"
CAMPAIGN_AGENT_ROOT="${RUNNER_TEMP:?}/ehb-campaign-agents"
BASE_WORKSPACE="${RUNNER_TEMP:?}/ehb-campaign-base"
CONTROLLER="${GITHUB_WORKSPACE:?}/.github/scripts/campaign_controller.py"
FINALIZER="${GITHUB_WORKSPACE:?}/.github/scripts/finalize_campaign.py"

rm -rf "$CAMPAIGN_CONTEXT" "$CAMPAIGN_AGENT_ROOT" "$BASE_WORKSPACE" \
       "$EHB_WORKER_DIR/state/campaign"
mkdir -p "$CAMPAIGN_CONTEXT" "$CAMPAIGN_AGENT_ROOT" "$BASE_WORKSPACE" \
         "$EHB_WORKER_DIR/state/campaign"

echo "CAMPAIGN_AGENT_COUNT=10" >> "$GITHUB_ENV"
echo "CAMPAIGN_AGENT_TIMEOUT_MINUTES=28" >> "$GITHUB_ENV"
echo "CAMPAIGN_STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"
CAMPAIGN_DUMMY="${CAMPAIGN_DUMMY:-false}"

rsync -a --delete \
  --exclude="state/research/" \
  "$EHB_WORKER_DIR/" "$BASE_WORKSPACE/"
mkdir -p "$BASE_WORKSPACE/state/campaign"

cat > "$CAMPAIGN_CONTEXT/CAMPAIGN_CONTEXT.md" <<'EOF'
# Controller Campaign Context

This file is controller-generated campaign coordination, not benchmark ground truth.

## Communication boundary
- Each numbered session is a fresh Kilo process/container.
- Prior agent claims are hypotheses until independently verified.
- Durable communication is limited to controller-selected TASK.json and compact RESULT.md memos.
- The worker must not inspect hidden benchmark implementation, evaluator state, or controller-only files.

## Session contract
ONE primary question.
ONE bounded objective.
ONE meaningful deliverable.
ONE evidence gate.
ONE explicit stop condition.
ZERO intentional scope expansion.

## Safety
- Stay inside the explicitly authorized worker target and safe research primitives.
- Do not access the hidden evaluator.
- Do not attempt credential theft, persistence, destructive actions, evasion, or unrelated systems.
- Do not commit or push.
- Do not launch another Kilo session, workflow, recursive agent, or hidden campaign.
EOF

campaign_successes=0
campaign_failures=0
final_agent_status=FAILED
finalization_status=FAILED

for index in $(seq 1 10); do
  printf -v agent_id "%02d" "$index"
  agent_dir="$CAMPAIGN_AGENT_ROOT/agent_$agent_id"
  log_path="$RUNNER_TEMP/ehb-campaign-agent-$agent_id.log"
  rm -rf "$agent_dir"
  mkdir -p "$agent_dir"
  cp -a "$BASE_WORKSPACE/." "$agent_dir/"
  mkdir -p "$agent_dir/state/campaign"
  : > "$log_path"

  python3 "$CONTROLLER" prepare-agent \
    --root "$BASE_WORKSPACE" \
    --agent-root "$agent_dir" \
    --context-dir "$CAMPAIGN_CONTEXT" \
    --agent-number "$index"
  prep_status=$?

  if [ "$prep_status" -ne 0 ]; then
    echo "TASK_FIREWALL_REJECTED for Agent $agent_id."
    status="$prep_status"
    agent_status=FAILED
  elif [ "$CAMPAIGN_DUMMY" = "true" ]; then
    bash "$GITHUB_WORKSPACE/.github/scripts/mock_kilo_session.sh" \
      "$index" \
      "$agent_dir/state/campaign/TASK.json" \
      "$agent_dir/state/campaign/RESULT.md"
    status=$?
    if [ -f "$agent_dir/state/campaign/MOCK_SESSION_ID" ]; then
      cp "$agent_dir/state/campaign/MOCK_SESSION_ID" \
        "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_MOCK_SESSION_ID"
      cp "$agent_dir/state/campaign/MOCK_SESSION_ID" \
        "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_MOCK_SESSION_ID"
    fi
  else
    cp "$agent_dir/state/campaign/TASK.json" \
      "$EHB_WORKER_DIR/state/campaign/agent_$agent_id_TASK.json"
    cp "$agent_dir/state/campaign/TASK.json" \
      "$BASE_WORKSPACE/state/campaign/agent_$agent_id_TASK.json"

    docker run --rm \
      --name "ehb-kilo-agent-$agent_id" \
      --user "$(id -u):$(id -g)" \
      --network ehb-worker-net \
      --add-host "api.kilo.ai:${KILO_RELAY_IP}" \
      --mount type=bind,source="$agent_dir",target=/workspace \
      --mount type=bind,source="${RUNNER_TEMP}/ehb-research-snapshot",target=/workspace/state/research,readonly \
      --mount type=bind,source="$CAMPAIGN_CONTEXT",target=/workspace/state/campaign/context,readonly \
      --mount type=bind,source="$HOME/.config/kilo/kilo.json",target=/tmp/kilo.json,readonly \
      -e HOME=/tmp/kilo-home \
      -e XDG_CONFIG_HOME=/tmp/kilo-home/.config \
      -e XDG_CACHE_HOME=/tmp/kilo-home/.cache \
      -e KILO_DISABLE_EXTERNAL_SKILLS=true \
      -e BENCHMARK_ID="$BENCHMARK_ID" \
      -e SECURITY_RESEARCH_TARGET="$SECURITY_RESEARCH_TARGET" \
      -e CAMPAIGN_AGENT_NUMBER="$agent_id" \
      "$EHB_KILO_IMAGE" \
      bash -lc '
        set -uo pipefail
        cd /workspace
        mkdir -p "$HOME/.config/kilo" "$HOME/.cache"
        cp /tmp/kilo.json "$HOME/.config/kilo/kilo.json"
        chmod 600 "$HOME/.config/kilo/kilo.json"

        {
          cat "/workspace/state/campaign/context/agent_${CAMPAIGN_AGENT_NUMBER}_TASK.md"
          echo
          echo "Read /workspace/state/campaign/context/CAMPAIGN_CONTEXT.md."
          echo "Read only durable prior agent_*_RESULT.md memos that are present in the campaign context."
          echo "Execute exactly the selected task. Do not broaden it."
          echo
          cat /workspace/.kilo/wakeup-prompt.md
        } > /tmp/campaign-agent-prompt

        # Exactly one Kilo invocation for this numbered session.
        timeout --foreground --signal=TERM --kill-after=60s 28m \
          kilo run --model openai-compatible/free-kilo --auto "$(cat /tmp/campaign-agent-prompt)"
        exit $?
      ' > >(tee "$log_path") 2>&1
    status=$?
  fi

  task_path="$agent_dir/state/campaign/TASK.json"
  result_path="$agent_dir/state/campaign/RESULT.md"

  if [ -f "$result_path" ] && [ -f "$task_path" ]; then
    python3 "$CONTROLLER" validate-result --task "$task_path" --result "$result_path"
    validation_status=$?
  else
    validation_status=1
  fi

  if [ "$validation_status" -eq 0 ]; then
    cp "$result_path" "$CAMPAIGN_CONTEXT/agent_$agent_id_RESULT.md"
    cp "$result_path" "$EHB_WORKER_DIR/state/campaign/agent_$agent_id_RESULT.md"
    cp "$result_path" "$BASE_WORKSPACE/state/campaign/agent_$agent_id_RESULT.md"
  else
    task_id_value=$(if [ -f "$task_path" ]; then python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["task_id"])' "$task_path"; else echo "UNKNOWN"; fi)
    cat > "$CAMPAIGN_CONTEXT/agent_$agent_id_RESULT.md" <<EOF
OUTCOME_CLASS: INFRASTRUCTURE_FAILURE
TASK_ID: $task_id_value
PRIMARY_QUESTION: Controller could not validate the session result.
BOTTLENECK: Result-contract or execution failure.
INFORMATION_GAP: What evidence, if any, the session produced.
BOUNDED_ACTION: Preserve diagnostics without fabricating research evidence.
DELIVERABLE: Failure handoff.
SUCCESS_EVIDENCE_CRITERION: Failure remains explicitly unverified.
STOP_CONDITION: Stop this session and let the next controller-selected task proceed.
OUT_OF_SCOPE: Synthetic research claims.
VERIFICATION_REQUIREMENT: Future activation or a fresh session must re-run any decision-relevant question.
CHANGED: false
VERIFIED: controller preserved failure diagnostics
UNVERIFIED: session result
OBSERVED_EFFECT: No valid result memo was available.
UNCERTAINTY_TARGETED: Session outcome.
UNCERTAINTY_REDUCED: none
DECISION: UNVERIFIED
NEXT: Reassess the highest-value unresolved task from durable evidence.
EOF
    cp "$CAMPAIGN_CONTEXT/agent_$agent_id_RESULT.md" \
      "$EHB_WORKER_DIR/state/campaign/agent_$agent_id_RESULT.md"
    cp "$CAMPAIGN_CONTEXT/agent_$agent_id_RESULT.md" \
      "$BASE_WORKSPACE/state/campaign/agent_$agent_id_RESULT.md"
    validation_status=1
  fi

  if [ "$status" -eq 0 ] && [ "$validation_status" -eq 0 ]; then
    campaign_successes=$((campaign_successes + 1))
    agent_status=SUCCESS
  else
    campaign_failures=$((campaign_failures + 1))
    agent_status=FAILED
  fi

  task_id_value=$(python3 - <<'PY' "$task_path" 2>/dev/null
import json,sys
try:
    print(json.load(open(sys.argv[1], encoding="utf-8")).get("task_id","UNKNOWN"))
except Exception:
    print("UNKNOWN")
PY
)

  session_id="$(cat "$agent_dir/state/campaign/MOCK_SESSION_ID" 2>/dev/null || true)"
  cat > "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_CONTROLLER.md" <<EOF
AGENT_NUMBER: ${agent_id}
TASK_ID: ${task_id_value}
SESSION_ID: ${session_id}
STATUS: ${agent_status}
EXIT_CODE: ${status}
RESULT_VALID: $([ "${validation_status}" -eq 0 ] && echo true || echo false)
OBSERVED_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
AGENT_NUMBER: $agent_id
TASK_ID: $task_id_value
STATUS: $agent_status
EXIT_CODE: $status
RESULT_VALID: $([ "$validation_status" -eq 0 ] && echo true || echo false)
OBSERVED_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
  cp "$EHB_WORKER_DIR/state/campaign/agent_$agent_id_CONTROLLER.md" \
     "$BASE_WORKSPACE/state/campaign/agent_$agent_id_CONTROLLER.md"

  rsync -a --delete "$EHB_WORKER_DIR/state/campaign/" "$BASE_WORKSPACE/state/campaign/"

  echo "CAMPAIGN_AGENT_$agent_id_STATUS=$agent_status" >> "$GITHUB_ENV"
  echo "CAMPAIGN_SUCCESS_COUNT=$campaign_successes" >> "$GITHUB_ENV"
  echo "CAMPAIGN_FAILURE_COUNT=$campaign_failures" >> "$GITHUB_ENV"
  echo "::notice::Campaign agent $index/10 finished: $agent_status; task=$task_id_value; successes=$campaign_successes; failures=$campaign_failures"
done

rm -f "$EHB_WORKER_DIR/reports/benchmark_findings_candidate.json" \
      "$EHB_WORKER_DIR/PROGRAM_PROPOSAL_CANDIDATE.json"

if [ -f "$CAMPAIGN_AGENT_ROOT/agent_10/reports/benchmark_findings_candidate.json" ]; then
  mkdir -p "$EHB_WORKER_DIR/reports"
  cp "$CAMPAIGN_AGENT_ROOT/agent_10/reports/benchmark_findings_candidate.json" \
    "$EHB_WORKER_DIR/reports/benchmark_findings_candidate.json"
fi
if [ -f "$CAMPAIGN_AGENT_ROOT/agent_10/PROGRAM_PROPOSAL_CANDIDATE.json" ]; then
  cp "$CAMPAIGN_AGENT_ROOT/agent_10/PROGRAM_PROPOSAL_CANDIDATE.json" \
    "$EHB_WORKER_DIR/PROGRAM_PROPOSAL_CANDIDATE.json"
fi

python3 "$FINALIZER" prepare --root "$EHB_WORKER_DIR"
finalization_status=$?
final_agent_status=$(grep '^STATUS:' "$EHB_WORKER_DIR/state/campaign/agent_10_CONTROLLER.md" 2>/dev/null | cut -d' ' -f2-)
[ -n "$final_agent_status" ] || final_agent_status=FAILED

campaign_status=FAILED
if [ "$finalization_status" -eq 0 ] && [ "$final_agent_status" = "SUCCESS" ]; then
  if [ "$campaign_failures" -eq 0 ]; then
    campaign_status=COMPLETE
  else
    campaign_status=PARTIAL
  fi
fi

echo "CAMPAIGN_SUCCESS_COUNT=$campaign_successes" >> "$GITHUB_ENV"
echo "CAMPAIGN_FAILURE_COUNT=$campaign_failures" >> "$GITHUB_ENV"
echo "CAMPAIGN_STATUS=$campaign_status" >> "$GITHUB_ENV"
echo "CAMPAIGN_FINISHED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"

cat > "$EHB_WORKER_DIR/state/campaign/campaign_status.json" <<EOF
{
  "schema_version": 2,
  "status": "$campaign_status",
  "agent_count": 10,
  "success_count": $campaign_successes,
  "failure_count": $campaign_failures,
  "final_agent_status": "$final_agent_status",
  "finalization_status": $finalization_status,
  "finished_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

if [ "$campaign_status" = "COMPLETE" ] || [ "$campaign_status" = "PARTIAL" ]; then
  echo "KILO_LIVENESS_STATUS=COMPLETED_WITH_10_SESSION_CAMPAIGN" >> "$GITHUB_ENV"
  echo "KILO_LIVENESS_REASON=controller executed exactly ten numbered fresh sessions; failures were preserved as evidence" >> "$GITHUB_ENV"
  exit 0
fi

echo "KILO_LIVENESS_STATUS=10_SESSION_CAMPAIGN_INCOMPLETE" >> "$GITHUB_ENV"
echo "KILO_LIVENESS_REASON=agent_10 or controller finalization did not complete successfully" >> "$GITHUB_ENV"
exit 1
