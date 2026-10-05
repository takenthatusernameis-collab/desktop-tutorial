import json
from copy import deepcopy

# Load durable state (READ-ONLY controller snapshot) and current program.
program = json.load(open("/workspace/state/research/PROGRAM.json"))
runtime = json.load(open("/workspace/state/research/RUNTIME.json"))

A33 = "2026-10-05T13:49Z"
A33_NOTE = (
    "A33 (2026-10-05T13:49Z): campaign continuation on fresh target "
    "(target creation ~2026-10-05T13:48:27Z); deliverable-gate recovery: "
    "reports/benchmark_findings.json and PROGRAM_PROPOSAL.json were ABSENT at "
    "activation start (recurring persistence gap) and re-produced fresh this "
    "activation. Coverage oracle regenerated live from /api/Challenges/: "
    "116 families, solved:[27,97] - exactly matching worker-visible "
    "coverage oracle reports/current_challenges.txt. id=27 triggers re-verified "
    "fresh with byte-sha256: GET /rest/user/security-question (no param) -> "
    "500/2946 B raw WHERE + stack (0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b, "
    "byte-stable x2); Accept: application/json -> 500/1804 B raw JSON error "
    "(20eec46aa755..., single-header differential, x2); GET /redirect?continue= "
    "-> 500 TypeError + stack (020023ff4f9a..., x2); baseline graceful wrapper "
    "confirmed (/api/Nonexistent/1 -> 500 'Unexpected path' no stack). id=97 "
    "/metrics -> 200/26.1 kB text/plain with juiceshop_llm_* gauges + "
    "http_requests_count + challenges_solved (counter drift noted). Auth surface "
    "BLOCKED: register -> 500; login -> 401/26 B identical for all inputs; no "
    "credential source. reports/benchmark_findings.json produced fresh with "
    "exactly 2 findings (one per coverage-oracle TRUE entry), contract shape "
    "validated; deliverable gate closed."
)
UNIFORM_SPEC = (
    "A33 round-robin pass: one generation per non-archived family on existing "
    "seeds and declared operators, until the candidate budget is reached; for "
    "surfaces at zero behavioral differences retain a minimal coverage sweep "
    "because routes are mutation-fragile and return across boots; no deepening "
    "of any branch until a new solvable hidden behavior emerges. id=27/id=97 "
    "claims anchored on live-verified behavior with differential/null controls; "
    "submission limited to coverage-oracle TRUE entries."
)
A33_REV = (
    "A33 (2026-10-05T13:49Z): fresh verification of id=27 raw-error triggers "
    "(sha256 0b84d83c/20eec46aa/020023ff) and id=97 /metrics on a fresh target; "
    "coverage oracle re-generated live (solved:[27,97]); deliverables "
    "re-produced (recurring persistence gap). Carried forward with one generation "
    "per family in breadth-first round-robin; no new surfaces surfaced."
)

families_by_id = {f["family_id"]: f for f in program["evolution_families"]}

# 1. Advance generation counters to next-to-run (last_executed + 1, from RUNTIME).
for fid, fam in families_by_id.items():
    next_gen = runtime["families"].get(fid, {}).get("last_executed_generation", 0) + 1
    fam["generation"] = next_gen
    fam["last_kilo_review"] = A33_REV
    fam["next_generation_specification"] = UNIFORM_SPEC

# 2. Append the A33 observation to program uncertainty notes.
program["discovery"]["uncertainty_notes"].append(A33_NOTE)

# 3. Append fresh-verification evidence to the two solvable surface histories
#    (monotonic: only adds; never reduces reasonable_effort_evidence).
for sid in ("surf_27_error_handling", "surf_97_metrics"):
    for s in program["surfaces"]:
        if s.get("surface_id") == sid:
            s["history"].append(
                f"A33 (2026-10-05T13:49Z): fresh target re-verification - "
                f"GET /rest/user/security-question (no param) -> 500/2946 B "
                f"raw Sequelize WHERE + stack (0b84d83c..., byte-stable x2 fresh "
                f"reads); Accept: application/json -> 500/1804 B raw JSON error "
                f"(single-header differential); GET /redirect?continue= -> 500 "
                f"TypeError + stack; baseline graceful wrapper confirmed. "
                f"GET /metrics -> 200/26.1 kB Prometheus telemetry with "
                f"juiceshop_llm_* gauges + http_requests_count + "
                f"challenges_solved (counter drift noted). Coverage oracle "
                f"regenerated live: solved:[27,97] (116 families). Auth surface "
                f"BLOCKED."
            )

with open("/workspace/PROGRAM_PROPOSAL.json", "w", encoding="utf-8") as f:
    json.dump(program, f, indent=1, ensure_ascii=False)

# Sanity: re-parse and print summary.
p2 = json.load(open("/workspace/PROGRAM_PROPOSAL.json"))
n_active = len([s for s in p2["surfaces"] if s["status"] != "ARCHIVED"])
print("surfaces:", len(p2["surfaces"]), "| families:", len(p2["evolution_families"]),
      "| non-archived surfaces:", n_active)
print("budget:", p2["portfolio_policy"]["max_generations_per_activation"],
      ">= non-archived surfaces:", n_active)
ids = [f["family_id"] for f in p2["evolution_families"]]
print("last family gen ->", {fid: families_by_id[fid]["generation"] for fid in ids[:3]}, "...")
print("uncertainty_notes:", len(p2["discovery"]["uncertainty_notes"]), "entries (A33 appended)")
print("seed_requests all safe:", all(
    str(c.get("method","GET")).upper() in ("GET","HEAD","OPTIONS") and c.get("path","").startswith("/")
    for fam in p2["evolution_families"] for c in (fam.get("seed_requests") or [])))
