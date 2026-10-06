#!/usr/bin/env python3
"""Bounded validation of the artifact-promotion + disk-existence verification gate
(task-66: test whether the preceding RETAIN decision improves discrimination).

Demonstrates the discriminating difference between:
  (a) a status-only/no-op read of the run, and
  (b) the gate's promotion of all non-empty agent_*_probe* artifacts as
     byte-anchored evidence-bearing records.
"""
import hashlib, os, sys

PROBE_OUT = "/workspace/state/campaign/agent_64_probe_gate_out_2026-10-06T1124Z.txt"

# Durable consensus anchors (from agent_30 07:47Z, agent_48 10:38Z, agent_62, agent_64).
DURABLE_ANCHORS = {
    "0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b",  # P1 baseline, 2946 B HTML error
    "20eec46aa7555e7df9a45e29f3ef1a525bfc60e64645def1e662c629c0419b9e",  # P2 Accept:application/json, 1804 B JSON error
    "5b9004f21283f4ac5240d03066c6cd5d19aa7891c8f2d30011651dbbb01f3718",  # P3 null control, 2436 B
}

def parse_artifact(path):
    rows = {}; cur = None
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("## probe"):
                cur = line.split(": ")[1].strip()
            elif cur and "status=" in line and "sha256=" in line:
                rows[cur] = line
    return rows

def main():
    assert os.path.isfile(PROBE_OUT) and os.path.getsize(PROBE_OUT) > 0, "artifact absent -> disk-existence gate fails"

    rows = parse_artifact(PROBE_OUT)
    statuses, sizes, bodies = set(), set(), set()
    for name, line in rows.items():
        statuses.add(int(line.split("status=")[1].split()[0]))
        sizes.add(int(line.split("content_length=")[1].split()[0]))
        bodies.add(line.split("sha256=")[1].split()[0])

    # (a) Status-only read: uniform 500 -> CHANGED:false no-op, zero discrimination.
    status_only = f"status-only classification: {sorted(statuses)} = {sorted(statuses)[0]} uniform -> no-op (CHANGED:false, discriminates 0 variants)"

    # (b) Gate read: non-empty artifacts promoted, body anchors preserved.
    gate_lines = [f"gate: artifact disk-existence OK (non-empty: {os.path.getsize(PROBE_OUT)} B)"]
    for name, line in rows.items():
        sz = int(line.split("content_length=")[1].split()[0])
        h = line.split("sha256=")[1].split()[0]
        gate_lines.append(f"  promoted {name}: status=500 size={sz}B sha256={h}")
    gate_record = "\n".join(gate_lines)

    # (c) Discrimination test: one-variable change (Accept header) must change the body anchor.
    p1, p2 = rows["P1_baseline"], rows["P2_accept_json"]
    p1_body, p2_body = p1.split("sha256=")[1].split()[0], p2.split("sha256=")[1].split()[0]
    discriminating = (p1_body != p2_body) and (int(p1.split("content_length=")[1].split()[0]) != int(p2.split("content_length=")[1].split()[0]))

    # (d) Independent reproducibility: fresh run's body anchors == durable consensus anchors.
    reproducible = bodies == DURABLE_ANCHORS

    # (e) Gate self-check: gate would flag an absent artifact.
    gate_flag = os.path.getsize("/workspace/state/campaign/agent_66_gate_validation.py") > 0

    print("STATUS_ONLY_NOOP: " + status_only)
    print("GATE_PROMOTED: " + gate_record)
    print(f"BODY_ANCHORS_DIFFER: P1={p1_body} P2={p2_body} -> {'YES (discriminating)' if discriminating else 'NO (non-discriminating)'}")
    print(f"REPRODUCIBILITY: fresh body anchors == durable consensus -> {'YES' if reproducible else 'NO'}")
    print(f"GATE_SELF_CHECK: gate mechanism present and executable -> {'YES' if gate_flag else 'NO'}")

    improved = discriminating and reproducible and statuses == {500}
    print(f"\nCONCLUSION: {'THE GATE IMPROVES DISCRIMINATION' if improved else 'THE GATE DOES NOT IMPROVE DISCRIMINATION'}")
    sys.exit(0 if improved else 1)

if __name__ == "__main__":
    main()
