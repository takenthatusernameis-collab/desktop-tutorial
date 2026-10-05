#!/usr/bin/env python3
"""Deterministic worker-outcome reporter used both in preflight and at hand-off."""

from __future__ import annotations

import argparse
from pathlib import Path


def report(
    *,
    preflight: str,
    smoke: str,
    worker: str,
    evaluate: str,
    portfolio: str,
    research_validation: str,
    findings_path: Path,
    research_report_path: Path,
    research_handoff: str = "success",
) -> tuple[int, str]:
    print(f"Preflight infrastructure outcome: {preflight}")
    print(f"Kilo execution smoke outcome: {smoke}")
    print(f"Raw Kilo worker outcome: {worker}")
    print(f"Independent evaluator outcome: {evaluate}")
    print(f"Deterministic research portfolio outcome: {portfolio}")
    print(f"Kilo research-program validation outcome: {research_validation}")
    print(f"Research-program handoff outcome: {research_handoff}")

    if portfolio != "success":
        return 1, "FAILED_PRE_KILO_PORTFOLIO"
    if preflight != "success":
        return 1, "FAILED_PRECHECK"
    if smoke != "success":
        return 1, "FAILED_KILO_SMOKE"
    if worker == "skipped":
        return 1, "FAILED_WORKER_SKIPPED"

    findings_present = findings_path.is_file() and findings_path.stat().st_size > 0
    research_report_present = research_report_path.is_file() and research_report_path.stat().st_size > 0

    # A non-successful worker is a continuation point, not an automatic
    # activation failure. Dependent post-worker validation/evaluation stages
    # are intentionally skipped; durable state remains truthfully PARTIAL.
    if worker != "success":
        return 0, "PARTIAL"

    if research_validation != "success":
        return 1, "FAILED_RESEARCH_VALIDATION"
    if research_handoff != "success":
        return 1, "FAILED_RESEARCH_HANDOFF"
    if evaluate != "success":
        return 1, "FAILED_INDEPENDENT_EVALUATION"
    if not findings_present:
        return 1, "FAILED_FINDINGS_REPORT_MISSING"
    if not research_report_present:
        return 1, "FAILED_RESEARCH_REPORT_MISSING"

    return 0, "SUCCESS"


def self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        findings = root / "benchmark_findings.json"
        research = root / "benchmark_research.md"
        findings.write_text("{}\n", encoding="utf-8")
        research.write_text("# report\n", encoding="utf-8")

        rc, outcome = report(
            preflight="success",
            smoke="success",
            worker="success",
            evaluate="success",
            portfolio="success",
            research_validation="success",
            findings_path=findings,
            research_report_path=research,
        )
        assert (rc, outcome) == (0, "SUCCESS")

        rc, outcome = report(
            preflight="success",
            smoke="success",
            worker="failure",
            evaluate="success",
            portfolio="success",
            research_validation="success",
            findings_path=findings,
            research_report_path=research,
        )
        assert (rc, outcome) == (0, "PARTIAL")

        rc, outcome = report(
            preflight="success",
            smoke="success",
            worker="success",
            evaluate="success",
            portfolio="success",
            research_validation="success",
            findings_path=findings,
            research_report_path=research,
            research_handoff="failure",
        )
        assert rc != 0 and outcome == "FAILED_RESEARCH_HANDOFF"

        rc, outcome = report(
            preflight="success",
            smoke="success",
            worker="failure",
            evaluate="skipped",
            portfolio="success",
            research_validation="success",
            findings_path=root / "missing.json",
            research_report_path=research,
        )
        assert (rc, outcome) == (0, "PARTIAL")

        rc, outcome = report(
            preflight="success",
            smoke="success",
            worker="failure",
            evaluate="success",
            portfolio="success",
            research_validation="success",
            findings_path=findings,
            research_report_path=research,
        )
        assert (rc, outcome) == (0, "PARTIAL")

    print("worker outcome self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--preflight")
    parser.add_argument("--smoke")
    parser.add_argument("--worker")
    parser.add_argument("--evaluate")
    parser.add_argument("--portfolio")
    parser.add_argument("--research-validation")
    parser.add_argument("--research-handoff", default="success")
    parser.add_argument("--findings-path", type=Path)
    parser.add_argument("--research-report-path", type=Path)
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    required = {
        "preflight": args.preflight,
        "smoke": args.smoke,
        "worker": args.worker,
        "evaluate": args.evaluate,
        "portfolio": args.portfolio,
        "research-validation": args.research_validation,
        "research-handoff": args.research_handoff,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing or args.findings_path is None or args.research_report_path is None:
        parser.error("all outcome fields and both report paths are required")

    rc, outcome = report(
        preflight=args.preflight,
        smoke=args.smoke,
        worker=args.worker,
        evaluate=args.evaluate,
        portfolio=args.portfolio,
        research_validation=args.research_validation,
        findings_path=args.findings_path,
        research_report_path=args.research_report_path,
        research_handoff=args.research_handoff,
    )
    print(f"WORKER_OUTCOME={outcome}")
    if outcome == "PARTIAL":
        print(
            "Worker activation did not complete; preserving truthful partial state "
            "without converting the continuation point into a workflow failure."
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
