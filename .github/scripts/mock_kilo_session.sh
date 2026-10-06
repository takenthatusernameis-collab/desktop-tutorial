#!/usr/bin/env bash
set -euo pipefail

agent_number="$1"
task_path="$2"
result_path="$3"

session_id="$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"
task_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["task_id"])' "$task_path")"

mkdir -p "$(dirname "$result_path")"
printf '%s\n' "$session_id" > "$(dirname "$result_path")/MOCK_SESSION_ID"
cat > "$result_path" <<EOF
OUTCOME_CLASS: $([ "$agent_number" -eq 3 ] && echo INFRASTRUCTURE_FAILURE || echo NEW_EVIDENCE)
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
OBSERVED_EFFECT: Mock session $agent_number created unique session_id=$session_id.
UNCERTAINTY_TARGETED: Sequential fresh-session isolation.
UNCERTAINTY_REDUCED: The controller persisted one bounded result for the next slot.
DECISION: $([ "$agent_number" -eq 3 ] && echo UNVERIFIED || echo RETAIN)
NEXT: Continue with the next controller-selected bounded task.
EOF

if [ "$agent_number" -eq 3 ]; then
  exit 75
fi
exit 0
