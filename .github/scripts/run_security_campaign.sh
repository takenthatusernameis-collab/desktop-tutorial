#!/usr/bin/env bash
set +e

EHB_WORKER_DIR="$RUNNER_TEMP/ehb-worker"
mkdir -p "$EHB_WORKER_DIR/state/campaign"

campaign_failed=0
campaign_successes=0
echo "CAMPAIGN_AGENT_COUNT=10" >> "$GITHUB_ENV"
echo "CAMPAIGN_AGENT_TIMEOUT_MINUTES=28" >> "$GITHUB_ENV"
echo "CAMPAIGN_STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"

for index in $(seq 1 10); do
  case "$index" in
    1) role=FORENSICS ;;
    2) role=HYPOTHESIS_EXPANSION ;;
    3) role=ADVERSARIAL_FALSIFICATION ;;
    4) role=COVERAGE_ENGINEERING ;;
    5) role=DECISIVE_EXPERIMENT ;;
    6) role=INDEPENDENT_REPRODUCTION ;;
    7) role=ROBUSTNESS_STRESS ;;
    8) role=RESEARCH_SOFTWARE_RELIABILITY ;;
    9) role=SYNTHESIS_LEARNING ;;
    10) role=FINAL_RED_TEAM_HANDOFF ;;
  esac

  printf -v agent_id "%02d" "$index"
  log_path="$RUNNER_TEMP/ehb-campaign-agent-$agent_id.log"
  echo "STARTING FRESH ISOLATED CAMPAIGN AGENT $index/10: $role"
  : > "$log_path"

  docker run --rm     --name "ehb-kilo-agent-$agent_id"     --user "$(id -u):$(id -g)"     --network ehb-worker-net     --add-host "api.kilo.ai:$KILO_RELAY_IP"     --mount type=bind,source="$EHB_WORKER_DIR",target=/workspace     --mount type=bind,source="$RUNNER_TEMP/ehb-research-snapshot",target=/workspace/state/research,readonly     --mount type=bind,source="$HOME/.config/kilo/kilo.json",target=/tmp/kilo.json,readonly     -e HOME=/tmp/kilo-home     -e XDG_CONFIG_HOME=/tmp/kilo-home/.config     -e XDG_CACHE_HOME=/tmp/kilo-home/.cache     -e KILO_DISABLE_EXTERNAL_SKILLS=true     -e BENCHMARK_ID="$BENCHMARK_ID"     -e SECURITY_RESEARCH_TARGET="$SECURITY_RESEARCH_TARGET"     -e CAMPAIGN_AGENT_NUMBER="$agent_id"     -e CAMPAIGN_AGENT_ROLE="$role"     "$EHB_KILO_IMAGE"     bash -lc '
      set -euo pipefail
      cd /workspace
      mkdir -p "$HOME/.config/kilo" "$HOME/.cache"
      cp /tmp/kilo.json "$HOME/.config/kilo/kilo.json"
      chmod 600 "$HOME/.config/kilo/kilo.json"
      {
        echo "CAMPAIGN_AGENT_NUMBER=$CAMPAIGN_AGENT_NUMBER"
        echo "CAMPAIGN_AGENT_ROLE=$CAMPAIGN_AGENT_ROLE"
        echo
        echo "You are one fresh member of a sequential 10-agent security-research campaign."
        echo "Inspect durable evidence before acting. Treat previous agent claims as hypotheses."
        echo "Do not launch another Kilo session, workflow, recursive agent, or hidden campaign."
        echo "Do not commit or push. Do not modify trusted controller artifacts."
        echo
        cat /workspace/.kilo/wakeup-prompt.md
      } > /tmp/campaign-agent-prompt
      timeout --foreground --signal=TERM --kill-after=60s 28m kilo run --model openai-compatible/free-kilo --auto "$(cat /tmp/campaign-agent-prompt)"
    ' > >(tee "$log_path") 2>&1
  status=$?

  if [ "$status" -eq 0 ]; then
    campaign_successes=$((campaign_successes + 1))
    agent_status=SUCCESS
  elif [ "$status" -eq 124 ]; then
    campaign_failed=1
    agent_status=TIMEOUT
  else
    campaign_failed=1
    agent_status=FAILED
  fi

  {
    echo "# Security Campaign Agent $agent_id"
    echo
    echo "- role: $role"
    echo "- status: $agent_status"
    echo "- exit_code: $status"
    echo "- observed_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    echo "## Controller-observed worker status"
    git -C "$EHB_WORKER_DIR" status --short 2>/dev/null || true
    echo
    echo "This record does not certify security findings."
  } > "$EHB_WORKER_DIR/state/campaign/agent_$agent_id_controller.md"

  echo "CAMPAIGN_AGENT_$agent_id_STATUS=$agent_status" >> "$GITHUB_ENV"
  echo "CAMPAIGN_SUCCESS_COUNT=$campaign_successes" >> "$GITHUB_ENV"
  echo "CAMPAIGN_FAILURE_COUNT=$((index - campaign_successes))" >> "$GITHUB_ENV"
  echo "::notice::Campaign agent $index/10 finished: $agent_status; successes=$campaign_successes; failures=$((index - campaign_successes))"
done

campaign_status=PARTIAL
if [ "$campaign_failed" -eq 0 ]; then campaign_status=COMPLETE; fi

echo "CAMPAIGN_SUCCESS_COUNT=$campaign_successes" >> "$GITHUB_ENV"
echo "CAMPAIGN_FAILURE_COUNT=$((10 - campaign_successes))" >> "$GITHUB_ENV"
echo "CAMPAIGN_STATUS=$campaign_status" >> "$GITHUB_ENV"
echo "CAMPAIGN_FINISHED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"
printf '{"status":"%s","agent_count":10,"success_count":%d,"failure_count":%d,"finished_utc":"%s"}
' "$campaign_status" "$campaign_successes" "$((10 - campaign_successes))" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EHB_WORKER_DIR/state/campaign/campaign_status.json"

if [ "$campaign_failed" -eq 0 ]; then
  echo "KILO_LIVENESS_STATUS=COMPLETED_WITH_POSTCAMPAIGN_VERIFICATION" >> "$GITHUB_ENV"
  echo "KILO_LIVENESS_REASON=10 fresh isolated security-research sessions executed" >> "$GITHUB_ENV"
  exit 0
fi

echo "KILO_LIVENESS_STATUS=COMPLETED_WITHOUT_FULL_CAMPAIGN" >> "$GITHUB_ENV"
echo "KILO_LIVENESS_REASON=campaign had failed or timed-out agents" >> "$GITHUB_ENV"
exit 1
