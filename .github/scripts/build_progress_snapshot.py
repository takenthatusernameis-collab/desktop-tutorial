#!/usr/bin/env python3
"""Track activation-level research progress independently of the hidden benchmark score.

The benchmark score can remain flat while the research process makes real progress
through new behavioral differences, reproductions, breadth, falsification, or
reliable deliverable production. This tracker records current state and
activation-to-activation deltas so a flat outcome score cannot masquerade as
"no progress".
"""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def nonnegative_delta(current: float, previous: float) -> float:
    return max(0.0, float(current) - float(previous))


def saturate(delta: float, scale: float = 1.0) -> float:
    if delta <= 0:
        return 0.0
    return clamp(1.0 - math.exp(-delta / max(scale, 1e-9)))


def benchmark_result(path: Path) -> dict[str, Any]:
    value = load_json(path, {})
    return value if isinstance(value, dict) else {}


def portfolio_state() -> dict[str, Any]:
    summary = load_json(Path("state/research/PORTFOLIO_SUMMARY.json"), {})
    program = load_json(Path("state/research/PROGRAM.json"), {})

    families = program.get("evolution_families") or []
    surfaces = program.get("surfaces") or []
    family_statuses: dict[str, int] = {}
    surface_statuses: dict[str, int] = {}

    for family in families:
        if isinstance(family, dict):
            status = str(family.get("status", "UNKNOWN"))
            family_statuses[status] = family_statuses.get(status, 0) + 1

    for surface in surfaces:
        if isinstance(surface, dict):
            status = str(surface.get("status", "UNKNOWN"))
            surface_statuses[status] = surface_statuses.get(status, 0) + 1

    return {
        "candidate_requests": int(summary.get("candidate_requests", 0) or 0),
        "behavioral_differences": int(summary.get("behavioral_differences", 0) or 0),
        "repeat_reproductions": int(summary.get("repeat_reproductions", 0) or 0),
        "executed_generations": int(summary.get("executed_generations", 0) or 0),
        "compiled_generations": int(summary.get("compiled_generations", 0) or 0),
        "families_represented": len(summary.get("families_represented") or []),
        "surfaces_represented": len(summary.get("surfaces_represented") or []),
        "family_count": len(families),
        "surface_count": len(surfaces),
        "family_statuses": family_statuses,
        "surface_statuses": surface_statuses,
    }


def file_integrity(path: str) -> bool:
    p = Path(path)
    return p.is_file() and p.stat().st_size > 0


def previous_record(
    history_path: Path,
    activation_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                rows.append(value)

    previous = rows[-1] if rows else None
    for index in range(len(rows) - 1, -1, -1):
        if str(rows[index].get("activation_id")) == activation_id:
            previous = rows[index - 1] if index > 0 else None
            break

    return previous, rows


def metric_progress_delta(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, float]:
    keys = (
        "candidate_requests",
        "behavioral_differences",
        "repeat_reproductions",
        "executed_generations",
        "families_represented",
        "surfaces_represented",
        "negated_surfaces",
        "exhausted_surfaces",
    )
    if not previous:
        return {key: 0.0 for key in keys}

    prev = previous.get("portfolio") or {}
    return {
        "candidate_requests": nonnegative_delta(
            current["candidate_requests"], prev.get("candidate_requests", 0)
        ),
        "behavioral_differences": nonnegative_delta(
            current["behavioral_differences"], prev.get("behavioral_differences", 0)
        ),
        "repeat_reproductions": nonnegative_delta(
            current["repeat_reproductions"], prev.get("repeat_reproductions", 0)
        ),
        "executed_generations": nonnegative_delta(
            current["executed_generations"], prev.get("executed_generations", 0)
        ),
        "families_represented": nonnegative_delta(
            current["families_represented"], prev.get("families_represented", 0)
        ),
        "surfaces_represented": nonnegative_delta(
            current["surfaces_represented"], prev.get("surfaces_represented", 0)
        ),
        "negated_surfaces": nonnegative_delta(
            current["surface_statuses"].get("NEGATED", 0),
            (prev.get("surface_statuses") or {}).get("NEGATED", 0),
        ),
        "exhausted_surfaces": nonnegative_delta(
            current["surface_statuses"].get("EXHAUSTED_FOR_NOW", 0),
            (prev.get("surface_statuses") or {}).get("EXHAUSTED_FOR_NOW", 0),
        ),
    }


def classify_progress(
    delta: dict[str, float],
    benchmark: dict[str, float],
    previous_benchmark: dict[str, float] | None,
    healthy: bool,
    delivery_ok: bool,
) -> str:
    if not healthy:
        return "BLOCKED"

    if previous_benchmark is not None:
        benchmark_gain = max(
            0.0,
            benchmark.get("overall_score", 0.0) - previous_benchmark.get("overall_score", 0.0),
            benchmark.get("discovery_rate", 0.0) - previous_benchmark.get("discovery_rate", 0.0),
            benchmark.get("reproduction_rate", 0.0) - previous_benchmark.get("reproduction_rate", 0.0),
            benchmark.get("precision_component", 0.0) - previous_benchmark.get("precision_component", 0.0),
        )
        if benchmark_gain > 0:
            return "BREAKTHROUGH"

    material = (
        delta["behavioral_differences"]
        + delta["repeat_reproductions"]
        + delta["families_represented"]
        + delta["surfaces_represented"]
        + delta["negated_surfaces"]
        + delta["exhausted_surfaces"]
    )
    if material > 0:
        return "ADVANCE"

    if delta["candidate_requests"] > 0 or delta["executed_generations"] > 0:
        return "INCREMENTAL"

    if delivery_ok:
        return "STABLE"

    return "STALLED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", default="")
    parser.add_argument("--history", default="state/research/PROCESS_HISTORY.jsonl")
    parser.add_argument("--output", default="state/research/PROGRESS.json")
    parser.add_argument("--preflight", default="unknown")
    parser.add_argument("--smoke", default="unknown")
    parser.add_argument("--portfolio", default="unknown")
    parser.add_argument("--worker", default="unknown")
    parser.add_argument("--evaluate", default="unknown")
    parser.add_argument("--persist", default="pending")
    args = parser.parse_args()

    activation_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    benchmark = benchmark_result(Path(args.result)) if args.result else {}
    benchmark_public = {
        "overall_score": float(benchmark.get("overall_score", 0.0) or 0.0),
        "discovery_rate": float(benchmark.get("discovery_rate", 0.0) or 0.0),
        "reproduction_rate": float(benchmark.get("reproduction_rate", 0.0) or 0.0),
        "precision_component": float(benchmark.get("precision_component", 0.0) or 0.0),
        "evidence_quality": float(benchmark.get("evidence_quality", 0.0) or 0.0),
        "finding_count_submitted": int(benchmark.get("finding_count_submitted", 0) or 0),
        "reproduced_claim_count": int(benchmark.get("reproduced_claim_count", 0) or 0),
        "unmatched_claim_count": int(benchmark.get("unmatched_claim_count", 0) or 0),
    }

    current = portfolio_state()
    previous, rows = previous_record(Path(args.history), activation_id)
    previous_benchmark = (previous or {}).get("benchmark")
    delta = metric_progress_delta(current, previous)

    findings_ok = file_integrity("reports/benchmark_findings.json")
    proposal_ok = file_integrity("PROGRAM_PROPOSAL.json")
    research_report_ok = file_integrity("reports/benchmark_research.md")
    delivery_ok = findings_ok and proposal_ok and research_report_ok

    execution_healthy = all(
        value == "success"
        for value in (args.preflight, args.smoke, args.portfolio)
    )

    surface_total = max(1, current["surface_count"])
    active_surface_count = sum(
        count
        for status, count in current["surface_statuses"].items()
        if status not in {"ARCHIVED", "NEGATED"}
    )

    reproduction_density = current["repeat_reproductions"] / max(
        1, current["candidate_requests"]
    )
    behavioral_difference_rate = current["behavioral_differences"] / max(
        1, current["candidate_requests"]
    )
    surface_coverage = current["surfaces_represented"] / surface_total

    novelty_signal = saturate(delta["behavioral_differences"], scale=2.0)
    reproduction_signal = saturate(delta["repeat_reproductions"], scale=2.0)
    breadth_signal = clamp(
        (delta["families_represented"] + delta["surfaces_represented"]) / 4.0
    )
    falsification_signal = clamp(
        (delta["negated_surfaces"] + delta["exhausted_surfaces"]) / 3.0
    )
    information_gain = round(
        0.40 * novelty_signal
        + 0.30 * reproduction_signal
        + 0.20 * breadth_signal
        + 0.10 * falsification_signal,
        4,
    )

    process_metrics = {
        "execution_reliability": 1.0 if execution_healthy else 0.0,
        "surface_coverage": round(clamp(surface_coverage), 4),
        "active_surface_coverage": round(
            clamp(current["surfaces_represented"] / max(1, active_surface_count)),
            4,
        ),
        "behavioral_difference_rate": round(clamp(behavioral_difference_rate), 4),
        "reproduction_density": round(clamp(reproduction_density), 4),
        "activation_information_gain": information_gain,
        "falsification_signal": round(falsification_signal, 4),
        "delivery_integrity": 1.0 if delivery_ok else 0.0,
    }

    process_score = round(sum(process_metrics.values()) / len(process_metrics), 4)
    progress_state = classify_progress(
        delta,
        benchmark_public,
        previous_benchmark,
        execution_healthy,
        delivery_ok,
    )

    if previous_benchmark is None:
        benchmark_signal = "BASELINE"
    else:
        benchmark_delta = benchmark_public["overall_score"] - previous_benchmark.get(
            "overall_score", 0.0
        )
        if benchmark_delta > 0.01:
            benchmark_signal = "IMPROVING"
        elif benchmark_delta < -0.01:
            benchmark_signal = "DECLINING"
        else:
            benchmark_signal = "UNCHANGED"

    record = {
        "schema_version": 3,
        "activation_id": activation_id,
        "observed_at_utc": observed_at,
        "progress_state": progress_state,
        "benchmark_signal": benchmark_signal,
        "execution": {
            "preflight": args.preflight,
            "smoke": args.smoke,
            "portfolio": args.portfolio,
            "worker": args.worker,
            "evaluate": args.evaluate,
            "persist": args.persist,
            "healthy": execution_healthy,
        },
        "benchmark": benchmark_public,
        "portfolio": current,
        "delta": delta,
        "process_score": process_score,
        "process_metrics": process_metrics,
        "deliverables": {
            "findings": findings_ok,
            "proposal": proposal_ok,
            "research_report": research_report_ok,
            "complete": delivery_ok,
        },
        "interpretation": {
            "benchmark_score_is_outcome_only": True,
            "progress_is_tracked_by_process_and_state_changes": True,
            "stagnation": progress_state in {"STABLE", "STALLED"} and information_gain == 0.0,
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    history_path = Path(args.history)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    new_rows = [row for row in rows if str(row.get("activation_id")) != activation_id]
    new_rows.append(record)
    history_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in new_rows[-200:]),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "progress_state": progress_state,
                "benchmark_signal": benchmark_signal,
                "process_score": process_score,
                "activation_information_gain": information_gain,
                "delta": delta,
                "deliverables_complete": delivery_ok,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
