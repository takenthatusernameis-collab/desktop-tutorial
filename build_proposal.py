import json
from copy import deepcopy

# Load durable state (read-only controller snapshot) and the A27-written program.
program = json.load(open("/workspace/state/research/PROGRAM.json"))
runtime = json.load(open("/workspace/state/research/RUNTIME.json"))

A28 = "2026-10-05T11:02Z"
A28_NOTE = (
    "A28 (2026-10-05T11:00Z): campaign continuation - no DISCOVERY_REQUIRED.json; "
    "solved:[27,97] stable across fresh reads of /api/Challenges/ on the live target; "
    "7 verified findings re-produced fresh this boot with byte-sha256 signatures "
    "(id=27 raw errors, id=97 /metrics, id=23 /rest/memories exposure, "
    "id=24 unauth POST write gap, id=6 PUT mass-assignment, id=7 CAPTCHA answer leak, "
    "id=5 security-question enumeration differential). Deliverable "
    "reports/benchmark_findings.json re-produced at 2026-10-05T11:02Z from live "
    "verification. Surface is flat (144 total candidate probes across 144 generations, "
    "72 behavioral differences, mostly 500-variant noise); auth surface BLOCKED on this "
    "and all prior boots; no new routes beyond the mapped 15 surfaces. Next program: "
    "one generation per non-archived family in breadth-first round-robin, plus a new "
    "HEADER_ORIGIN_VARIANTS differential family."
)

UNIFORM_SPEC = (
    "A28 round-robin pass: one generation per non-archived family on existing seeds "
    "and declared operators, until the candidate budget is reached; for surfaces at "
    "zero behavioral differences retain a minimal coverage sweep because routes are "
    "mutation-fragile and return across boots; no deepening of any branch until a new "
    "solvable hidden behavior emerges."
)

A28_REV = (
    "A28 (2026-10-05T11:02Z): fresh verification of 7 findings on this boot "
    "(solved:[27,97]); deliverable re-produced; carried forward with one generation "
    "per family in breadth-first round-robin plus one HEADER_ORIGIN_VARIANTS "
    "differential family; no new surfaces surfaced."
)

families_by_id = {f["family_id"]: f for f in program["evolution_families"]}

# 1. Advance generation counters to next-to-run (last_executed + 1, authoritative from RUNTIME).
for fid, fam in families_by_id.items():
    fam["generation"] = runtime["families"].get(fid, {}).get("last_executed_generation", 0) + 1
    fam["last_kilo_review"] = A28_REV
    fam["next_generation_specification"] = UNIFORM_SPEC

# 2. Append the A28 observation to program uncertainty notes.
program["discovery"]["uncertainty_notes"].append(A28_NOTE)

# 3. New surface for the untried HEADER_ORIGIN_VARIANTS operator.
new_surface = {
    "surface_id": "surf_origin_header_variants",
    "name": "Header-origin differential (HEADER_ORIGIN_VARIANTS)",
    "description": "Differential testing that varies Origin/Referer/CORS/Access-Control-* header presence and values against the error/redirect surface to test for header-based access differentiation.",
    "origin": "A28: HEADER_ORIGIN_VARIANTS is the only operator in the accepted set never yet executed; added as a single cheap breadth probe on the error surface.",
    "status": "ACTIVE",
    "priority": "LOW",
    "current_intensity": "full",
    "coverage_estimate": "minimal - one untried operator, first generation pending",
    "uncertainty": "header-based gating is unlikely on the Juice Shop error surface; low expected information gain but the operator is unexplored",
    "reasonable_effort_evidence": "HEADER_ORIGIN_VARIANTS sweep pending (gen 1). Baseline GET /rest/user/security-question (no param) -> 500/2946 B raw WHERE, verified 2026-10-05T11:02Z.",
    "promising_branches": [],
    "known_anomalies": [],
    "related_surfaces": ["surf_27_error_handling"],
    "evolutionary_families": ["fam_origin_header_variants"],
    "reopen_triggers": ["variant change", "any error surface returns a differentiated response to Origin/Referer/CORS headers"],
    "history": [
        "A28 (2026-10-05T11:02Z): surface created; HEADER_ORIGIN_VARIANTS is the untried operator in the accepted set - added as a low-cost breadth probe."
    ],
}

new_family = {
    "family_id": "fam_origin_header_variants",
    "surface_id": "surf_origin_header_variants",
    "name": "Header-origin differential sweep",
    "purpose": "Test whether Origin/Referer/CORS/Access-Control-* header presence and values differentiate responses on the error/redirect surface (the only untried operator in the accepted set).",
    "status": "ACTIVE",
    "generation": 1,
    "population_size": 12,
    "mutation_operators": ["BASELINE", "HEADER_ORIGIN_VARIANTS"],
    "selection_policy": "best_response_signature diversity; retain any candidate producing a response distinct from BASELINE",
    "exploration_exploitation_policy": "exploration reserve: HEADER_ORIGIN_VARIANTS is a breadth probe; do not starve other surfaces",
    "novelty_requirement": "new candidate must differ in at least one observed response field (status, body-length, or header) from BASELINE to be retained as best",
    "seed_requests": [
        {"method": "GET", "path": "/rest/user/security-question", "query": {}, "headers": {}}
    ],
    "best_candidates": [],
    "lineage": [],
    "results_history": [],
    "coverage_history": [],
    "information_gain_history": [],
    "false_positive_history": [],
    "independent_reproduction_history": [],
    "reasonable_effort_contribution": "first generation of HEADER_ORIGIN_VARIANTS sweep on the error surface",
    "last_kilo_review": A28_REV,
    "next_generation_specification": UNIFORM_SPEC,
}

program["surfaces"].append(new_surface)
program["evolution_families"].append(new_family)

with open("/workspace/PROGRAM_PROPOSAL.json", "w", encoding="utf-8") as f:
    json.dump(program, f, indent=1, ensure_ascii=False)

# Sanity: re-parse and print summary.
p2 = json.load(open("/workspace/PROGRAM_PROPOSAL.json"))
print("surfaces:", len(p2["surfaces"]), "| families:", len(p2["evolution_families"]))
print("budget:", p2["portfolio_policy"]["max_generations_per_activation"],
      ">= non-archived surfaces:", len([s for s in p2["surfaces"] if s["status"] != "ARCHIVED"]))
ids = [f["family_id"] for f in p2["evolution_families"]]
print("new family present:", "fam_origin_header_variants" in ids)
print("new surface declared families:", [s["evolutionary_families"] for s in p2["surfaces"] if s["surface_id"]=="surf_origin_header_variants"])
