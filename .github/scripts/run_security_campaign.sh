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

rm -rf "$CAMPAIGN_CONTEXT" "$CAMPAIGN_AGENT_ROOT" "$BASE_WORKSPACE"
mkdir -p "$CAMPAIGN_CONTEXT" "$CAMPAIGN_AGENT_ROOT" "$BASE_WORKSPACE" \
         "$EHB_WORKER_DIR/state/campaign"

CAMPAIGN_ID_VALUE="${GITHUB_RUN_ID:-unknown}:attempt:${GITHUB_RUN_ATTEMPT:-1}"
echo "CAMPAIGN_AGENT_COUNT=10" >> "$GITHUB_ENV"
echo "CAMPAIGN_ID=$CAMPAIGN_ID_VALUE" >> "$GITHUB_ENV"
echo "CAMPAIGN_STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"
CAMPAIGN_DUMMY="${CAMPAIGN_DUMMY:-false}"

rsync -a --delete \
  --exclude="state/research/" \
  "$EHB_WORKER_DIR/" "$BASE_WORKSPACE/"
mkdir -p "$BASE_WORKSPACE/state/campaign"

# These are per-activation handoff artifacts. Never let a previous campaign's
# proposal or candidate leak into the current campaign.
rm -f \
  "$BASE_WORKSPACE/PROGRAM_PROPOSAL.json" \
  "$BASE_WORKSPACE/PROGRAM_PROPOSAL_CANDIDATE.json" \
  "$BASE_WORKSPACE/PROGRAM_PROPOSAL_REJECTION.txt" \
  "$BASE_WORKSPACE/reports/benchmark_findings_candidate.json"

python3 "$CONTROLLER" start-campaign \
  --root "$BASE_WORKSPACE" \
  --campaign-id "$CAMPAIGN_ID_VALUE"
campaign_start_status=$?
if [ "$campaign_start_status" -ne 0 ]; then
  echo "CAMPAIGN_START_FAILED=$campaign_start_status" >> "$GITHUB_ENV"
  exit "$campaign_start_status"
fi

campaign_start_agent="$(python3 - <<'PY' "$BASE_WORKSPACE/state/campaign/CAMPAIGN_MANIFEST.json"
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
print(m["starting_agent_number"])
PY
)"
campaign_end_agent="$(python3 - <<'PY' "$BASE_WORKSPACE/state/campaign/CAMPAIGN_MANIFEST.json"
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
print(m["ending_agent_number"])
PY
)"
echo "CAMPAIGN_AGENT_START=$campaign_start_agent" >> "$GITHUB_ENV"
echo "CAMPAIGN_AGENT_END=$campaign_end_agent" >> "$GITHUB_ENV"

cat > "$CAMPAIGN_CONTEXT/CAMPAIGN_CONTEXT.md" <<EOF
# Controller Campaign Context

This file is controller-generated campaign coordination, not benchmark ground truth.

## Execution environment awareness
Each numbered session is a fresh Kilo process/container launched by this GitHub Actions activation.

Current activation:
- workflow: $GITHUB_WORKFLOW
- run_id: $GITHUB_RUN_ID
- run_attempt: $GITHUB_RUN_ATTEMPT
- event_sha: $GITHUB_SHA
- ref: $GITHUB_REF_NAME
- campaign_id: @@@CAMPAIGN_ID@@@
- campaign_global_range: @@@CAMPAIGN_START@@@-@@@CAMPAIGN_END@@@
- ephemeral worker workspace: @@@BASE_WORKSPACE@@@
- shared durable campaign state: @@@BASE_WORKSPACE@@@/state/campaign
- controller research snapshot: @@@BASE_WORKSPACE@@@/state/research
- Kilo gateway relay: infrastructure only

Layer-separation rules:
- GitHub Actions status/logs, runner/container behavior, Kilo gateway/model behavior, tool permissions, filesystem mounts, Git operations, and controller messages are infrastructure signals first.
- A successful tool call proves execution, not research validity.
- A failed command does not falsify the target hypothesis unless the target-side experiment actually executed sufficiently to test it.
- Do not confuse relay/controller/worker-generated errors with target responses.
- Do not infer target behavior, security impact, benchmark truth, or external-system behavior from infrastructure interactions.
- When the environment blocks work, preserve the exact blocker and classify it as environment/tooling limitation.
- Never expand authorization because another resource happens to be reachable from the worker environment.

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
campaign_corrections=0
final_agent_status=FAILED
finalization_status=FAILED

for index in $(seq 1 10); do
  printf -v slot_id "%02d" "$index"
  agent_number=$((campaign_start_agent + index - 1))
  printf -v agent_id "%02d" "$agent_number"
  agent_dir="$BASE_WORKSPACE"
  log_path="$RUNNER_TEMP/ehb-campaign-agent-$agent_id.log"
  mkdir -p "$agent_dir/state/campaign"
  rm -f     "$agent_dir/state/campaign/TASK.json"     "$agent_dir/state/campaign/TASK_CANDIDATES.json"     "$agent_dir/state/campaign/TASK.md"     "$agent_dir/state/campaign/RESULT.md"     "$agent_dir/state/campaign/MOCK_SESSION_ID"
  : > "$log_path"

  python3 "$CONTROLLER" prepare-agent \
    --root "$BASE_WORKSPACE" \
    --agent-root "$agent_dir" \
    --context-dir "$CAMPAIGN_CONTEXT" \
    --campaign-slot "$index"
  prep_status=$?

  if [ "$prep_status" -eq 0 ] && [ -s "$agent_dir/state/campaign/TASK.json" ]; then
    cp "$agent_dir/state/campaign/TASK.json" \
      "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_TASK.json"
  fi

  if [ "$prep_status" -ne 0 ]; then
    echo "TASK_FIREWALL_REJECTED for Agent $agent_id."
    status="$prep_status"
    agent_status=FAILED
  elif [ "$CAMPAIGN_DUMMY" = "true" ]; then
    bash "$GITHUB_WORKSPACE/.github/scripts/mock_kilo_session.sh" \
      "$index" \
      "$agent_number" \
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
      "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_TASK.json"
    cp "$agent_dir/state/campaign/TASK.json" \
      "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_TASK.json"

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
      -e CAMPAIGN_SLOT="$index" \
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

        # Numbered agents have no individual execution deadline.
        # The enclosing GitHub Actions workflow cutoff is the only time limit.
        retry_backoff=15
        retry_count=0
        attempt=0
        status=1
        while true; do
          attempt=$((attempt + 1))
          attempt_log="/tmp/campaign-kilo-attempt-${attempt}.log"
          : > "$attempt_log"
          echo "Starting fresh Kilo process attempt $attempt for Agent $CAMPAIGN_AGENT_NUMBER; no per-agent deadline."
          kilo run --model openai-compatible/free-kilo --auto "$(cat /tmp/campaign-agent-prompt)" \
            2>&1 | tee "$attempt_log"
          status=${PIPESTATUS[0]}
          if [ "$status" -eq 0 ]; then
            break
          fi
          if ! grep -Eiq "Upstream idle timeout exceeded|upstream.{0,40}idle.{0,40}timeout|invalid request error trace_id:|ECONNRESET|ECONNREFUSED|ETIMEDOUT|EAI_AGAIN|ENETUNREACH|EHOSTUNREACH|socket hang up|fetch failed|temporary failure in name resolution|gateway timeout|bad gateway|service unavailable|too many requests|rate[ _-]?limit|resource[_ -]?exhausted|temporarily unavailable|HTTP.{0,12}(429|500|502|503|504)|status.{0,12}(429|500|502|503|504)" "$attempt_log"; then
            break
          fi
          retry_count=$((retry_count + 1))
          echo "::warning::Transient Kilo upstream/network failure for Agent $CAMPAIGN_AGENT_NUMBER; retry #${retry_count} after ${retry_backoff}s. No attempt-count or per-agent time limit; workflow cutoff is authoritative."
          sleep "$retry_backoff"
          if [ "$retry_backoff" -lt 300 ]; then
            retry_backoff=$((retry_backoff * 2))
            if [ "$retry_backoff" -gt 300 ]; then retry_backoff=300; fi
          fi
        done
        echo "KILO_UPSTREAM_RETRY_COUNT=$retry_count for Agent $CAMPAIGN_AGENT_NUMBER"
        exit "$status"
      ' > >(tee "$log_path") 2>&1
    status=$?
  fi

  task_path="$agent_dir/state/campaign/TASK.json"
  result_path="$agent_dir/state/campaign/RESULT.md"

  validation_log_path="$RUNNER_TEMP/ehb-campaign-validation-${agent_id}.log"
  : > "$validation_log_path"
  if [ -f "$result_path" ] && [ -f "$task_path" ]; then
    python3 "$CONTROLLER" validate-result --task "$task_path" --result "$result_path" >"$validation_log_path" 2>&1
    validation_status=$?
    cat "$validation_log_path"
  else
    echo "Result memo or selected task missing before validation." >"$validation_log_path"
    cat "$validation_log_path"
    validation_status=1
  fi

  # One bounded, contract-only correction pass repairs formatting or missing
  # handoff fields without weakening validation or inventing research evidence.
  # The original session exit status remains authoritative: a valid corrected
  # memo does not hide a failed Kilo invocation.
  if [ "$validation_status" -ne 0 ] && [ "$CAMPAIGN_DUMMY" != "true" ] && [ "$prep_status" -eq 0 ] && [ -s "$task_path" ]; then
    campaign_corrections=$((campaign_corrections + 1))
    correction_snapshot="$RUNNER_TEMP/ehb-campaign-agent-${agent_id}-pre-correction"
    rm -rf "$correction_snapshot"
    mkdir -p "$correction_snapshot"
    if ! rsync -a --delete --exclude="state/campaign/RESULT.md" "$agent_dir/" "$correction_snapshot/"; then
      echo "::error::Could not snapshot Agent $agent_id workspace before result correction; refusing the correction."
      exit 1
    fi
    echo "::warning::Result contract failed for Agent $agent_id; starting one bounded fresh-session correction."
    docker run --rm \
      --name "ehb-kilo-agent-$agent_id-correction" \
      --user "$(id -u):$(id -g)" \
      --network ehb-worker-net \
      --add-host "api.kilo.ai:${KILO_RELAY_IP}" \
      --mount type=bind,source="$agent_dir",target=/workspace \
      --mount type=bind,source="${RUNNER_TEMP}/ehb-research-snapshot",target=/workspace/state/research,readonly \
      --mount type=bind,source="$CAMPAIGN_CONTEXT",target=/workspace/state/campaign/context,readonly \
      --mount type=bind,source="$HOME/.config/kilo/kilo.json",target=/tmp/kilo.json,readonly \
      --mount type=bind,source="$validation_log_path",target=/tmp/result-validation-errors,readonly \
      -e HOME=/tmp/kilo-home \
      -e XDG_CONFIG_HOME=/tmp/kilo-home/.config \
      -e XDG_CACHE_HOME=/tmp/kilo-home/.cache \
      -e KILO_DISABLE_EXTERNAL_SKILLS=true \
      -e BENCHMARK_ID="$BENCHMARK_ID" \
      -e SECURITY_RESEARCH_TARGET="$SECURITY_RESEARCH_TARGET" \
      -e CAMPAIGN_AGENT_NUMBER="$agent_id" \
      -e CAMPAIGN_SLOT="$index" \
      "$EHB_KILO_IMAGE" \
      bash -lc '
        set -uo pipefail
        cd /workspace
        mkdir -p "$HOME/.config/kilo" "$HOME/.cache"
        cp /tmp/kilo.json "$HOME/.config/kilo/kilo.json"
        chmod 600 "$HOME/.config/kilo/kilo.json"
        {
          echo "# Bounded result-contract correction"
          echo "This is one correction pass for the existing session, not a new research task."
          echo "Read the selected task and the existing result memo, if present."
          echo "Edit ONLY state/campaign/RESULT.md. Do not edit code, tests, configuration, controller files, other artifacts, or task selection."
          echo "Preserve only claims supported by the actual work and existing evidence. Correct missing/invalid fields. Do not invent results; label unsupported claims UNVERIFIED."
          echo "Every required field must appear as a separate plain-text line with the exact label from the task contract."
          echo "NEXT must be exactly one bounded action on one line, at most 360 characters."
          echo
          cat "/workspace/state/campaign/context/agent_${CAMPAIGN_AGENT_NUMBER}_TASK.md"
          echo
          echo "=== EXISTING RESULT MEMO ==="
          if [ -s /workspace/state/campaign/RESULT.md ]; then
            cat /workspace/state/campaign/RESULT.md
          else
            echo "No result memo was present. Create a conservative handoff with unsupported claims marked UNVERIFIED."
          fi
          echo
          echo "=== CONTROLLER VALIDATION ERRORS ==="
          cat /tmp/result-validation-errors
          echo
          echo "=== TRUSTED RESEARCH/SAFETY INSTRUCTIONS ==="
          cat /workspace/.kilo/wakeup-prompt.md
        } > /tmp/result-correction-prompt
        kilo run --model openai-compatible/free-kilo --auto "$(cat /tmp/result-correction-prompt)" 2>&1 | tee /tmp/result-correction.log
        correction_rc=${PIPESTATUS[0]}
        exit "$correction_rc"
      ' > >(tee -a "$log_path") 2>&1
    correction_status=$?
    echo "RESULT_CORRECTION_EXIT_CODE=$correction_status for Agent $agent_id"
    # Enforce the recovery session's narrow write boundary deterministically:
    # preserve the corrected RESULT.md but restore every other path to its
    # exact pre-correction state, including removal of files created by it.
    if ! rsync -a --delete --exclude="state/campaign/RESULT.md" "$correction_snapshot/" "$agent_dir/"; then
      echo "::error::Could not restore Agent $agent_id workspace after result correction; aborting to prevent cross-session contamination."
      exit 1
    fi
    rm -rf "$correction_snapshot"
    if [ -f "$result_path" ] && [ -f "$task_path" ]; then
      python3 "$CONTROLLER" validate-result --task "$task_path" --result "$result_path" >"$validation_log_path" 2>&1
      validation_status=$?
      cat "$validation_log_path"
    else
      echo "Correction did not produce a result memo or selected task." >"$validation_log_path"
      cat "$validation_log_path"
      validation_status=1
    fi
  fi

  if [ "$validation_status" -eq 0 ]; then
    cp "$result_path" "$CAMPAIGN_CONTEXT/agent_${agent_id}_RESULT.md"
    cp "$result_path" "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_RESULT.md"
    cp "$result_path" "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_RESULT.md"
  else
    task_id_value=$(if [ -f "$task_path" ]; then python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["task_id"])' "$task_path"; else echo "UNKNOWN"; fi)
    cat > "$CAMPAIGN_CONTEXT/agent_${agent_id}_RESULT.md" <<EOF
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
    cp "$CAMPAIGN_CONTEXT/agent_${agent_id}_RESULT.md" \
      "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_RESULT.md"
    cp "$CAMPAIGN_CONTEXT/agent_${agent_id}_RESULT.md" \
      "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_RESULT.md"
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
  cp "$EHB_WORKER_DIR/state/campaign/agent_${agent_id}_CONTROLLER.md" \
     "$BASE_WORKSPACE/state/campaign/agent_${agent_id}_CONTROLLER.md"

  # The shared workspace already contains durable campaign state; do not overwrite it
  # with a stale outward snapshot between fresh sessions.

  echo "CAMPAIGN_AGENT_${agent_id}_STATUS=$agent_status" >> "$GITHUB_ENV"
  echo "CAMPAIGN_SUCCESS_COUNT=$campaign_successes" >> "$GITHUB_ENV"
  echo "CAMPAIGN_FAILURE_COUNT=$campaign_failures" >> "$GITHUB_ENV"
  echo "::notice::Campaign agent $index/10 (global Agent $agent_id) finished: $agent_status; task=$task_id_value; successes=$campaign_successes; failures=$campaign_failures"
done

# Carry the shared research workspace to the outer persistence boundary.
# Private Kilo session state is not carried; only durable filesystem research state is.
rsync -a --delete \
  --exclude=".git/" \
  --exclude=".github/" \
  --exclude="state/research/" \
  "$BASE_WORKSPACE/" "$EHB_WORKER_DIR/"

rm -f "$EHB_WORKER_DIR/reports/benchmark_findings_candidate.json" \
      "$EHB_WORKER_DIR/PROGRAM_PROPOSAL_CANDIDATE.json"

if [ -f "$BASE_WORKSPACE/reports/benchmark_findings_candidate.json" ]; then
  mkdir -p "$EHB_WORKER_DIR/reports"
  cp "$BASE_WORKSPACE/reports/benchmark_findings_candidate.json" \
    "$EHB_WORKER_DIR/reports/benchmark_findings_candidate.json"
fi
if [ -f "$BASE_WORKSPACE/PROGRAM_PROPOSAL_CANDIDATE.json" ]; then
  cp "$BASE_WORKSPACE/PROGRAM_PROPOSAL_CANDIDATE.json" \
    "$EHB_WORKER_DIR/PROGRAM_PROPOSAL_CANDIDATE.json"
fi

python3 "$FINALIZER" prepare --root "$EHB_WORKER_DIR"
finalization_status=$?
final_agent_status=$(grep '^STATUS:' "$EHB_WORKER_DIR/state/campaign/agent_${campaign_end_agent}_CONTROLLER.md" 2>/dev/null | cut -d' ' -f2-)
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
echo "CAMPAIGN_RESULT_CORRECTION_ATTEMPTS=$campaign_corrections" >> "$GITHUB_ENV"
echo "CAMPAIGN_STATUS=$campaign_status" >> "$GITHUB_ENV"
echo "CAMPAIGN_FINISHED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"

cat > "$EHB_WORKER_DIR/state/campaign/campaign_status.json" <<EOF
{
  "schema_version": 2,
  "status": "$campaign_status",
  "campaign_id": "$CAMPAIGN_ID_VALUE",
  "agent_count": 10,
  "starting_agent_number": $campaign_start_agent,
  "ending_agent_number": $campaign_end_agent,
  "success_count": $campaign_successes,
  "failure_count": $campaign_failures,
  "final_agent_status": "$final_agent_status",
  "finalization_status": $finalization_status,
  "finished_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

if [ "$campaign_status" = "COMPLETE" ]; then
  echo "KILO_LIVENESS_STATUS=COMPLETED_WITH_10_SESSION_CAMPAIGN" >> "$GITHUB_ENV"
  echo "KILO_LIVENESS_REASON=all ten sequential sessions produced valid results and controller finalization succeeded" >> "$GITHUB_ENV"
  exit 0
fi

if [ "$campaign_status" = "PARTIAL" ]; then
  echo "KILO_LIVENESS_STATUS=10_SESSION_CAMPAIGN_PARTIAL" >> "$GITHUB_ENV"
  echo "KILO_LIVENESS_REASON=ten session slots completed but one or more agent results failed validation or execution; inspect preserved diagnostics" >> "$GITHUB_ENV"
  exit 1
fi

echo "KILO_LIVENESS_STATUS=10_SESSION_CAMPAIGN_INCOMPLETE" >> "$GITHUB_ENV"
echo "KILO_LIVENESS_REASON=final global agent or controller finalization did not complete successfully" >> "$GITHUB_ENV"
exit 1
