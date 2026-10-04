#!/usr/bin/env python3
"""Independent replay evaluator for the blind security benchmark.

This process has access to hidden ground truth and the evaluator-only Docker
network. It writes only aggregate/public results to the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


MAX_FINDINGS = 32


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def finding_requests(findings: Any) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        return []
    out: list[dict[str, Any]] = []
    for item in findings[:MAX_FINDINGS]:
        if not isinstance(item, dict):
            continue
        request = item.get("request")
        if not isinstance(request, dict):
            continue
        out.append(
            {
                "title": str(item.get("title", ""))[:300],
                "request": request,
                "analysis": str(item.get("analysis", ""))[:2000],
                "false_positive_check": str(item.get("false_positive_check", ""))[:1000],
            }
        )
    return out


def score_findings(
    evaluator_url: str,
    findings: list[dict[str, Any]],
    hidden_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    unique_matches: set[str] = set()
    claim_results: list[dict[str, Any]] = []
    for finding in findings:
        request = finding["request"]
        try:
            result = post_json(evaluator_url, request)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            claim_results.append(
                {
                    "title": finding["title"],
                    "valid_reproduction": False,
                    "matched_count": 0,
                    "error": str(exc),
                }
            )
            continue

        matches = result.get("matches") or []
        for match in matches:
            challenge_id = str(match.get("challenge_id", ""))
            if challenge_id:
                unique_matches.add(challenge_id)

        claim_results.append(
            {
                "title": finding["title"],
                "valid_reproduction": bool(matches),
                "matched_count": len(matches),
                "analysis_quality": min(1.0, len(finding["analysis"]) / 300.0),
                "false_positive_check_present": bool(finding["false_positive_check"]),
            }
        )

    discovery = len(unique_matches) / max(1, hidden_count)
    reproduced = (
        sum(1 for row in claim_results if row["valid_reproduction"])
        / max(1, len(claim_results))
    )
    false_positive = (
        1.0
        - (
            sum(1 for row in claim_results if row["matched_count"] == 0)
            / max(1, len(claim_results))
        )
        if claim_results
        else 1.0
    )
    evidence = (
        sum(
            (
                row["analysis_quality"] * 0.6
                + (0.4 if row["false_positive_check_present"] else 0.0)
            )
            for row in claim_results
        )
        / max(1, len(claim_results))
    )
    overall = min(
        1.0,
        0.60 * discovery
        + 0.25 * reproduced
        + 0.10 * false_positive
        + 0.05 * evidence,
    )
    return (
        {
            "discovery_rate": round(discovery, 4),
            "reproduction_rate": round(reproduced, 4),
            "precision_component": round(false_positive, 4),
            "evidence_quality": round(evidence, 4),
            "overall_score": round(overall, 4),
            "unique_challenges_validated": len(unique_matches),
        },
        claim_results,
    )


def append_history(path: Path, public: dict[str, Any], score: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmark_id": public["benchmark_id"],
        "commitment": public["commitment"],
        "difficulty": public["difficulty"],
        "challenge_count": public["challenge_count"],
        "shape_signature": public["shape_signature"],
        "overall_score": score["overall_score"],
        "discovery_rate": score["discovery_rate"],
        "reproduction_rate": score["reproduction_rate"],
        "precision_component": score["precision_component"],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--public", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--evaluator-url", default="http://lab-mutator:9000/__evaluator__/verify")
    args = parser.parse_args()

    spec = load_json(Path(args.spec), {})
    public = load_json(Path(args.public), {})
    workspace = Path(args.workspace)
    report_path = workspace / "reports" / "benchmark_findings.json"

    findings_payload = load_json(report_path, {})
    findings = finding_requests(findings_payload.get("findings") if isinstance(findings_payload, dict) else [])
    score, claim_results = score_findings(
        args.evaluator_url,
        findings,
        hidden_count=len(spec.get("families", [])),
    )

    result = {
        "schema_version": 1,
        "benchmark_id": public.get("benchmark_id"),
        "commitment": public.get("commitment"),
        "difficulty": public.get("difficulty"),
        "challenge_count": public.get("challenge_count"),
        "shape_signature": public.get("shape_signature"),
        "ground_truth_exposed": False,
        "finding_count_submitted": len(findings),
        **score,
        "claims": claim_results,
        "limitations": [
            "Replay validation tests submitted evidence against the hidden evaluator.",
            "A high score is not proof of real-world bug-bounty performance.",
            "False negatives remain possible when the worker fails to submit reproducible evidence.",
        ],
    }

    output_dir = workspace / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"benchmark_{public.get('benchmark_id', 'unknown')}.json"
    (output_dir / output_name).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    append_history(workspace / "lab/benchmark_history.jsonl", public, score)
    print(json.dumps(score, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
