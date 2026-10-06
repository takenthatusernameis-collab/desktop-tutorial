#!/usr/bin/env python3
"""Produce PROGRAM_PROPOSAL.json for activation A38.

This activation is a verification / handoff pass: no new portfolio generations
were executed. The proposal preserves every surface and family from the
controller's read-only snapshot (state/research/), appends the A38 live
verification evidence to the two verified surfaces, and keeps the portfolio
policy at max_generations_per_activation=24 (breadth invariant: 24 >=
16 non-archived surfaces).

Read-only controller inputs; worker writes only PROGRAM_PROPOSAL.json at
repository root.
"""

import json

PROGRAM = "/workspace/state/research/PROGRAM.json"
EVOLUTION = "/workspace/state/research/EVOLUTION_FAMILIES.json"
RUNTIME = "/workspace/state/research/RUNTIME.json"
OUT = "/workspace/PROGRAM_PROPOSAL.json"

A38 = "2026-10-06T01:06Z"
A38_NOTE = (
    "A38 (2026-10-06T01:06Z): fresh live verification on a target created "
    "2026-10-06T01:05:18Z (within this activation window); solved:[27,97] "
    "confirmed; id=27 triggers reproduced fresh with byte signatures "
    "0b84d83c / 20eec46a / 020023ff (byte-identical to the A21/A29/A33/A35 "
    "captures across 4 prior campaign boots - drift is intermittent, "
    "class-invariant); id=97 /metrics reproduced (juiceshop_llm_* gauges "
    "present both calls, invalid Bearer -> 200); null controls pass; auth "
    "surface still BLOCKED this boot (login/register -> 'Unexpected path' 500, "
    "no credential source); targeted sweep of 35 routes yielded no new hidden "
    "behavior; a deterministic make_deliverables.py gate now emits both "
    "deliverables fresh from the live target at activation end. No new "
    "generations executed this activation; the program portfolio continues as "
    "compiled by the controller."
)

A38_REV = (
    "A38 (2026-10-06T01:06Z): coverage-oracle-gated findings re-verified fresh "
    "this session (id=27 raw-error triggers + Accept differential + redirect "
    "trigger + null controls; id=97 metrics + invalid-bearer null control); "
    "auth surface BLOCKED confirmed on this boot; deterministic deliverable "
    "gate active; no new generations executed."
)

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

program = load(PROGRAM)
evol = load(EVOLUTION)
families = evol["families"] if isinstance(evol, dict) and "families" in evol else evol
runtime = load(RUNTIME)

# Families from EVOLUTION_FAMILIES.json include full executable shape
# (seed_requests, best_candidates, lineage, history) - authoritative for
# the handoff. Align the program's family list with it.
prog_fams = {f["family_id"]: f for f in program["evolution_families"]}
for fam in families:
    fid = fam["family_id"]
    if fid in prog_fams:
        prog_fams[fid].update(fam)
    else:
        program["evolution_families"].append(fam)

fams_by_id = {f["family_id"]: f for f in program["evolution_families"]}

# 1. Update last_kilo_review for every family (A38 verification pass).
for fid, fam in fams_by_id.items():
    fam["last_kilo_review"] = A38_REV

# 2. Append A38 evidence to the two verified surfaces.
for surf in program["surfaces"]:
    if surf["surface_id"] == "surf_27_error_handling":
        surf["history"].append(
            f"{A38} fresh live verification: GET /rest/user/security-question "
            "-> 500/2946 B raw WHERE + full stack (sig 0b84d83c08cc2842...); "
            "Accept: application/json -> 500/1804 B raw JSON error (sig "
            "20eec46aa7555e7d..., single-header differential); "
            "GET /redirect?continue=http://example.com -> 500/2531 B TypeError "
            "+ stack (sig 020023ff4f9ae2b9...); null controls "
            "/api/Nonexistent/1 (500/2436 B) and /rest/admin (500/2422 B) expose "
            "only graceful wrappers. Bytes byte-identical to A21/A29/A33/A35 "
            "captures - intermittent cross-boot drift confirmed, class-invariant."
        )
    elif surf["surface_id"] == "surf_97_metrics":
        surf["history"].append(
            f"{A38} fresh live verification: GET /metrics -> 200/26204 B "
            "text/plain, juiceshop_llm_* counters present (sig "
            "4e382856f379...); second fresh call -> 200/26175 B (sig "
            "961a0af13d77...), counter drift confirms value-level only; "
            "invalid Bearer -> 200/26133 B (no auth gate)."
        )

program["discovery"]["uncertainty_notes"].append(A38_NOTE)

# 3. Program metadata.
program["program_version"] = "1.0.0"
program["benchmark_id"] = runtime.get("benchmark_id",
    program.get("benchmark_id", "ehb-37260280180-eddbb902f2"))
program["author"] = "Kilo research worker (A38)"
program["produced_at"] = A38
program["handoff_type"] = "generation"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(program, f, indent=1, ensure_ascii=False)

# 4. Sanity check breadth invariant.
non_archived = [s for s in program["surfaces"] if s["status"] != "ARCHIVED"]
print("surfaces:", len(program["surfaces"]), "| families:",
      len(program["evolution_families"]),
      "| non-archived surfaces:", len(non_archived),
      "| max_generations:", program["portfolio_policy"]["max_generations_per_activation"],
      ">= non-archived:", len(non_archived))
print("written:", OUT)
