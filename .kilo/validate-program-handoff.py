#!/usr/bin/env python3
"""Worker-visible validator for state/research/PROGRAM.json.

This mirrors the trusted controller's machine-readable handoff contract so the
worker can catch invalid program state before ending an activation.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
ID_RE = re.compile(r"^cand-[0-9a-f]{20}$")
ACTIVE_STATUSES = {
    "ACTIVE", "ACTIVE_HIGH_INTENSITY", "ACTIVE_LOW_INTENSITY",
    "DEPRIORITIZED", "READY_FOR_REVIEW", "SUBSTANTIAL_EFFORT",
    "EXHAUSTED_FOR_NOW", "REOPENED", "VERIFIED", "NEGATED",
}


def fail(message: str) -> None:
    raise SystemExit("PROGRAM_HANDOFF_INVALID: " + message)


def validate_request(value, label: str) -> None:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    method = str(value.get("method", "GET")).upper()
    if method not in SAFE_METHODS:
        fail(f"{label}.method={method} is not safe")
    path = value.get("path")
    if not isinstance(path, str) or not path.startswith("/") or "://" in path:
        fail(f"{label}.path must be relative")
    if not isinstance(value.get("query", {}), dict):
        fail(f"{label}.query must be an object")
    if not isinstance(value.get("headers", {}), dict):
        fail(f"{label}.headers must be an object")
    if value.get("body") not in (None, "", {}, []):
        fail(f"{label}.body is forbidden")


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def candidate_id(request_value: dict) -> str:
    return "cand-" + hashlib.sha256(canonical(request_value).encode("utf-8")).hexdigest()[:20]


def normalize_candidate_request(value, label: str) -> dict:
    validate_request(value, label)
    method = str(value.get("method", "GET")).upper()
    raw_query = value.get("query") or {}
    query = {}
    for key, raw in raw_query.items():
        if not isinstance(key, str) or not key:
            fail(f"{label}.query contains an invalid key")
        vals = raw if isinstance(raw, list) else [raw]
        if len(vals) > 4:
            fail(f"{label}.query.{key} has too many duplicate values")
        query[key] = [str(item) for item in vals]
    headers = {str(k): str(v) for k, v in (value.get("headers") or {}).items()}
    return {"method": method, "path": value["path"], "query": query, "headers": headers}


def main() -> int:
    path = Path("state/research/PROGRAM.json")
    if not path.is_file():
        fail("state/research/PROGRAM.json is missing")
    try:
        program = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"PROGRAM.json is not valid JSON: {exc}")

    if program.get("program_version") != "1.0.0":
        fail("unsupported program_version")
    discovery = program.get("discovery") or {}
    if discovery.get("surface_map_exhaustive") is not False or discovery.get("open_world") is not True:
        fail("discovery must declare non-exhaustive open-world research")

    surfaces = program.get("surfaces")
    families = program.get("evolution_families")
    if not isinstance(surfaces, list) or not isinstance(families, list):
        fail("surfaces and evolution_families must be lists")

    surface_ids = {s.get("surface_id") for s in surfaces if isinstance(s, dict)}
    family_ids = {f.get("family_id") for f in families if isinstance(f, dict)}
    family_by_surface = {}

    for i, family in enumerate(families):
        if not isinstance(family, dict):
            fail(f"evolution_families[{i}] is not an object")
        fid = family.get("family_id")
        sid = family.get("surface_id")
        if not fid or sid not in surface_ids:
            fail(f"family {fid!r} references unknown surface {sid!r}")
        family_by_surface.setdefault(sid, []).append(family)
        if not isinstance(family.get("lineage"), list):
            fail(f"family {fid} must retain lineage")
        for j, seed in enumerate(family.get("seed_requests") or []):
            validate_request(seed, f"family {fid} seed {j}")
        for j, candidate in enumerate(family.get("best_candidates") or []):
            if not isinstance(candidate, dict):
                fail(f"family {fid} best_candidates[{j}] must be an object")
            for field in ("candidate_id", "parent_candidate_id", "mutation", "response_signature"):
                if field not in candidate:
                    fail(f"family {fid} candidate {j} missing {field}")
            normalized_candidate = normalize_candidate_request(
                candidate.get("request"), f"family {fid} candidate {j}.request"
            )
            expected_candidate_id = candidate_id(normalized_candidate)
            if candidate.get("candidate_id") != expected_candidate_id:
                fail(
                    f"family {fid} candidate {j} has inconsistent candidate_id "
                    f"(expected {expected_candidate_id}, got {candidate.get('candidate_id')!r})"
                )
            if not isinstance(candidate.get("parent_candidate_id"), str):
                fail(f"family {fid} candidate {j}.parent_candidate_id must be a string")

    for i, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            fail(f"surfaces[{i}] is not an object")
        sid = surface.get("surface_id")
        status = surface.get("status", "CANDIDATE")
        if status in ACTIVE_STATUSES:
            active_families = [f for f in family_by_surface.get(sid, []) if f.get("status") != "ARCHIVED"]
            if not active_families:
                fail(
                    f"active surface {sid} has no durable family; "
                    "keep it CANDIDATE until a non-archived family exists"
                )
        declared = surface.get("evolutionary_families")
        if isinstance(declared, list):
            unknown = [fid for fid in declared if fid not in family_ids]
            if unknown:
                fail(f"surface {sid} declares unknown evolutionary families: {unknown}")

    print(
        "PROGRAM_HANDOFF_VALID=1",
        f"surfaces={len(surfaces)}",
        f"families={len(families)}",
        f"active_surfaces={sum(1 for s in surfaces if s.get('status') in ACTIVE_STATUSES)}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
