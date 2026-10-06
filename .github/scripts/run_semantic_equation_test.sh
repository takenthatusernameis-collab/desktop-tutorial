#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TEMP:?}"
: "${EHB_KILO_IMAGE:?}"
: "${KILO_RELAY_IP:?}"

ROOT="${RUNNER_TEMP}/semantic-equation-test"
CONTEXT="$ROOT/context"
AGENTS="$ROOT/agents"
BASE="$ROOT/base"
RESULTS="$ROOT/results"

rm -rf "$ROOT"
mkdir -p "$CONTEXT" "$AGENTS" "$BASE" "$RESULTS"

copy_if_present() {
  local src="$1" dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
}

for file in AGENTS.md ENTERPRISE.md PERSISTENCE_POLICY.md AUTHORIZED_TARGET.md             SOLVER_FEEDBACK.md LEARNING_STATE.md research_state.md README.md; do
  copy_if_present "$GITHUB_WORKSPACE/$file" "$BASE/$file"
done
copy_if_present "$GITHUB_WORKSPACE/.kilo/wakeup-prompt.md" "$BASE/.kilo/wakeup-prompt.md"

cat > "$CONTEXT/SEMANTIC_TEST_CONTEXT.md" <<'EOF'
# One-time semantic-path test

This is an infrastructure validation task, not security research.

The test intentionally follows the same semantic path used by the real campaign:
1. fresh isolated agent workspace;
2. controller context;
3. trusted project instructions;
4. trusted wakeup prompt;
5. fresh Kilo session;
6. deterministic machine-readable result.

The agent must not access, probe, enumerate, or modify any security target.
The agent must not launch another agent, workflow, or recursive process.
The only substantive task is the equation supplied in its agent brief.
EOF

cat > "$CONTEXT/EQUATION_RULES.md" <<'EOF'
# Equation test rules

Return a single RESULT.md containing exactly:
AGENT:
EQUATION:
ANSWER:
CHECK:
STATUS:

STATUS must be PASS or FAIL.

ANSWER must be the exact integer result.
CHECK must show the arithmetic in compact form.

Do not modify repository files outside the disposable agent workspace.
EOF

# Distinct but deterministic equations exercise semantic parsing rather than a
# single memorized answer.
equation_for() {
  case "$1" in
    1)  echo '((17 * 23) - 41 + 8)' ;;
    2)  echo '((29 * 14) + 37 - 19)' ;;
    3)  echo '((31 * 17) - 52 + 11)' ;;
    4)  echo '((43 * 12) + 25 - 18)' ;;
    5)  echo '((19 * 27) - 64 + 9)' ;;
    6)  echo '((37 * 16) + 21 - 47)' ;;
    7)  echo '((28 * 22) - 33 + 14)' ;;
    8)  echo '((41 * 15) + 16 - 29)' ;;
    9)  echo '((23 * 26) - 71 + 32)' ;;
    10) echo '((34 * 19) + 27 - 58)' ;;
    *) return 1 ;;
  esac
}

expected_for() {
  case "$1" in
    1) echo 358 ;;
    2) echo 424 ;;
    3) echo 486 ;;
    4) echo 523 ;;
    5) echo 458 ;;
    6) echo 566 ;;
    7) echo 597 ;;
    8) echo 602 ;;
    9) echo 559 ;;
    10) echo 615 ;;
    *) return 1 ;;
  esac
}

successes=0
failures=0

for index in $(seq 1 10); do
  agent_id="$(printf '%02d' "$index")"
  agent_dir="$AGENTS/agent_$agent_id"
  equation="$(equation_for "$index")"
  expected="$(expected_for "$index")"
  log_path="$RESULTS/agent_$agent_id.log"

  rm -rf "$agent_dir"
  mkdir -p "$agent_dir/.kilo" "$agent_dir/state/campaign" "$agent_dir/state/research"
  cp -a "$BASE/." "$agent_dir/"

  cat > "$CONTEXT/agent_$agent_id_BRIEF.md" <<EOF
# Agent $agent_id

This is a one-time semantic-path infrastructure test.

You are not performing security research.

EQUATION: $equation
EXPECTED_ANSWER: $expected

Your task:
1. Read /workspace/state/campaign/context/SEMANTIC_TEST_CONTEXT.md
2. Read /workspace/state/campaign/context/EQUATION_RULES.md
3. Follow the same trusted instruction/context path supplied to the normal Kilo campaign.
4. Calculate the equation exactly.
5. Create /workspace/state/campaign/RESULT.md with the required fields.
6. Do not access or probe any target.
7. Do not launch another Kilo session, workflow, or agent.
EOF

  {
    echo "You are agent $agent_id in a one-time semantic-path infrastructure test."
    echo
    cat "$CONTEXT/agent_${agent_id}_BRIEF.md"
    echo
    cat "$CONTEXT/SEMANTIC_TEST_CONTEXT.md"
    echo
    cat "$CONTEXT/EQUATION_RULES.md"
    echo
    echo "=== TRUSTED PROJECT INSTRUCTIONS ==="
    cat "$BASE/AGENTS.md" 2>/dev/null || true
    echo
    echo "=== TRUSTED ENTERPRISE INSTRUCTIONS ==="
    cat "$BASE/ENTERPRISE.md" 2>/dev/null || true
    echo
    echo "=== TRUSTED PERSISTENCE INSTRUCTIONS ==="
    cat "$BASE/PERSISTENCE_POLICY.md" 2>/dev/null || true
    echo
    echo "=== TRUSTED WAKEUP PROMPT ==="
    cat "$BASE/.kilo/wakeup-prompt.md" 2>/dev/null || true
    echo
    echo "=== FINAL ONE-TIME TEST DIRECTIVE ==="
    echo "Ignore the research objective in the trusted wakeup prompt for this infrastructure test."
    echo "Do not perform security research or target interaction."
    echo "Do only the equation in the agent brief, then create RESULT.md and finish."
    echo "The equation and expected answer are:"
    echo "EQUATION: $equation"
    echo "EXPECTED_ANSWER: $expected"
  } > "$agent_dir/.kilo/semantic-test-prompt.md"

  echo "Running semantic-path Kilo agent $index/10: equation $equation"

  set +e
  docker run --rm     --name "semantic-equation-agent-$agent_id"     --user "$(id -u):$(id -g)"     --network ehb-semantic-worker-net     --add-host "api.kilo.ai:$KILO_RELAY_IP"     --mount type=bind,source="$agent_dir",target=/workspace     --mount type=bind,source="$CONTEXT",target=/workspace/state/campaign/context,readonly     --mount type=bind,source="$HOME/.config/kilo/kilo.json",target=/tmp/kilo.json,readonly     -e HOME=/tmp/kilo-home     -e XDG_CONFIG_HOME=/tmp/kilo-home/.config     -e XDG_CACHE_HOME=/tmp/kilo-home/.cache     -e KILO_DISABLE_EXTERNAL_SKILLS=true     -e SEMANTIC_TEST_AGENT="$agent_id"     "$EHB_KILO_IMAGE"     bash -lc '
      set -euo pipefail
      cd /workspace
      mkdir -p "$HOME/.config/kilo" "$HOME/.cache"
      cp /tmp/kilo.json "$HOME/.config/kilo/kilo.json"
      chmod 600 "$HOME/.config/kilo/kilo.json"
      timeout --foreground --signal=TERM --kill-after=30s 3m         kilo run --model openai-compatible/free-kilo --auto "$(cat /workspace/.kilo/semantic-test-prompt.md)"
    ' > >(tee "$log_path") 2>&1
  status=$?
  set -e

  if [ $status -ne 0 ]; then
    echo "Agent $agent_id Kilo exit code=$status" | tee "$agent_dir/state/campaign/CONTROLLER.md"
    failures=$((failures + 1))
  elif [ ! -s "$agent_dir/state/campaign/RESULT.md" ]; then
    echo "Agent $agent_id produced no RESULT.md" | tee "$agent_dir/state/campaign/CONTROLLER.md"
    failures=$((failures + 1))
  else
    cp "$agent_dir/state/campaign/RESULT.md" "$RESULTS/agent_$agent_id_RESULT.md"
    if grep -Eq "^STATUS: PASS$" "$agent_dir/state/campaign/RESULT.md"; then
      successes=$((successes + 1))
    else
      failures=$((failures + 1))
    fi
  fi
done

python3 - "$RESULTS" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
rows = []
for path in sorted(root.glob("agent_*_RESULT.md")):
    fields = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    rows.append({"agent": fields.get("AGENT"), "equation": fields.get("EQUATION"),
                 "answer": fields.get("ANSWER"), "check": fields.get("CHECK"),
                 "status": fields.get("STATUS")})
(root / "SUMMARY.json").write_text(json.dumps({
    "agent_count": 10,
    "results_present": len(rows),
    "pass_count": sum(r["status"] == "PASS" for r in rows),
    "fail_count": sum(r["status"] != "PASS" for r in rows),
    "results": rows,
}, indent=2) + "\n", encoding="utf-8")
PY

echo "SEMANTIC_TEST_SUCCESS_COUNT=$successes" >> "$GITHUB_ENV"
echo "SEMANTIC_TEST_FAILURE_COUNT=$failures" >> "$GITHUB_ENV"

test "$successes" -eq 10
test "$failures" -eq 0
echo "All ten semantic-path equation agents passed."
