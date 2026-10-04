#!/usr/bin/env python3
"""Deterministic self-tests for triage_tasks.py.

These tests encode the enterprise's triage contract as hardcoded expected
values so that the authorization gate, prioritization rubric, thresholds, and
checklist evaluator can be regression-tested against research_state.md without
any external target.

    python3 scripts/test_triage.py
Exit: 0 = all tests passed, 1 = failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import triage_tasks as t

FAILED = 0
PASSED = 0


def check(name, actual, expected):
    global FAILED, PASSED
    if actual == expected:
        PASSED += 1
        print(f"PASS {name}")
    else:
        FAILED += 1
        print(f"FAIL {name}")
        print(f"      expected {expected!r}, got {actual!r}")


def base_task():
    return {
        "task_id": "T",
        "intake_status": "awaiting_triage",
        "authorized_target": "example",
        "scope_boundary": "http://example/*",
        "hypothesis": "XSS in search.",
        "success_criteria": "payload reflected",
        "auth_verified_by": "analyst-01",
        "scope_size": "medium",
        "hypothesis_specificity": "moderate",
        "novelty": "documented pattern",
        "evidence_available": "partial",
    }


def main():
    global FAILED, PASSED

    # ---- Required-field validation ----
    bad = {"task_id": "T1", "intake_status": "awaiting_triage"}
    check("missing required fields -> error", len(t.triage_task(bad)["errors"]) > 0, True)

    # ---- Authorization gate ----
    gate_fail = t.triage_task({"task_id": "T1", "intake_status": "awaiting_triage", "auth_verified_by": ""})
    check("empty auth_verified_by -> gate fail", gate_fail["auth_gate"]["status"] == "fail", True)
    check("empty auth_verified_by -> priority_total None", gate_fail["priority_total"] is None, True)
    check("empty auth_verified_by -> decision reject", gate_fail["decision"] == "reject", True)

    gate_pass = t.triage_task(base_task() | {"task_id": "T2"})
    check("nonempty auth_verified_by -> gate cleared (scoring proceeds)", gate_pass["priority_total"] is not None, True)
    check("nonempty auth_verified_by -> priority_total not None", gate_pass["priority_total"] is not None, True)

    # ---- Rubric scoring ----
    check("scope small -> 1", t.score_rubric({"task_id": "x", "scope_size": "small",
          "hypothesis_specificity": "moderate", "novelty": "common", "evidence_available": "none"})["scope_size"] == 1, True)
    check("scope medium -> 2", t.score_rubric({"task_id": "x", "scope_size": "medium",
          "hypothesis_specificity": "moderate", "novelty": "common", "evidence_available": "none"})["scope_size"] == 2, True)
    check("scope large -> 3", t.score_rubric({"task_id": "x", "scope_size": "large",
          "hypothesis_specificity": "moderate", "novelty": "common", "evidence_available": "none"})["scope_size"] == 3, True)
    check("specificity specific -> 3", t.score_rubric({"task_id": "x", "scope_size": "small",
          "hypothesis_specificity": "specific", "novelty": "common", "evidence_available": "none"})["hypothesis_specificity"] == 3, True)
    check("novelty potentially novel -> 3", t.score_rubric({"task_id": "x", "scope_size": "small",
          "hypothesis_specificity": "moderate", "novelty": "potentially novel", "evidence_available": "none"})["novelty"] == 3, True)
    check("evidence substantial -> 3", t.score_rubric({"task_id": "x", "scope_size": "small",
          "hypothesis_specificity": "moderate", "novelty": "common", "evidence_available": "substantial"})["evidence_available"] == 3, True)
    check("all max scores -> total 12", t.triage_task(base_task() | {"scope_size": "large",
          "hypothesis_specificity": "specific", "novelty": "potentially novel",
          "evidence_available": "substantial"})["priority_total"] == 12, True)
    check("unrecognised criterion -> rejected",
          t.triage_task(base_task() | {"scope_size": "huge"})["decision"] == "reject", True)

    # ---- Decision thresholds ----
    check("total 12 -> research", t.triage_task(base_task() | {"scope_size": "large",
          "hypothesis_specificity": "specific", "novelty": "potentially novel",
          "evidence_available": "substantial", "rejected_false_positives": "none",
          "safe_interaction": "GET", "reproduction_conditions": "curl",
          "evidence_quality": "high", "accept_null_result": "yes", "triage_decision": "research"})["decision"] == "research", True)
    check("total 7 -> defer", t.triage_task(base_task() | {"scope_size": "medium",
          "hypothesis_specificity": "moderate", "novelty": "documented pattern",
          "evidence_available": "none"})["decision"] == "defer", True)
    check("total 4 -> reject", t.triage_task(base_task() | {"scope_size": "small",
          "hypothesis_specificity": "vague", "novelty": "common",
          "evidence_available": "none"})["decision"] == "reject", True)

    # ---- Checklist evaluator ----
    check("checklist returns 9 items", t.evaluate_checklist(base_task())["n"] == 9, True)
    check("empty record -> score 0", t.evaluate_checklist({"task_id": "x", "intake_status": "awaiting_triage",
          "auth_verified_by": "a"})["score"] == 0, True)
    rich = base_task() | {"task_id": "x", "intake_status": "awaiting_triage", "auth_verified_by": "analyst-01",
        "scope_boundary": "http://x/*", "hypothesis": "h", "success_criteria": "c",
        "rejected_false_positives": "reflected raw", "safe_interaction": "GET only",
        "reproduction_conditions": "curl example", "evidence_quality": "high",
        "accept_null_result": "yes", "triage_decision": "defer"}
    check("fully rich record -> score 9", t.evaluate_checklist(rich)["score"] == 9, True)
    check("scoring example-like record -> score 3",
          t.evaluate_checklist({"task_id": "S", "intake_status": "awaiting_triage",
              "auth_verified_by": "analyst-01", "scope_boundary": "http://s/*",
              "hypothesis": "h", "success_criteria": "c"})["score"] == 3, True)
    check("missing false-positive field -> missing",
          t.evaluate_checklist({"task_id": "x", "intake_status": "awaiting_triage",
              "auth_verified_by": "a"})["items"][3]["status"] == "missing", True)
    check("missing hypothesis field -> missing",
          t.evaluate_checklist({"task_id": "x", "intake_status": "awaiting_triage",
              "auth_verified_by": "a"})["items"][0]["status"] == "missing", True)

    # ---- Finalize decision override ----
    ck_low = {"score": 3.0, "n": 9}
    ck_ok = {"score": 6.0, "n": 9}
    dec, reason = t.finalize_decision("research", ck_low)
    check("low checklist overrides research -> defer", dec == "defer", True)
    check("override reason mentions checklist", reason and "checklist" in reason.lower(), True)
    dec2, reason2 = t.finalize_decision("research", ck_ok)
    check("sufficient checklist keeps research", dec2 == "research", True)
    check("sufficient checklist has no override reason", reason2 is None, True)

    # ---- Deterministic ranking ----
    tasks = [base_task() | {"task_id": f"B{i}"} for i in range(3)]
    results = [t.triage_task(x) for x in tasks]
    ranked = sorted(results, key=lambda r: (-r["priority_total"], r["task_id"]))
    check("stable ranking by id asc when tied", [r["task_id"] for r in ranked] == ["B0", "B1", "B2"], True)

    # ---- Module invariants ----
    check("CHECKLIST_THRESHOLD equals DEFER_THRESHOLD", t.CHECKLIST_THRESHOLD == t.DEFER_THRESHOLD, True)
    check("CHECKLIST_ITEMS has 9 entries", len(t.CHECKLIST_ITEMS) == 9, True)

    print()
    print(f"Results: {PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
