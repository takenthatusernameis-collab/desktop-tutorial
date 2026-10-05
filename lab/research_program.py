#!/usr/bin/env python3
"""Deterministic controller-side compiler and executor for the research program.

Kilo may propose only declarative research programs in state/research/PROGRAM.json.
This module is the trusted execution boundary: it validates the program, compiles a
bounded sequential portfolio, executes safe black-box request mutations against
the authorized mutation gateway, and records auditable generation receipts.

No hidden benchmark specification or evaluator implementation is exposed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, Callable
from urllib import error, parse, request


PROGRAM_VERSION = "1.0.0"
CONTROLLER_VERSION = "1.0.0"

PROGRAM = "PROGRAM.json"
RUNTIME = "RUNTIME.json"
SURFACES = "SURFACES.json"
FAMILIES = "EVOLUTION_FAMILIES.json"
RECEIPTS = "EXECUTION_RECEIPTS.jsonl"
CHECKLIST = "PORTFOLIO_CHECKLIST.md"
SUMMARY = "PORTFOLIO_SUMMARY.json"
COMPILED = "COMPILED_PORTFOLIO.json"
GENERATIONS = "GENERATIONS"
RESULTS = "RESULTS"
REVIEWS = "REVIEWS"

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
ALLOWED_OPERATORS = {
    "BASELINE",
    "QUERY_EDGE_VALUES",
    "DUPLICATE_QUERY",
    "ENCODING_VARIANTS",
    "PATH_VARIANTS",
    "METHOD_VARIANTS",
    "HEADER_ORIGIN_VARIANTS",
    "PARAMETER_OMISSION",
}
SURFACE_STATUSES = {
    "CANDIDATE",
    "ACTIVE",
    "ACTIVE_HIGH_INTENSITY",
    "ACTIVE_LOW_INTENSITY",
    "DEPRIORITIZED",
    "READY_FOR_REVIEW",
    "SUBSTANTIAL_EFFORT",
    "EXHAUSTED_FOR_NOW",
    "REOPENED",
    "VERIFIED",
    "NEGATED",
}
FAMILY_STATUSES = set(SURFACE_STATUSES)
ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,96}$")
MAX_SURFACES = 256
MAX_FAMILIES = 1024
MAX_GENERATIONS = 128
MAX_CANDIDATES = 24
MAX_BODY = 128_000
MAX_TIMEOUT = 12.0
FORBIDDEN_MARKERS = (
    "spec.json",
    "evaluate_benchmark.py",
    "evaluate_benchmark",
    "mutator.py",
    "/run/lab",
    "hidden evaluator",
    "hidden_evaluator",
    "challenge_id",
    "lab_secret",
)


class ProgramError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProgramError(f"invalid JSONL in {path} line {line_no}") from exc
        if not isinstance(row, dict):
            raise ProgramError(f"JSONL row {line_no} in {path} is not an object")
        rows.append(row)
    return rows


def ensure_dirs(state_dir: Path) -> None:
    for dirname in (GENERATIONS, RESULTS, REVIEWS):
        (state_dir / dirname).mkdir(parents=True, exist_ok=True)


def ensure_readme(state_dir: Path) -> None:
    path = state_dir / "README.md"
    if path.exists():
        return
    path.write_text(
        """# Research program state

PROGRAM.json is the Kilo-authored declarative next research program.
The trusted controller validates and executes it.

Controller-owned evidence:
- RUNTIME.json
- SURFACES.json
- EVOLUTION_FAMILIES.json
- EXECUTION_RECEIPTS.jsonl
- COMPILED_PORTFOLIO.json
- GENERATIONS/
- RESULTS/
- PORTFOLIO_SUMMARY.json
- PORTFOLIO_CHECKLIST.md

REVIEWS/ contains Kilo's strategic review notes.
The vulnerability landscape is permanently open-world; the initial surface map is never exhaustive.
""",
        encoding="utf-8",
    )


def validate_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ProgramError(f"{label} has invalid identifier: {value!r}")
    return value


def reject_forbidden(value: Any, label: str) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in text:
            raise ProgramError(f"{label} contains forbidden control-plane marker: {marker}")


def normalize_target(target: str) -> str:
    parsed = parse.urlsplit(target)
    if parsed.scheme != "http" or parsed.hostname != "lab-mutator" or parsed.port not in (None, 3000):
        raise ProgramError("controller target must be exactly http://lab-mutator:3000")
    return "http://lab-mutator:3000"


def normalize_query(value: Any) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ProgramError("request.query must be an object")
    out = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not key:
            raise ProgramError("query keys must be non-empty strings")
        vals = raw if isinstance(raw, list) else [raw]
        if len(vals) > 4:
            raise ProgramError(f"too many duplicate values for query key {key}")
        out[key] = [str(item) for item in vals]
    return out


def normalize_request(raw: Any, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ProgramError(f"{label} must be an object")
    method = str(raw.get("method", "GET")).upper()
    if method not in SAFE_METHODS:
        raise ProgramError(f"{label} uses unsafe method {method}")
    path = raw.get("path", "/")
    if not isinstance(path, str) or not path.startswith("/") or "://" in path:
        raise ProgramError(f"{label}.path must be relative")
    if len(path) > 2048:
        raise ProgramError(f"{label}.path is too long")
    if any(segment == ".." for segment in parse.urlsplit(path).path.split("/")):
        raise ProgramError(f"{label}.path contains raw parent traversal")
    headers = raw.get("headers") or {}
    if not isinstance(headers, dict):
        raise ProgramError(f"{label}.headers must be an object")
    blocked = {"authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"}
    clean_headers = {}
    for key, value in headers.items():
        key_s, value_s = str(key), str(value)
        if key_s.lower() in blocked:
            raise ProgramError(f"{label} attempts to supply credential-bearing header {key_s}")
        if len(key_s) > 128 or len(value_s) > 1024:
            raise ProgramError(f"{label} has an oversized header")
        clean_headers[key_s] = value_s
    if raw.get("body") not in (None, "", {}, []):
        raise ProgramError(f"{label}.body is not allowed in deterministic safe mode")
    result = {
        "method": method,
        "path": path,
        "query": normalize_query(raw.get("query")),
        "headers": clean_headers,
    }
    reject_forbidden(result, label)
    return result


def request_url(target: str, req: dict[str, Any]) -> str:
    query = []
    for key in sorted(req["query"]):
        query.extend((key, value) for value in req["query"][key])
    encoded = parse.urlencode(query, doseq=True)
    base = target.rstrip("/") + req["path"]
    return base if not encoded else base + ("&" if "?" in base else "?") + encoded


def candidate_id(req: dict[str, Any]) -> str:
    return "cand-" + digest(req)[:20]


def retained_request(candidate: Any) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    request_value = candidate.get("request")
    if isinstance(request_value, dict):
        return normalize_request(request_value, "retained candidate request")
    if {"method", "path", "query", "headers"} <= set(candidate):
        return normalize_request(candidate, "retained candidate")
    return None


def select_promising_candidates(rows: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if row.get("behavioral_difference") and row.get("repeat_reproduction")
    ]
    eligible.sort(
        key=lambda row: (
            json.dumps(response_signature(row["observation"]), sort_keys=True),
            row["candidate_id"],
        )
    )

    selected: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()
    for row in eligible:
        signature = json.dumps(response_signature(row["observation"]), sort_keys=True)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        selected.append(
            {
                "candidate_id": row["candidate_id"],
                "parent_candidate_id": row["parent_candidate_id"],
                "request": row["request"],
                "mutation": row["mutation"],
                "response_signature": json.loads(signature),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def mutate_request(seed: dict[str, Any], operator: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    seed = normalize_request(seed, "seed")
    out: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if operator == "BASELINE":
        return [(seed, {"operator": operator, "mutation": "identity"})]

    if operator == "QUERY_EDGE_VALUES":
        for key in sorted(seed["query"]):
            for value in ("", "0", "-1", "1", "null", "true", "false", "%", "%2e%2e"):
                child = dict(seed)
                child["query"] = {k: list(v) for k, v in seed["query"].items()}
                child["query"][key] = [value]
                out.append((child, {"operator": operator, "parameter": key, "value": value}))
        return out

    if operator == "DUPLICATE_QUERY":
        for key in sorted(seed["query"]):
            child = dict(seed)
            child["query"] = {k: list(v) for k, v in seed["query"].items()}
            child["query"][key] = (child["query"][key] or [""])[:3] + ["desktop-evo-alt"]
            child["query"][key] = child["query"][key][:4]
            out.append((child, {"operator": operator, "parameter": key}))
        return out

    if operator == "ENCODING_VARIANTS":
        for key in sorted(seed["query"]):
            for value in seed["query"][key] or [""]:
                variants = (
                    ("percent", parse.quote(value, safe="")),
                    ("double_percent", parse.quote(parse.quote(value, safe=""), safe="")),
                    ("plus_space", value.replace(" ", "+")),
                )
                for name, variant in variants:
                    child = dict(seed)
                    child["query"] = {k: list(v) for k, v in seed["query"].items()}
                    child["query"][key] = [variant]
                    out.append((child, {"operator": operator, "parameter": key, "variant": name}))
        return out

    if operator == "PATH_VARIANTS":
        path = seed["path"]
        variants = []
        if path != "/" and not path.endswith("/"):
            variants.append(("trailing_slash", path + "/"))
        if path.endswith("/") and path != "/":
            variants.append(("without_trailing_slash", path.rstrip("/")))
        if "//" not in path[1:]:
            variants.append(("duplicate_separator", path.replace("/", "//", 1)))
        variants.append(("dot_suffix", path.rstrip("/") + "/."))
        for name, new_path in variants:
            child = dict(seed)
            child["path"] = new_path
            out.append((child, {"operator": operator, "variant": name}))
        return out

    if operator == "METHOD_VARIANTS":
        if seed["method"] != "GET":
            return []
        for method in ("HEAD", "OPTIONS"):
            child = dict(seed)
            child["method"] = method
            out.append((child, {"operator": operator, "method": method}))
        return out

    if operator == "HEADER_ORIGIN_VARIANTS":
        for origin in ("null", "https://example.invalid", "http://localhost"):
            child = dict(seed)
            child["headers"] = dict(seed["headers"])
            child["headers"]["Origin"] = origin
            out.append((child, {"operator": operator, "origin": origin}))
        return out

    if operator == "PARAMETER_OMISSION":
        for key in sorted(seed["query"]):
            child = dict(seed)
            child["query"] = {k: list(v) for k, v in seed["query"].items() if k != key}
            out.append((child, {"operator": operator, "omitted": key}))
        return out

    raise ProgramError(f"unsupported operator: {operator}")


def validate_program(program: Any, benchmark_id: str) -> dict[str, Any]:
    if not isinstance(program, dict):
        raise ProgramError("PROGRAM.json must be an object")
    if str(program.get("program_version")) != PROGRAM_VERSION:
        raise ProgramError("unsupported program_version")
    if str(program.get("benchmark_id")) != benchmark_id:
        raise ProgramError("program benchmark_id does not match current benchmark")
    discovery = program.get("discovery") or {}
    if discovery.get("surface_map_exhaustive") is not False:
        raise ProgramError("surface map must explicitly remain non-exhaustive")
    if discovery.get("open_world") is not True:
        raise ProgramError("open-world discovery must be enabled")
    if not isinstance(discovery.get("uncertainty_notes", []), list):
        raise ProgramError("discovery.uncertainty_notes must be a list")

    surfaces = program.get("surfaces")
    families = program.get("evolution_families")
    if not isinstance(surfaces, list) or not isinstance(families, list):
        raise ProgramError("program requires surfaces and evolution_families")
    if len(surfaces) > MAX_SURFACES or len(families) > MAX_FAMILIES:
        raise ProgramError("program exceeds deterministic registry bounds")

    surface_ids = set()
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            raise ProgramError(f"surface {index} is not an object")
        sid = validate_id(surface.get("surface_id"), f"surface[{index}].surface_id")
        if sid in surface_ids:
            raise ProgramError(f"duplicate surface_id {sid}")
        surface_ids.add(sid)
        status = str(surface.get("status", "CANDIDATE"))
        if status not in SURFACE_STATUSES | {"ARCHIVED"}:
            raise ProgramError(f"surface {sid} has invalid status {status}")
        if not isinstance(surface.get("history"), list):
            raise ProgramError(f"surface {sid} must retain a history list")
        _surface_score_value(surface.get("priority"), f"{sid}.priority", 0.5)
        _surface_score_value(surface.get("uncertainty"), f"{sid}.uncertainty", 0.5)
        _surface_intensity_value(surface.get("current_intensity"), f"{sid}.current_intensity", 1)
        if status == "ARCHIVED" and not surface.get("archive_reason"):
            raise ProgramError(f"archived surface {sid} requires archive_reason")
        reject_forbidden(surface, f"surface {sid}")

    family_ids = set()
    family_counts = {}
    for index, family in enumerate(families):
        if not isinstance(family, dict):
            raise ProgramError(f"family {index} is not an object")
        fid = validate_id(family.get("family_id"), f"family[{index}].family_id")
        if fid in family_ids:
            raise ProgramError(f"duplicate family_id {fid}")
        family_ids.add(fid)
        sid = validate_id(family.get("surface_id"), f"family[{index}].surface_id")
        if sid not in surface_ids:
            raise ProgramError(f"family {fid} refers to unknown surface {sid}")
        status = str(family.get("status", "CANDIDATE"))
        if status not in FAMILY_STATUSES | {"ARCHIVED"}:
            raise ProgramError(f"family {fid} has invalid status {status}")
        generation = int(family.get("generation", 1))
        if generation < 1:
            raise ProgramError(f"family {fid}.generation must be >= 1")
        operators = family.get("mutation_operators") or family.get("operators") or []
        if not isinstance(operators, list) or not operators:
            raise ProgramError(f"family {fid} has no operators")
        if any(op not in ALLOWED_OPERATORS for op in operators):
            raise ProgramError(f"family {fid} contains an unsupported operator")
        seeds = family.get("seed_requests") or []
        if not isinstance(seeds, list) or len(seeds) > 32:
            raise ProgramError(f"family {fid} has invalid seed_requests")
        for seed_index, seed in enumerate(seeds):
            normalize_request(seed, f"family {fid} seed {seed_index}")
        if not seeds:
            raise ProgramError(f"family {fid} has no executable seed requests")
        # Every family must compile to at least one deterministic candidate from
        # its current seeds/operators. This catches no-op operator/seed pairings
        # before the long activation reaches execution.
        if not any(
            mutate_request(seed, operator)
            for seed in seeds
            for operator in operators
        ):
            raise ProgramError(
                f"family {fid} compiles to zero candidates from its current "
                "seed_requests and mutation_operators; add a compatible operator "
                "(BASELINE is the universal fallback) or a compatible seed"
            )
        if not isinstance(family.get("lineage"), list):
            raise ProgramError(f"family {fid} must retain lineage")
        if status == "ARCHIVED" and not family.get("archive_reason"):
            raise ProgramError(f"archived family {fid} requires archive_reason")
        family_counts[sid] = family_counts.get(sid, 0) + (0 if status == "ARCHIVED" else 1)
        reject_forbidden(family, f"family {fid}")

    policy = program.get("portfolio_policy") or {}
    max_generations = int(policy.get("max_generations_per_activation", 24))
    max_candidates = int(policy.get("max_candidates_per_generation", 12))
    exploration = float(policy.get("exploration_reserve_fraction", 0.25))
    if not 1 <= max_generations <= MAX_GENERATIONS:
        raise ProgramError("portfolio generation budget is outside bounds")
    if not 1 <= max_candidates <= MAX_CANDIDATES:
        raise ProgramError("candidate budget is outside bounds")
    if not 0.0 <= exploration <= 1.0:
        raise ProgramError("exploration_reserve_fraction must be in [0,1]")

    required_breadth = {
        surface["surface_id"]
        for surface in surfaces
        if surface.get("status") in SURFACE_STATUSES
        and family_counts.get(surface["surface_id"], 0) > 0
    }
    if max_generations < len(required_breadth):
        raise ProgramError(
            "portfolio generation budget is smaller than required surface breadth: "
            f"{len(required_breadth)} surfaces > {max_generations} generations"
        )

    for surface in surfaces:
        if surface.get("status") in SURFACE_STATUSES and family_counts.get(surface["surface_id"], 0) == 0:
            if surface.get("status") != "CANDIDATE":
                raise ProgramError(
                    f"active surface {surface['surface_id']} has no durable non-archived family; "
                    "keep the surface CANDIDATE until a non-archived evolutionary family "
                    "is attached, or persist the required family before handoff"
                )
    return program


def validate_state(state_dir: Path, benchmark_id: str, mode: str) -> dict[str, Any] | None:
    """Validate persisted controller state without making network requests."""
    program_path = state_dir / PROGRAM
    if not program_path.exists():
        if mode == "fresh":
            print("RESEARCH_PROGRAM_VALIDATION=SKIP_NO_PROGRAM")
            return None
        raise ProgramError("resumed benchmark has no persisted PROGRAM.json")
    program = load_json(program_path)
    validate_program(program, benchmark_id)
    runtime = load_runtime(state_dir)
    plan = compile_portfolio(program, runtime)
    if mode != "fresh" and not plan:
        raise ProgramError("persisted research program compiled to an empty portfolio")
    for family in program.get("evolution_families", []):
        if family.get("status") == "ARCHIVED" or family.get("dormant"):
            continue
        fid = family["family_id"]
        runtime_generation = int(
            ((runtime.get("families") or {}).get(fid, {})).get("last_executed_generation", 0)
        )
        program_generation = int(family.get("generation", 1))
        if runtime_generation and program_generation != runtime_generation + 1:
            raise ProgramError(
                f"generation continuity divergence for {fid}: "
                f"program expects {program_generation}, runtime last executed {runtime_generation}"
            )

    print(
        f"RESEARCH_PROGRAM_VALIDATION=PASS surfaces={len(program.get('surfaces', []))} "
        f"families={len(program.get('evolution_families', []))} tickets={len(plan)}"
    )
    return program


def load_runtime(state_dir: Path) -> dict[str, Any]:
    path = state_dir / RUNTIME
    if not path.exists():
        return {
            "schema_version": PROGRAM_VERSION,
            "controller_version": CONTROLLER_VERSION,
            "benchmark_id": None,
            "cycles": 0,
            "families": {},
            "surfaces": {},
        }
    runtime = load_json(path)
    if not isinstance(runtime, dict):
        raise ProgramError("RUNTIME.json is invalid")
    return runtime


def archive_active_program(state_dir: Path, benchmark_id: str) -> None:
    program_path = state_dir / PROGRAM
    if not program_path.exists():
        return
    old = load_json(program_path) or {}
    old_id = str(old.get("benchmark_id", "unknown"))
    stamp = now_utc().replace(":", "").replace("-", "")
    archive = state_dir / "ARCHIVE" / f"{old_id}-{stamp}"
    archive.mkdir(parents=True, exist_ok=True)
    names = (
        PROGRAM,
        RUNTIME,
        SURFACES,
        FAMILIES,
        RECEIPTS,
        CHECKLIST,
        SUMMARY,
        COMPILED,
    )
    dirs = (GENERATIONS, RESULTS, REVIEWS)
    for name in names:
        path = state_dir / name
        if path.exists():
            shutil.move(str(path), archive / name)
    for name in dirs:
        path = state_dir / name
        if path.exists():
            shutil.move(str(path), archive / name)
    write_json(
        archive / "ARCHIVE_METADATA.json",
        {
            "archived_at": now_utc(),
            "previous_benchmark_id": old_id,
            "new_benchmark_id": benchmark_id,
            "reason": "new benchmark campaign",
        },
    )


def _surface_score_value(value: Any, field: str, default: float) -> float:
    """Convert controller score inputs without rejecting worker prose."""
    if isinstance(value, bool):
        raise ProgramError(f"surface {field} must not be boolean")
    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            score = default
        else:
            try:
                score = float(raw)
            except ValueError:
                upper = raw.upper()
                match = re.match(r"^(HIGH|MEDIUM|LOW)\\b", upper)
                if match:
                    score = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.2}[match.group(1)]
                else:
                    # Worker state may preserve explanatory prose in uncertainty.
                    # Treat unlabelled prose as an explicit-but-neutral score rather
                    # than crashing the trusted portfolio compiler.
                    score = default
    elif value is None:
        score = default
    else:
        raise ProgramError(
            f"surface {field} must be numeric, text, or omitted"
        )
    if not 0.0 <= score <= 1.0:
        raise ProgramError(f"surface {field} score must be in [0,1]")
    return score


def _surface_intensity_value(value: Any, field: str, default: int = 1) -> int:
    """Convert numeric or qualitative worker intensity values to 1..4."""
    if isinstance(value, bool):
        raise ProgramError(f"surface {field} must not be boolean")
    if isinstance(value, (int, float)):
        intensity = int(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            intensity = default
        else:
            try:
                intensity = int(float(raw))
            except ValueError:
                label = raw.lower()
                intensity = {
                    "minimal": 1,
                    "low": 2,
                    "medium": 3,
                    "moderate": 3,
                    "high": 4,
                    "full": 4,
                }.get(label, default)
    elif value is None:
        intensity = default
    else:
        raise ProgramError(f"surface {field} must be numeric, text, or omitted")
    return max(1, min(4, intensity))


def surface_priority(surface: dict[str, Any]) -> float:
    priority = _surface_score_value(surface.get("priority"), "priority", 0.5)
    uncertainty = _surface_score_value(surface.get("uncertainty"), "uncertainty", 0.5)
    status = str(surface.get("status"))
    bonus = 0.2 if status in {"ACTIVE_HIGH_INTENSITY", "REOPENED", "READY_FOR_REVIEW"} else 0.0
    maintenance = 0.03 if status in {"DEPRIORITIZED", "EXHAUSTED_FOR_NOW"} else 0.0
    return priority + uncertainty + bonus + maintenance


def compile_portfolio(program: dict[str, Any], runtime: dict[str, Any]) -> list[dict[str, Any]]:
    surfaces = {s["surface_id"]: s for s in program["surfaces"]}
    families = []
    for family in program["evolution_families"]:
        if family.get("status") == "ARCHIVED" or family.get("dormant"):
            continue
        if not family.get("seed_requests"):
            continue
        surface = surfaces[family["surface_id"]]
        if surface.get("status") == "ARCHIVED":
            continue
        family_id = family["family_id"]
        fr = (runtime.get("families") or {}).get(family_id, {})
        score = (
            surface_priority(surface)
            + float(fr.get("last_information_gain", 0.0))
            + (0.20 if fr.get("best_candidates") else 0.0)
            + min(0.25, 0.05 * max(0, int(family.get("generation", 1)) - int(fr.get("last_active_generation", 0))))
        )
        families.append((score, family_id, family))

    if not families:
        return []

    families.sort(key=lambda row: (-row[0], row[1]))
    max_generations = int((program.get("portfolio_policy") or {}).get("max_generations_per_activation", 24))
    max_candidates = int((program.get("portfolio_policy") or {}).get("max_candidates_per_generation", 12))

    tickets = {}
    for _, family_id, family in families:
        surface = surfaces[family["surface_id"]]
        intensity = _surface_intensity_value(
            surface.get("current_intensity", family.get("intensity", 1)),
            f"{surface['surface_id']}.current_intensity",
            1,
        )
        if surface.get("status") in {"DEPRIORITIZED", "EXHAUSTED_FOR_NOW"}:
            intensity = min(1, intensity)
        tickets[family_id] = max(1, min(4, intensity))

    all_relevant_surfaces = {
        s["surface_id"]
        for s in program["surfaces"]
        if s.get("status") in SURFACE_STATUSES and s["surface_id"] in {
            f["surface_id"] for _, _, f in families
        }
    }
    if len(all_relevant_surfaces) > max_generations:
        raise ProgramError(
            "portfolio generation budget is smaller than required surface breadth: "
            f"{len(all_relevant_surfaces)} surfaces > {max_generations} generations"
        )

    # Reserve one generation for every relevant surface before exploitation.
    plan = []
    scheduled_families: set[str] = set()
    best_family_by_surface: dict[str, tuple[float, str, dict[str, Any]]] = {}
    for row in families:
        surface_id = row[2]["surface_id"]
        best_family_by_surface.setdefault(surface_id, row)

    for surface_id in sorted(all_relevant_surfaces):
        _, family_id, family = best_family_by_surface[surface_id]
        plan.append(
            {
                "surface_id": surface_id,
                "family_id": family_id,
                "generation": int(family.get("generation", 1)),
                "round": 1,
                "max_candidates": max_candidates,
            }
        )
        scheduled_families.add(family_id)

    # Spend the remaining budget in score order, preserving family generation order.
    for round_index in range(1, max(tickets.values()) + 1):
        for _, family_id, family in families:
            if tickets[family_id] < round_index:
                continue
            if family_id in scheduled_families and round_index == 1:
                continue
            if len(plan) >= max_generations:
                break
            plan.append(
                {
                    "surface_id": family["surface_id"],
                    "family_id": family_id,
                    "generation": int(family.get("generation", 1)) + round_index - 1,
                    "round": round_index,
                    "max_candidates": max_candidates,
                }
            )
        if len(plan) >= max_generations:
            break

    covered_surfaces = {item["surface_id"] for item in plan}
    missing = sorted(all_relevant_surfaces - covered_surfaces)
    if missing:
        raise ProgramError("portfolio budget would starve surfaces: " + ", ".join(missing))
    return plan


def response_signature(observation: dict[str, Any]) -> tuple[Any, ...]:
    return (
        observation.get("status"),
        observation.get("body_sha256"),
        observation.get("content_type"),
        observation.get("body_length"),
        observation.get("location"),
    )


def perform_request(target: str, req: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    body = b""
    status = None
    content_type = ""
    location = ""
    error_text = None
    try:
        headers = dict(req.get("headers") or {})
        headers.setdefault("User-Agent", "DesktopResearchController/1.0")
        http_req = request.Request(request_url(target, req), headers=headers, method=req["method"])
        with request.urlopen(http_req, timeout=8.0) as response:
            status = int(response.status)
            body = response.read(MAX_BODY)
            content_type = response.headers.get("Content-Type", "")
            location = response.headers.get("Location", "")
    except error.HTTPError as exc:
        status = int(exc.code)
        body = exc.read(MAX_BODY)
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        location = exc.headers.get("Location", "") if exc.headers else ""
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
    return {
        "status": status,
        "body_length": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "content_type": content_type[:200],
        "location": location[:500],
        "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
        "error": error_text,
    }


def execute_generation(
    state_dir: Path,
    target: str,
    family: dict[str, Any],
    generation: int,
    max_candidates: int,
    transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    transport = transport or perform_request
    runtime = load_runtime(state_dir)
    fr = (runtime.get("families") or {}).get(family["family_id"], {})
    program_generation = int(family.get("generation", 1))
    runtime_generation = int(fr.get("last_executed_generation", 0))
    if generation != program_generation:
        raise ProgramError(
            f"generation continuity failure for {family['family_id']}: "
            f"got {generation}, program expects {program_generation}"
        )
    if runtime_generation and program_generation != runtime_generation + 1:
        raise ProgramError(
            f"generation continuity divergence for {family['family_id']}: "
            f"program expects {program_generation}, runtime last executed {runtime_generation}"
        )

    seeds: list[dict[str, Any]] = []
    retained_candidates = family.get("best_candidates") or fr.get("best_candidates") or []
    for candidate in retained_candidates:
        request_value = retained_request(candidate)
        if request_value is not None and request_value not in seeds:
            seeds.append(request_value)
    for seed in family.get("seed_requests") or []:
        normalized = normalize_request(seed, "seed")
        if normalized not in seeds:
            seeds.append(normalized)
    if not seeds:
        raise ProgramError(f"family {family['family_id']} has no executable seed requests")

    operators = list(family.get("mutation_operators") or family.get("operators") or [])
    candidates = []
    seen = set()
    for seed in seeds[:32]:
        normalized = normalize_request(seed, "seed")
        parent = candidate_id(normalized)
        for operator in operators:
            for child, mutation in mutate_request(normalized, operator):
                cid = candidate_id(child)
                if cid in seen:
                    continue
                seen.add(cid)
                candidates.append(
                    {
                        "candidate_id": cid,
                        "parent_candidate_id": parent,
                        "request": child,
                        "mutation": mutation,
                    }
                )
                if len(candidates) >= max_candidates:
                    break
            if len(candidates) >= max_candidates:
                break
        if len(candidates) >= max_candidates:
            break
    if not candidates:
        raise ProgramError(f"family {family['family_id']} compiled to zero candidates")

    seed_by_id = {
        candidate_id(normalize_request(seed, "seed")): normalize_request(seed, "seed")
        for seed in seeds
    }
    baseline_cache = {}
    rows = []
    differences = 0
    reproductions = 0
    errors_seen = 0

    for candidate in candidates:
        parent = candidate["parent_candidate_id"]
        if parent not in baseline_cache:
            baseline_cache[parent] = transport(target, seed_by_id[parent])
        observed = transport(target, candidate["request"])
        differs = response_signature(observed) != response_signature(baseline_cache[parent])
        reproduced = False
        repeat = None
        if differs:
            repeat = transport(target, candidate["request"])
            reproduced = response_signature(repeat) == response_signature(observed)
            differences += 1
            reproductions += int(reproduced)
        errors_seen += int(bool(observed.get("error")))
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "parent_candidate_id": parent,
                "request": candidate["request"],
                "mutation": candidate["mutation"],
                "baseline_observation": baseline_cache[parent],
                "observation": observed,
                "behavioral_difference": differs,
                "repeat_reproduction": reproduced,
                "repeat_observation": repeat,
            }
        )

    signature_count = len({
        json.dumps(response_signature(row["observation"]), sort_keys=True)
        for row in rows
    })
    information_gain = round(
        min(1.0, 0.5 * signature_count / max(1, len(rows)) + 0.5 * differences / max(1, len(rows))),
        4,
    )
    promising = select_promising_candidates(rows)

    return {
        "generation_id": f"gen-{generation:04d}-{family['family_id']}",
        "family_id": family["family_id"],
        "surface_id": family["surface_id"],
        "generation": generation,
        "observed_at": now_utc(),
        "candidate_count": len(rows),
        "operators": operators,
        "immutable_baseline": True,
        "actual_execution": True,
        "parent_lineage": [
            {
                "candidate_id": row["candidate_id"],
                "parent_candidate_id": row["parent_candidate_id"],
                "mutation": row["mutation"],
            }
            for row in rows
        ],
        "results": {
            "behavioral_differences": differences,
            "repeat_reproductions": reproductions,
            "error_observations": errors_seen,
            "unique_response_signatures": signature_count,
            "information_gain": information_gain,
        },
        "promising_candidates": promising,
        "stopping_reason": (
            "candidate budget reached"
            if len(rows) >= max_candidates
            else "operator candidate set exhausted"
        ),
        "observations": rows,
    }


def persist_generation(state_dir: Path, result: dict[str, Any]) -> None:
    receipt = {
        key: result[key]
        for key in (
            "generation_id",
            "family_id",
            "surface_id",
            "generation",
            "observed_at",
            "candidate_count",
            "operators",
            "immutable_baseline",
            "actual_execution",
            "parent_lineage",
            "results",
            "promising_candidates",
            "stopping_reason",
        )
    }
    append_jsonl(state_dir / RECEIPTS, receipt)
    write_json(state_dir / GENERATIONS / f"{result['generation_id']}.json", result)
    write_json(
        state_dir / RESULTS / f"{result['generation_id']}.json",
        {
            "generation_id": result["generation_id"],
            "family_id": result["family_id"],
            "surface_id": result["surface_id"],
            "generation": result["generation"],
            "candidate_count": result["candidate_count"],
            "information_gain": result["results"]["information_gain"],
            "behavioral_differences": result["results"]["behavioral_differences"],
            "repeat_reproductions": result["results"]["repeat_reproductions"],
            "promising_candidates": result["promising_candidates"],
            "observed_at": result["observed_at"],
        },
    )


def update_runtime(
    state_dir: Path,
    program: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    increment_cycle: bool = True,
) -> dict[str, Any]:
    runtime = load_runtime(state_dir)
    runtime["schema_version"] = PROGRAM_VERSION
    runtime["controller_version"] = CONTROLLER_VERSION
    runtime["benchmark_id"] = program["benchmark_id"]
    if increment_cycle:
        runtime["cycles"] = int(runtime.get("cycles", 0)) + 1
    runtime["last_execution"] = now_utc()
    runtime.setdefault("families", {})
    runtime.setdefault("surfaces", {})

    for result in results:
        fid, sid = result["family_id"], result["surface_id"]
        fr = runtime["families"].setdefault(fid, {})
        fr["surface_id"] = sid
        fr["last_executed_generation"] = result["generation"]
        fr["last_information_gain"] = result["results"]["information_gain"]
        fr["last_candidate_count"] = result["candidate_count"]
        fr["last_behavioral_differences"] = result["results"]["behavioral_differences"]
        fr["last_repeat_reproductions"] = result["results"]["repeat_reproductions"]
        fr["best_candidates"] = result["promising_candidates"]
        fr["novelty_seen"] = bool(result["results"]["behavioral_differences"])
        fr["last_active_generation"] = result["generation"]
        fr["updated_at"] = now_utc()

        sr = runtime["surfaces"].setdefault(
            sid,
            {
                "generations": 0,
                "candidate_requests": 0,
                "behavioral_differences": 0,
                "repeat_reproductions": 0,
                "families_executed": 0,
            },
        )
        sr["generations"] += 1
        sr["candidate_requests"] += result["candidate_count"]
        sr["behavioral_differences"] += result["results"]["behavioral_differences"]
        sr["repeat_reproductions"] += result["results"]["repeat_reproductions"]
        sr["families_executed"] += 1
        sr["last_execution"] = now_utc()

    write_json(state_dir / RUNTIME, runtime)
    return runtime


def materialize_registries(state_dir: Path, program: dict[str, Any], runtime: dict[str, Any]) -> None:
    surfaces = []
    counter_keys = (
        "generations",
        "candidate_requests",
        "behavioral_differences",
        "repeat_reproductions",
        "families_executed",
    )
    for surface in program["surfaces"]:
        sid = surface["surface_id"]
        sr = (runtime.get("surfaces") or {}).get(sid, {})
        raw_effort = surface.get("reasonable_effort_evidence")
        if isinstance(raw_effort, dict):
            effort = dict(raw_effort)
        elif raw_effort is None:
            effort = {}
        else:
            # Worker prose is evidence, not a schema violation. Preserve it
            # explicitly while keeping controller counters machine-readable.
            effort = {"evidence": raw_effort}
        for key in counter_keys:
            raw_base = effort.get(key, 0)
            raw_runtime = sr.get(key, 0)
            try:
                base_value = int(raw_base)
            except (TypeError, ValueError):
                base_value = 0
            try:
                runtime_value = int(raw_runtime)
            except (TypeError, ValueError):
                runtime_value = 0
            effort[key] = base_value + runtime_value
        surfaces.append({**surface, "runtime": sr, "reasonable_effort_evidence": effort})

    families = []
    for family in program["evolution_families"]:
        fr = (runtime.get("families") or {}).get(family["family_id"], {})
        families.append({**family, "runtime": fr})

    write_json(
        state_dir / SURFACES,
        {
            "schema_version": PROGRAM_VERSION,
            "benchmark_id": program["benchmark_id"],
            "surface_map_exhaustive": False,
            "open_world": True,
            "surfaces": surfaces,
            "generated_at": now_utc(),
        },
    )
    write_json(
        state_dir / FAMILIES,
        {
            "schema_version": PROGRAM_VERSION,
            "benchmark_id": program["benchmark_id"],
            "families": families,
            "generated_at": now_utc(),
        },
    )


def append_checklist(state_dir: Path, results: list[dict[str, Any]]) -> None:
    path = state_dir / CHECKLIST
    if not path.exists():
        path.write_text(
            "# Evolutionary research progression\n\n"
            "Controller-generated and append-oriented. Prior generations are never replaced.\n\n",
            encoding="utf-8",
        )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"## Portfolio cycle — {now_utc()}\n\n")
        for result in results:
            r = result["results"]
            handle.write(
                f"- {result['surface_id']} / {result['family_id']} / G{result['generation']}: "
                f"{result['candidate_count']} candidates; {r['behavioral_differences']} behavioral differences; "
                f"{r['repeat_reproductions']} repeat reproductions; information gain {r['information_gain']}; "
                f"stopping={result['stopping_reason']}.\n"
            )
        handle.write("\n")


def run_pre_kilo(
    mode: str,
    benchmark_id: str,
    target: str,
    state_dir: Path,
    transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
) -> int:
    state_dir.mkdir(parents=True, exist_ok=True)
    ensure_dirs(state_dir)
    ensure_readme(state_dir)
    target = normalize_target(target)

    if mode == "fresh":
        archive_active_program(state_dir, benchmark_id)
        write_json(
            state_dir / "DISCOVERY_REQUIRED.json",
            {
                "benchmark_id": benchmark_id,
                "mode": "fresh",
                "discovery": "KILO_INITIAL_DISCOVERY",
                "surface_map_exhaustive": False,
                "open_world": True,
                "created_at": now_utc(),
            },
        )
        print("RESEARCH_PORTFOLIO_STATUS=SKIPPED_NEW_BENCHMARK")
        return 0

    program_path = state_dir / PROGRAM
    if not program_path.exists():
        write_json(
            state_dir / "DISCOVERY_REQUIRED.json",
            {
                "benchmark_id": benchmark_id,
                "mode": "existing_campaign_bootstrap",
                "discovery": "KILO_DISCOVERY_BOOTSTRAP",
                "surface_map_exhaustive": False,
                "open_world": True,
                "created_at": now_utc(),
            },
        )
        print("RESEARCH_PORTFOLIO_STATUS=DISCOVERY_BOOTSTRAP_REQUIRED")
        return 0

    program = load_json(program_path)
    if program is None:
        raise ProgramError("PROGRAM.json is invalid JSON")
    validate_program(program, benchmark_id)
    runtime = load_runtime(state_dir)
    runtime["benchmark_id"] = benchmark_id
    write_json(state_dir / RUNTIME, runtime)

    plan = compile_portfolio(program, runtime)
    write_json(
        state_dir / COMPILED,
        {
            "schema_version": PROGRAM_VERSION,
            "controller_version": CONTROLLER_VERSION,
            "benchmark_id": benchmark_id,
            "target": target,
            "compiled_at": now_utc(),
            "actual_execution_required": True,
            "plan": plan,
        },
    )

    results = []
    runtime = load_runtime(state_dir)
    for index, item in enumerate(plan):
        family = next(f for f in program["evolution_families"] if f["family_id"] == item["family_id"])
        result = execute_generation(
            state_dir,
            target,
            family,
            int(item["generation"]),
            int(item["max_candidates"]),
            transport=transport,
        )
        persist_generation(state_dir, result)
        results.append(result)
        family["best_candidates"] = result["promising_candidates"]
        family["generation"] = int(family.get("generation", 1)) + 1

        # Advance runtime immediately so a second round for the same family sees
        # the newly executed generation. Persist PROGRAM/RUNTIME together after
        # every successful generation.
        runtime = update_runtime(
            state_dir,
            program,
            [result],
            increment_cycle=(index == 0),
        )
        write_json(program_path, program)

    materialize_registries(state_dir, program, runtime)
    append_checklist(state_dir, results)
    write_json(
        state_dir / SUMMARY,
        {
            "schema_version": PROGRAM_VERSION,
            "controller_version": CONTROLLER_VERSION,
            "benchmark_id": benchmark_id,
            "compiled_generations": len(plan),
            "executed_generations": len(results),
            "families_represented": sorted({r["family_id"] for r in results}),
            "surfaces_represented": sorted({r["surface_id"] for r in results}),
            "candidate_requests": sum(r["candidate_count"] for r in results),
            "behavioral_differences": sum(r["results"]["behavioral_differences"] for r in results),
            "repeat_reproductions": sum(r["results"]["repeat_reproductions"] for r in results),
            "actual_execution": True,
            "observed_at": now_utc(),
        },
    )
    (state_dir / "DISCOVERY_REQUIRED.json").unlink(missing_ok=True)
    print(f"RESEARCH_PORTFOLIO_STATUS=EXECUTED generations={len(results)}")
    return 0


def same_path(left: Path, right: Path) -> bool:
    if not left.exists() and not right.exists():
        return True
    if left.exists() != right.exists():
        return False
    if left.is_file() or right.is_file():
        return left.is_file() and right.is_file() and left.read_bytes() == right.read_bytes()
    left_files = sorted(p.relative_to(left).as_posix() for p in left.rglob("*") if p.is_file())
    right_files = sorted(p.relative_to(right).as_posix() for p in right.rglob("*") if p.is_file())
    if left_files != right_files:
        return False
    return all((left / rel).read_bytes() == (right / rel).read_bytes() for rel in left_files)


def restore_controller_owned(state_dir: Path, snapshot_dir: Path) -> None:
    for name in (RUNTIME, SURFACES, FAMILIES, RECEIPTS, CHECKLIST, SUMMARY, COMPILED):
        current, snapshot = state_dir / name, snapshot_dir / name
        if current.exists():
            if current.is_dir():
                shutil.rmtree(current)
            else:
                current.unlink()
        if snapshot.exists():
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snapshot, current)
    for name in (GENERATIONS, RESULTS):
        current, snapshot = state_dir / name, snapshot_dir / name
        if current.exists():
            shutil.rmtree(current)
        if snapshot.exists():
            shutil.copytree(snapshot, current)


def validate_continuity(previous: dict[str, Any] | None, current: dict[str, Any]) -> None:
    if previous is None:
        return
    old_surfaces = {s["surface_id"]: s for s in previous.get("surfaces", [])}
    new_surfaces = {s["surface_id"]: s for s in current.get("surfaces", [])}
    missing_surfaces = sorted(set(old_surfaces) - set(new_surfaces))
    if missing_surfaces:
        raise ProgramError(
            "Kilo removed specializations instead of preserving them: " + ", ".join(missing_surfaces)
        )
    old_families = {f["family_id"]: f for f in previous.get("evolution_families", [])}
    new_families = {f["family_id"]: f for f in current.get("evolution_families", [])}
    missing_families = sorted(set(old_families) - set(new_families))
    if missing_families:
        raise ProgramError(
            "Kilo removed evolutionary families instead of preserving them: " + ", ".join(missing_families)
        )
    for fid, old in old_families.items():
        cur = new_families[fid]
        if not isinstance(cur.get("lineage"), list) or not isinstance(old.get("lineage"), list):
            raise ProgramError(f"family {fid} lost lineage history")
        if int(cur.get("generation", 1)) < int(old.get("generation", 1)):
            raise ProgramError(f"family {fid} generation regressed")
    for sid, old in old_surfaces.items():
        cur = new_surfaces[sid]
        old_effort = old.get("reasonable_effort_evidence") or {}
        cur_effort = cur.get("reasonable_effort_evidence") or {}
        for key, old_value in old_effort.items():
            if isinstance(old_value, (int, float)) and float(cur_effort.get(key, old_value)) < float(old_value):
                raise ProgramError(f"surface {sid} effort evidence regressed for {key}")


def post_kilo(mode: str, benchmark_id: str, state_dir: Path, snapshot_dir: Path) -> int:
    program_path = state_dir / PROGRAM
    previous = load_json(snapshot_dir / PROGRAM)
    current = load_json(program_path)

    controller_paths = (RUNTIME, SURFACES, FAMILIES, RECEIPTS, CHECKLIST, SUMMARY, COMPILED)
    controller_dirs = (GENERATIONS, RESULTS)
    tampered = any(
        not same_path(state_dir / name, snapshot_dir / name)
        for name in controller_paths
    ) or any(
        not same_path(state_dir / name, snapshot_dir / name)
        for name in controller_dirs
    )
    if tampered:
        restore_controller_owned(state_dir, snapshot_dir)
        print("RESEARCH_PROGRAM_VALIDATION=FAIL controller-owned execution evidence was modified")
        return 1

    if current is None:
        if previous is None:
            print("RESEARCH_PROGRAM_VALIDATION=UNVERIFIED Kilo did not persist an initial research program")
            return 1
        restore_controller_owned(state_dir, snapshot_dir)
        shutil.copy2(snapshot_dir / PROGRAM, program_path)
        print("RESEARCH_PROGRAM_VALIDATION=FAIL existing research program disappeared")
        return 1

    try:
        validate_program(current, benchmark_id)
        validate_continuity(previous, current)
    except ProgramError as exc:
        if previous is not None:
            write_json(program_path, previous)
        else:
            program_path.unlink(missing_ok=True)
        print(f"RESEARCH_PROGRAM_VALIDATION=FAIL {exc}")
        return 1

    reviews_dir = state_dir / REVIEWS
    if reviews_dir.exists():
        for path in reviews_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() not in {".md", ".json"}:
                raise ProgramError(f"unsupported strategic review artifact: {path}")
    print("RESEARCH_PROGRAM_VALIDATION=PASS")
    return 0


def self_test() -> int:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = parse.urlsplit(self.path)
            body = b"alpha" if not parsed.query else ("query=" + parsed.query).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)

        def do_HEAD(self) -> None:
            self.send_response(200)
            self.end_headers()

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_args: Any) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = Path(tmp)
        program = {
            "program_version": PROGRAM_VERSION,
            "benchmark_id": "test-benchmark",
            "discovery": {
                "surface_map_exhaustive": False,
                "open_world": True,
                "uncertainty_notes": ["initial map is a seed"],
            },
            "surfaces": [
                {
                    "surface_id": "surface-a",
                    "name": "A",
                    "description": "test",
                    "origin": "test",
                    "status": "ACTIVE",
                    "priority": 1,
                    "current_intensity": 2,
                    "coverage_estimate": 0.1,
                    "uncertainty": 0.9,
                    "reasonable_effort_evidence": {},
                    "promising_branches": [],
                    "known_anomalies": [],
                    "related_surfaces": [],
                    "evolutionary_families": ["family-a"],
                    "reopen_triggers": ["new behavior"],
                    "history": [],
                }
            ],
            "evolution_families": [
                {
                    "family_id": "family-a",
                    "surface_id": "surface-a",
                    "name": "query differential",
                    "purpose": "deterministic read-only differential testing",
                    "status": "ACTIVE",
                    "generation": 1,
                    "population_size": 8,
                    "mutation_operators": ["BASELINE", "QUERY_EDGE_VALUES"],
                    "selection_policy": "retain reproducible behavioral differences",
                    "exploration_exploitation_policy": "round-robin",
                    "novelty_requirement": "new response signature",
                    "seed_requests": [
                        {"method": "GET", "path": "/health", "query": {}, "headers": {}},
                        {"method": "GET", "path": "/search", "query": {"q": "alpha"}, "headers": {}},
                    ],
                    "best_candidates": [],
                    "lineage": [],
                    "results_history": [],
                    "coverage_history": [],
                    "information_gain_history": [],
                    "false_positive_history": [],
                    "independent_reproduction_history": [],
                    "reasonable_effort_contribution": {},
                    "last_kilo_review": "test",
                    "next_generation_specification": "continue",
                }
            ],
            "portfolio_policy": {
                "max_generations_per_activation": 4,
                "max_candidates_per_generation": 8,
                "exploration_reserve_fraction": 0.25,
            },
        }
        validate_program(program, "test-benchmark")
        plan = compile_portfolio(program, load_runtime(state_dir))
        assert len(plan) == 2 and plan[0]["family_id"] == "family-a"

        target = f"http://127.0.0.1:{server.server_port}"
        result = execute_generation(
            state_dir,
            target,
            program["evolution_families"][0],
            1,
            8,
        )
        assert result["actual_execution"] is True
        assert result["candidate_count"] > 0

        broken = json.loads(json.dumps(program))
        broken["surfaces"] = []
        try:
            validate_continuity(program, broken)
        except ProgramError:
            pass
        else:
            raise AssertionError("surface deletion was not rejected")

        invalid = json.loads(json.dumps(program))
        invalid["discovery"]["surface_map_exhaustive"] = True
        try:
            validate_program(invalid, "test-benchmark")
        except ProgramError:
            pass
        else:
            raise AssertionError("exhaustive map was not rejected")

        receipt_path = state_dir / RECEIPTS
        append_jsonl(receipt_path, {"generation": 1, "actual_execution": True})
        assert len(read_jsonl(receipt_path)) == 1

    server.shutdown()
    server.server_close()
    print("research program self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("pre-kilo", "post-kilo", "validate", "self-test"))
    parser.add_argument("--mode")
    parser.add_argument("--benchmark-id")
    parser.add_argument("--target", default="http://lab-mutator:3000")
    parser.add_argument("--state-dir", default="state/research")
    parser.add_argument("--snapshot-dir")
    args = parser.parse_args()

    if args.command == "self-test":
        return self_test()
    if not args.mode or not args.benchmark_id:
        raise SystemExit("--mode and --benchmark-id are required")

    state_dir = Path(args.state_dir)
    try:
        if args.command == "validate":
            if not args.mode or not args.benchmark_id:
                raise SystemExit("--mode and --benchmark-id are required")
            validate_state(state_dir, args.benchmark_id, args.mode)
            return 0
        if args.command == "pre-kilo":
            return run_pre_kilo(args.mode, args.benchmark_id, args.target, state_dir)
        if not args.snapshot_dir:
            raise SystemExit("--snapshot-dir is required")
        return post_kilo(args.mode, args.benchmark_id, state_dir, Path(args.snapshot_dir))
    except ProgramError as exc:
        print(f"RESEARCH_PROGRAM_STATUS=FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
