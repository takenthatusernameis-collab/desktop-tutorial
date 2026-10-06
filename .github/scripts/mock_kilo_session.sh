#!/usr/bin/env bash
set -euo pipefail

campaign_slot="$1"
agent_number="$2"
task_path="$3"
result_path="$4"

session_id="$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"
task_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["task_id"])' "$task_path")"

mkdir -p "$(dirname "$result_path")"
printf '%s\n' "$session_id" > "$(dirname "$result_path")/MOCK_SESSION_ID"
cat > "$result_path" <<EOF
OUTCOME_CLASS: $([ "$campaign_slot" -eq 3 ] && echo INFRASTRUCTURE_FAILURE || echo NEW_EVIDENCE)
TASK_ID: $task_id
PRIMARY_QUESTION: Mock session executes the controller-selected task only.
BOTTLENECK: Dummy orchestration path.
INFORMATION_GAP: Whether durable state is sufficient for the next fresh session.
BOUNDED_ACTION: Execute the selected mock task and emit one durable result.
DELIVERABLE: One durable mock result memo.
SUCCESS_EVIDENCE_CRITERION: Controller validation accepts this memo and the next slot starts from durable state.
STOP_CONDITION: Stop after this memo is written.
OUT_OF_SCOPE: Real security research and real benchmark access.
VERIFICATION_REQUIREMENT: Controller structural verification.
CHANGED: true
VERIFIED: mock session boundary
UNVERIFIED: real Kilo behavior
OBSERVED_EFFECT: Mock global Agent $agent_number (campaign slot $campaign_slot) created unique session_id=$session_id.
UNCERTAINTY_TARGETED: Sequential fresh-session isolation.
UNCERTAINTY_REDUCED: The controller persisted one bounded result for the next slot.
DECISION: $([ "$campaign_slot" -eq 3 ] && echo UNVERIFIED || echo RETAIN)
NEXT: Continue with the next controller-selected bounded task.
EOF

if [ "$campaign_slot" -eq 10 ]; then
  mkdir -p "$(dirname "$(dirname "$result_path")")/../reports"
  cat > "$(dirname "$(dirname "$result_path")")/../reports/benchmark_findings_candidate.json" <<'EOF'
{"findings":[],"smoke_test":true}
EOF
  cat > "$(dirname "$(dirname "$result_path")")/../PROGRAM_PROPOSAL_CANDIDATE.json" <<'EOF'
{
  "program_version": "1.0.0",
  "benchmark_id": "dummy-smoke",
  "discovery": {"surface_map_exhaustive": false, "open_world": true},
  "surfaces": [
    {"surface_id": "smoke-surface", "status": "ACTIVE", "evolutionary_families": ["smoke-family"]}
  ],
  "evolution_families": [
    {
      "family_id": "smoke-family",
      "surface_id": "smoke-surface",
      "status": "ACTIVE",
      "generation": 1,
      "lineage": [],
      "seed_requests": [],
      "best_candidates": []
    }
  ]
}
EOF
  cat > "$(dirname "$(dirname "$result_path")")/../reports/benchmark_research.md" <<'EOF'
# Dummy campaign smoke report

Controller smoke only. No benchmark research evidence is claimed.
EOF
fi

if [ "$campaign_slot" -eq 3 ]; then
  exit 75
fi
exit 0
