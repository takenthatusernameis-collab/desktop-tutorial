#!/usr/bin/env python3
"""Build a precise, durable research-process evaluation.

The hidden benchmark score and the research-process score are intentionally
separate. Hidden replay measures benchmark outcome; this module measures how
well the research system operated even when hidden replay produced no match.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from statistics import fmean
from typing import Any

OUTCOME_CLASSES = {
    "NEW_EVIDENCE",
    "NEW_HYPOTHESIS",
    "FALSIFIED",
    "NO_NEW_INFORMATION",
    "INFRASTRUCTURE_FAILURE",
}
REQUIRED_FIELDS = (
    "OUTCOME_CLASS:",
    "TASK_ID:",
    "PRIMARY_QUESTION:",
    "BOTTLENECK:",
    "INFORMATION_GAP:",
    "BOUNDED_ACTION:",
    "DELIVERABLE:",
    "SUCCESS_EVIDENCE_CRITERION:",
    "STOP_CONDITION:",
    "OUT_OF_SCOPE:",
    "VERIFICATION_REQUIREMENT:",
    "CHANGED:",
    "VERIFIED:",
    "UNVERIFIED:",
    "OBSERVED_EFFECT:",
    "UNCERTAINTY_TARGETED:",
    "UNCERTAINTY_REDUCED:",
    "DECISION:",
    "NEXT:",
)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value[:240]


def read_agent_memos(context_dir: Path) -> list[dict[str, Any]]:
    memos: list[dict[str, Any]] = []
    for path in sorted(context_dir.glob("agent_*_RESULT.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        fields: dict[str, str] = {}
        for index, line in enumerate(lines):
            for field in REQUIRED_FIELDS:
                if line.startswith(field):
                    value_lines = []
                    first = line.split(":", 1)[1].strip()
                    if first:
                        value_lines.append(first)
                    for continuation in lines[index + 1 :]:
                        if any(continuation.startswith(prefix) for prefix in REQUIRED_FIELDS):
                            break
                        if continuation.strip():
                            value_lines.append(continuation.strip())
                    fields[field] = " ".join(value_lines).strip()
                    break
        outcome = fields.get("OUTCOME_CLASS:", "").strip()
        substantive = outcome in OUTCOME_CLASSES and outcome != "INFRASTRUCTURE_FAILURE"
        complete = all(fields.get(field, "").strip() for field in REQUIRED_FIELDS)
        memos.append(
            {
                "path": str(path),
                "outcome_class": outcome,
                "substantive": substantive,
                "complete": complete,
                "hypothesis": fields.get("PRIMARY_QUESTION:", ""),
                "task_id": fields.get("TASK_ID:", ""),
                "role": fields.get("ROLE:", ""),
                "decision": fields.get("DECISION:", ""),
                "next": fields.get("NEXT:", ""),
                "observed_effect": fields.get("OBSERVED_EFFECT:", ""),
                "uncertainty_reduced": fields.get("UNCERTAINTY_REDUCED:", ""),
            }
        )
    return memos


def portfolio_metrics() -> dict[str, float]:
    summary = load_json(Path("state/research/PORTFOLIO_SUMMARY.json"), {})
    candidates = int(summary.get("candidate_requests", 0) or 0)
    behavioral_differences = int(summary.get("behavioral_differences", 0) or 0)
    repeat_reproductions = int(summary.get("repeat_reproductions", 0) or 0)
    generations = int(summary.get("executed_generations", 0) or 0)
    families = len(summary.get("families_represented") or [])
    surfaces = len(summary.get("surfaces_represented") or [])
    program = load_json(Path("state/research/PROGRAM.json"), {})
    active_families = sum(
        1 for family in (program.get("evolution_families") or [])
        if isinstance(family, dict) and family.get("status") != "ARCHIVED"
    )
    active_surfaces = sum(
        1 for surface in (program.get("surfaces") or [])
        if isinstance(surface, dict) and surface.get("status") != "ARCHIVED"
    )
    return {
        "candidate_requests": float(candidates),
        "behavioral_differences": float(behavioral_differences),
        "repeat_reproductions": float(repeat_reproductions),
        "executed_generations": float(generations),
        "families_represented": float(families),
        "surfaces_represented": float(surfaces),
        "active_families": float(active_families),
        "active_surfaces": float(active_surfaces),
        "behavioral_difference_rate": clamp(
            behavioral_differences / max(1, candidates)
        ),
        "repeat_reproduction_rate": clamp(
            repeat_reproductions / max(1, candidates)
        ),
    }


def trend(history_path: Path, key: str) -> dict[str, Any]:
    if not history_path.exists():
        return {"current": None, "previous": None, "delta": None, "direction": "insufficient_history"}
    rows = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get(key), (int, float)):
            rows.append(float(value[key]))
    if not rows:
        return {"current": None, "previous": None, "delta": None, "direction": "insufficient_history"}
    current = rows[-1]
    previous = rows[-2] if len(rows) >= 2 else None
    delta = None if previous is None else round(current - previous, 4)
    if delta is None:
        direction = "baseline"
    elif delta > 0.03:
        direction = "improving"
    elif delta < -0.03:
        direction = "declining"
    else:
        direction = "stable"
    return {"current": round(current, 4), "previous": None if previous is None else round(previous, 4), "delta": delta, "direction": direction}


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
    parser.add_argument("--process-history", default="state/research/PROCESS_HISTORY.jsonl")
    args = parser.parse_args()

    result = load_json(Path(args.result), {}) if args.result else {}
    memos = read_agent_memos(Path(args.context_dir))
    substantive = [m for m in memos if m["substantive"]]
    complete = [m for m in memos if m["substantive"] and m["complete"]]
    outcomes = [m["outcome_class"] for m in memos]

    counts = {name: outcomes.count(name) for name in sorted(OUTCOME_CLASSES)}
    total_agents = max(1, len(memos))
    substantive_count = max(1, len(substantive))

    hypotheses = [normalize_text(m["hypothesis"]) for m in substantive if m["hypothesis"].strip()]
    hypothesis_diversity = len(set(hypotheses)) / max(1, len(hypotheses))

    learning_yield = clamp(
        (
            counts["NEW_EVIDENCE"]
            + counts["FALSIFIED"]
            + 0.5 * counts["NEW_HYPOTHESIS"]
        )
        / substantive_count
    )

    falsification_coverage = clamp(counts["FALSIFIED"] / substantive_count)

    portfolio = portfolio_metrics()
    breadth = clamp(portfolio["families_represented"] / max(1.0, portfolio["active_families"]))
    evidence_present = (
        Path(args.findings).is_file()
        and Path(args.findings).stat().st_size > 0
        and Path(args.proposal).is_file()
        and Path(args.proposal).stat().st_size > 0
    )

    roles = [m.get("role", "") for m in memos]
    alternating_roles = clamp(
        sum(
            1
            for idx, role in enumerate(roles, start=1)
            if role == ("LEARNING_PROCESS" if idx % 2 else "HIGHER_ORDER_RESEARCH")
        ) / max(1, len(roles))
    )
    task_contract_integrity = clamp(len(complete) / max(1, len(memos)))
    observed_effect_rate = clamp(
        sum(1 for m in substantive if m.get("observed_effect", "").strip()) / max(1, len(substantive))
    )
    uncertainty_reduction_rate = clamp(
        sum(1 for m in substantive if m.get("uncertainty_reduced", "").strip() and m.get("uncertainty_reduced", "").strip().lower() not in {"none", "unknown"})
        / max(1, len(substantive))
    )
    metrics = {
        "execution_reliability": 1.0 if args.preflight == "success" and args.smoke == "success" else 0.0,
        "agent_completion": clamp(len(substantive) / total_agents),
        "memo_integrity": task_contract_integrity,
        "task_contract_integrity": round(task_contract_integrity, 4),
        "alternating_role_integrity": round(alternating_roles, 4),
        "hypothesis_diversity": round(clamp(hypothesis_diversity), 4),
        "learning_yield": round(learning_yield, 4),
        "falsification_coverage": round(falsification_coverage, 4),
        "observed_effect_rate": round(observed_effect_rate, 4),
        "uncertainty_reduction_rate": round(uncertainty_reduction_rate, 4),
        "research_breadth": round(breadth, 4),
        "reproduction_density": round(portfolio["repeat_reproduction_rate"], 4),
        "handoff_completeness": 1.0 if evidence_present else 0.0,
    }

    # Equal weighting avoids arbitrary emphasis and keeps the index interpretable.
    process_score = round(fmean(metrics.values()), 4) if metrics else 0.0
    stagnation_rate = clamp(counts["NO_NEW_INFORMATION"] / substantive_count)

    activation_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    record = {
        "schema_version": 2,
        "activation_id": activation_id,
        "execution_health": "HEALTHY" if args.preflight == "success" and args.smoke == "success" else "DEGRADED",
        "research_health": (
            "PROGRESS"
            if counts["NEW_EVIDENCE"] or counts["FALSIFIED"]
            else "HYPOTHESIS_PROGRESS"
            if counts["NEW_HYPOTHESIS"]
            else "NO_NEW_INFORMATION"
            if substantive
            else "BLOCKED"
        ),
        "evidence_health": "PRESENT" if evidence_present else "MISSING",
        "evaluation_health": (
            "EVALUATION_FAILED"
            if args.evaluate != "success"
            else "EVALUATED_MATCHES"
            if int(result.get("reproduced_claim_count", 0) or 0) > 0
            else "EVALUATED_NO_MATCHES"
            if int(result.get("finding_count_submitted", 0) or 0) > 0
            else "EVALUATED_NO_SUBMISSIONS"
        ),
        "persistence_health": (
            "DURABLE" if args.persist == "success"
            else "PENDING_COMMIT" if args.persist == "pending"
            else "PARTIAL"
        ),
        "campaign_status": args.campaign_status,
        "agent_result_count": len(memos),
        "outcome_class_counts": counts,
        "process_score": process_score,
        "process_metrics": metrics,
        "stagnation_rate": round(stagnation_rate, 4),
        "campaign_contract": "CONTROLLED_10_AGENT_SEQUENTIAL",
        "portfolio": portfolio,
        "benchmark": {
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

    history = Path(args.process_history)
    history.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if history.exists():
        for line in history.read_text(encoding="utf-8").splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                existing.append(value)
    if not any(str(row.get("activation_id")) == activation_id for row in existing):
        history.open("a", encoding="utf-8").write(json.dumps(
            {
                "activation_id": activation_id,
                "process_score": process_score,
                "stagnation_rate": round(stagnation_rate, 4),
                "metrics": metrics,
                "research_health": record["research_health"],
                "evaluation_health": record["evaluation_health"],
            },
            sort_keys=True,
        ) + "\n")

    print(json.dumps({
        "process_score": process_score,
        "process_metrics": metrics,
        "stagnation_rate": round(stagnation_rate, 4),
        "benchmark_score": record["benchmark"]["overall_score"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
