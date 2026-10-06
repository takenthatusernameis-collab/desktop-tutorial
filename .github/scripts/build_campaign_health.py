#!/usr/bin/env python3
"""Build a durable, aggregate campaign-health record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

OUTCOME_CLASSES = {
    "NEW_EVIDENCE",
    "NEW_HYPOTHESIS",
    "FALSIFIED",
    "NO_NEW_INFORMATION",
    "INFRASTRUCTURE_FAILURE",
}

def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def collect_agent_outcomes(context_dir: Path) -> list[str]:
    outcomes: list[str] = []
    for path in sorted(context_dir.glob("agent_*_RESULT.md")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("OUTCOME_CLASS:"):
                value = line.split(":", 1)[1].strip()
                if value in OUTCOME_CLASSES:
                    outcomes.append(value)
                break
    return outcomes

def classify_research(outcomes: list[str], campaign_status: str) -> str:
    if "NEW_EVIDENCE" in outcomes or "FALSIFIED" in outcomes:
        return "PROGRESS"
    if "NEW_HYPOTHESIS" in outcomes:
        return "HYPOTHESIS_PROGRESS"
    if campaign_status == "FAILED":
        return "BLOCKED"
    if outcomes:
        return "NO_NEW_INFORMATION"
    return "NO_RESULT"

def classify_evaluation(evaluate: str, result: dict[str, Any]) -> str:
    if evaluate != "success":
        return "EVALUATION_FAILED"
    reproduced = int(result.get("reproduced_claim_count", 0) or 0)
    submitted = int(result.get("finding_count_submitted", 0) or 0)
    if submitted == 0:
        return "EVALUATED_NO_SUBMISSIONS"
    if reproduced > 0:
        return "EVALUATED_MATCHES"
    return "EVALUATED_NO_MATCHES"

def classify_evidence(findings_path: Path, proposal_path: Path) -> str:
    if not findings_path.is_file() or findings_path.stat().st_size == 0:
        return "MISSING"
    if not proposal_path.is_file() or proposal_path.stat().st_size == 0:
        return "PARTIAL"
    return "PRESENT"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--campaign-status", required=True)
    parser.add_argument("--evaluate", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--smoke", required=True)
    parser.add_argument("--persist", required=True)
    parser.add_argument("--context-dir", required=True)
    parser.add_argument("--result", default="")
    parser.add_argument("--findings", default="reports/benchmark_findings.json")
    parser.add_argument("--proposal", default="PROGRAM_PROPOSAL.json")
    args = parser.parse_args()

    result = load_json(Path(args.result), {}) if args.result else {}
    outcomes = collect_agent_outcomes(Path(args.context_dir))
    record = {
        "schema_version": 1,
        "execution_health": "HEALTHY" if args.preflight == "success" and args.smoke == "success" else "DEGRADED",
        "research_health": classify_research(outcomes, args.campaign_status),
        "evidence_health": classify_evidence(Path(args.findings), Path(args.proposal)),
        "evaluation_health": classify_evaluation(args.evaluate, result),
        "persistence_health": "DURABLE" if args.persist == "success" else "PARTIAL",
        "campaign_status": args.campaign_status,
        "agent_result_count": len(outcomes),
        "outcome_class_counts": {name: outcomes.count(name) for name in sorted(OUTCOME_CLASSES)},
        "evaluation": {
            "finding_count_submitted": int(result.get("finding_count_submitted", 0) or 0),
            "reproduced_claim_count": int(result.get("reproduced_claim_count", 0) or 0),
            "unmatched_claim_count": int(result.get("unmatched_claim_count", 0) or 0),
            "unique_challenges_validated": int(result.get("unique_challenges_validated", 0) or 0),
            "overall_score": float(result.get("overall_score", 0.0) or 0.0),
            "discovery_rate": float(result.get("discovery_rate", 0.0) or 0.0),
            "reproduction_rate": float(result.get("reproduction_rate", 0.0) or 0.0),
            "precision_component": float(result.get("precision_component", 0.0) or 0.0),
            "evidence_quality": float(result.get("evidence_quality", 0.0) or 0.0),
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
