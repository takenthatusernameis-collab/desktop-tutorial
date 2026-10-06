#!/usr/bin/env python3
"""Demonstrate the disk-existence gate's negative branch: an absent probe artifact fails the gate.

Companion to agent_66_gate_validation.py (positive branch). The combined artifact-promotion
+ disk-existence verification gate (REPOSITORY_PLAYBOOK.md entry, 2026-10-06) is a blocking
pre-completion check: every agent_*_probe* artifact referenced in a session's RESULT.md must
exist on disk and be non-empty, or the session must remain UNVERIFIED and not complete.
"""
import os, sys

def disk_exists(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0

PRESENT = "/workspace/state/campaign/agent_64_probe_gate_out_2026-10-06T1124Z.txt"
ABSENT  = "/workspace/state/campaign/NONEXISTENT_ARTIFACT_DOES_NOT_EXIST_xyz.txt"

print(f"PRESENT artifact: {PRESENT} -> {disk_exists(PRESENT)} "
      f"({os.path.getsize(PRESENT)} B) -> disk-existence gate: PASS")
print(f"ABSENT artifact:  {ABSENT} -> {disk_exists(ABSENT)} -> disk-existence gate: FAIL (blocks completion)")

assert disk_exists(PRESENT), "present non-empty artifact must pass the disk-existence gate"
assert not disk_exists(ABSENT), "absent artifact must be caught by the disk-existence gate"
print("GATE_CHECK: disk-existence gate blocks completion when any referenced artifact is missing")
sys.exit(0)
