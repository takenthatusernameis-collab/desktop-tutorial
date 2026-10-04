#!/usr/bin/env python3
"""Independent replay evaluator for the blind security benchmark.

This process has access to hidden ground truth and the evaluator-only Docker
network. It writes only aggregate/public results to the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutator


MAX_FINDINGS = 32


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


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


def verify_request(spec: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    mutator.SPEC = spec
    mutator.STATE = {"business_used": set(), "method_deleted": set()}

    method = str(request.get("method", "GET")).upper()
    url = str(request.get("url", ""))
    parsed = mutator.urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    headers = {
        str(k): str(v)
        for k, v in (request.get("headers") or {}).items()
    }
    body = request.get("body") or {}
    if not isinstance(body, dict):
        body = {}

    challenges = mutator.challenge_for_request(method, parsed.path or "/")
    matches: list[dict[str, Any]] = []
    for ch in challenges:
        vulnerable = mutator.local_handle(
            method, path, headers, body, [ch], mutate=ch.get("mode") != "secure_decoy"
        )
        secure = mutator.local_handle(
            method, path, headers, body, [ch], mutate=False
        )
        if vulnerable is None or secure is None:
            continue
        if ch.get("mode") == "vulnerable" and mutator.semantic_diff(vulnerable, secure):
            matches.append(
                {
                    "challenge_id": ch["id"],
                    "family": ch["family"],
                    "vulnerable_status": vulnerable[0],
                    "secure_status": secure[0],
                    "behavioral_difference": True,
                }
            )
    return {"valid_target": parsed.hostname in {"lab-mutator", "127.0.0.1", None}, "matches": matches}


def score_findings(
    spec: dict[str, Any],
    findings: list[dict[str, Any]],
    hidden_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    unique_matches: set[str] = set()
    claim_results: list[dict[str, Any]] = []
    for finding in findings:
        try:
            result = verify_request(spec, finding["request"])
        except Exception as exc:
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
    precision = (
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
        + 0.10 * precision
        + 0.05 * evidence,
    )
    return (
        {
            "discovery_rate": round(discovery, 4),
            "reproduction_rate": round(reproduced, 4),
            "precision_component": round(precision, 4),
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
    args = parser.parse_args()

    spec = load_json(Path(args.spec), {})
    public = load_json(Path(args.public), {})
    workspace = Path(args.workspace)
    report_path = workspace / "reports" / "benchmark_findings.json"

    findings_payload = load_json(report_path, {})
    findings = finding_requests(findings_payload.get("findings") if isinstance(findings_payload, dict) else [])
    score, claim_results = score_findings(
        spec,
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
