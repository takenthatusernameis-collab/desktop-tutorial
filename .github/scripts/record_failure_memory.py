#!/usr/bin/env python3
"""Record bounded controller-side failure memory for future worker activations."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def classify_pre_persist(
    *,
    portfolio: str,
    preflight: str,
    smoke: str,
    post_kilo_regression: str,
    worker: str,
    research_validation: str,
    research_handoff: str,
    evaluate: str,
) -> str:
    if portfolio != "success" or preflight != "success" or smoke != "success" or post_kilo_regression not in {"success", "skipped"}:
        return "FAILED"
    if worker != "success":
        return "PARTIAL"
    if research_validation != "success":
        return "PARTIAL"
    if research_handoff != "success":
        return "PARTIAL"
    if evaluate != "success":
        return "PARTIAL"
    return "COMPLETE"


def first_non_success(
    *,
    portfolio: str,
    preflight: str,
    smoke: str,
    post_kilo_regression: str,
    worker: str,
    research_validation: str,
    research_handoff: str,
    evaluate: str,
) -> str:
    ordered = (
        ("research_portfolio", portfolio),
        ("preflight", preflight),
        ("kilo_smoke", smoke),
        ("post_kilo_regression", post_kilo_regression),
        ("worker", worker),
        ("research_validation", research_validation),
        ("research_handoff", research_handoff),
        ("evaluate", evaluate),
    )
    for stage, outcome in ordered:
        if outcome not in {"success", "skipped"}:
            return stage
    return ""


def append_bounded(path: Path, record: dict, limit: int) -> None:
    rows: list[str] = []
    if path.exists():
        rows = path.read_text(encoding="utf-8").splitlines()
    rows.append(json.dumps(record, sort_keys=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows[-limit:]) + "\n", encoding="utf-8")


def record(args: argparse.Namespace) -> int:
    status = classify_pre_persist(
        portfolio=args.portfolio,
        preflight=args.preflight,
        smoke=args.smoke,
        post_kilo_regression=args.post_kilo_regression,
        worker=args.worker,
        research_validation=args.research_validation,
        research_handoff=args.research_handoff,
        evaluate=args.evaluate,
    )
    stage = first_non_success(
        portfolio=args.portfolio,
        preflight=args.preflight,
        smoke=args.smoke,
        post_kilo_regression=args.post_kilo_regression,
        worker=args.worker,
        research_validation=args.research_validation,
        research_handoff=args.research_handoff,
        evaluate=args.evaluate,
    )
    if status == "COMPLETE" and not stage:
        return 0

    record = {
        "activation_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "unknown"),
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "repository_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "status": status,
        "failure_stage": stage or "unknown",
        "stage_outcomes": {
            "research_portfolio": args.portfolio,
            "preflight": args.preflight,
            "kilo_smoke": args.smoke,
            "post_kilo_regression": args.post_kilo_regression,
            "worker": args.worker,
            "research_validation": args.research_validation,
            "research_handoff": args.research_handoff,
            "evaluate": args.evaluate,
        },
        "reminder": "Do not repeat the same failed invocation or implementation path without first identifying what changed and why the new approach should work; prefer the smallest verified path.",
    }
    append_bounded(Path(args.output), record, max(1, args.limit))
    return 0


def self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "FAILURE_MEMORY.jsonl"
        parser = argparse.Namespace(
            output=str(path),
            limit=3,
            portfolio="success",
            preflight="success",
            smoke="success",
            post_kilo_regression="success",
            worker="failure",
            research_validation="skipped",
            research_handoff="skipped",
            evaluate="skipped",
        )
        assert record(parser) == 0
        rows = path.read_text(encoding="utf-8").splitlines()
        assert len(rows) == 1
        data = json.loads(rows[0])
        assert data["status"] == "PARTIAL"
        assert data["failure_stage"] == "worker"

        parser.portfolio = "failure"
        parser.worker = "skipped"
        assert record(parser) == 0
        rows = path.read_text(encoding="utf-8").splitlines()
        data = json.loads(rows[-1])
        assert data["status"] == "FAILED"
        assert data["failure_stage"] == "research_portfolio"

    print("failure memory self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", default="state/research/FAILURE_MEMORY.jsonl")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--portfolio", required=False, default="skipped")
    parser.add_argument("--preflight", required=False, default="skipped")
    parser.add_argument("--smoke", required=False, default="skipped")
    parser.add_argument("--post-kilo-regression", required=False, default="skipped")
    parser.add_argument("--worker", required=False, default="skipped")
    parser.add_argument("--research-validation", required=False, default="skipped")
    parser.add_argument("--research-handoff", required=False, default="skipped")
    parser.add_argument("--evaluate", required=False, default="skipped")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    return record(args)


if __name__ == "__main__":
    raise SystemExit(main())
