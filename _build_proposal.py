import json, hashlib

SRC = "/workspace/state/research/PROGRAM.json"
OUT = "/workspace/PROGRAM_PROPOSAL.json"

p = json.load(open(SRC, encoding="utf-8"))
assert p.get("program_version") == "1.0.0"
assert p.get("discovery", {}).get("open_world") is True
assert p.get("discovery", {}).get("surface_map_exhaustive") is False

surf_by_id = {s["surface_id"]: s for s in p["surfaces"]}

A31_27 = (
    "A31 (2026-10-05T12:54Z): fresh independent verification - GET /rest/user/security-question "
    "(no param) -> 500/2946 B raw Sequelize WHERE 'WHERE parameter email has invalid undefined value' "
    "plus full Sequelize stack (query-generator.js:1759:35, SecurityAnswer.findAll model.js:1140:47); "
    "byte-stable across two consecutive fresh requests in-session (sha256 0b84d83c08cc... x2); "
    "coverage oracle TRUE (id=27) confirmed on live /api/Challenges/ envelope. Auth surface still "
    "BLOCKED (register 500 wrapped; login 401/26 B identical for every input)."
)
A31_97 = (
    "A31 (2026-10-05T12:54Z): fresh verification - GET /metrics -> 200/26141B "
    "text/plain; version=0.0.4; charset=utf-8 with juiceshop_llm_input_tokens_total, "
    "juiceshop_llm_output_tokens_total, juiceshop_llm_tool_calls_total gauges plus "
    "http_requests_count, juiceshop_challenges_solved/total, process_*, nodejs_*, "
    "juiceshop_version_info=20.2.0; secrets-clean. BASELINE candidate added for handoff "
    "invariant compliance; counter gauges increment across requests so body bytes drift "
    "(26141B this capture) - claim rests on gauge presence and Prometheus text/plain "
    "content-type, not exact bytes. Live solved:true=[27,97]."
)

for fam in p["evolution_families"]:
    s = surf_by_id[fam["surface_id"]]
    if fam["family_id"] == "fam_27_raw_error_discovery":
        s["history"].append(A31_27)
    if fam["family_id"] == "fam_97_metrics_baseline":
        s["history"].append(A31_97)

def cid(path, query):
    req = {"headers": {}, "method": "GET", "path": path, "query": query}
    norm = {"method": "GET", "path": path,
            "query": {k: [str(x) for x in req["query"].get(k)] if isinstance(req["query"].get(k), list)
                      else str(req["query"].get(k, "")) for k in req["query"]},
            "headers": {str(k): str(v) for k, v in req["headers"].items()}}
    return "cand-" + hashlib.sha256(json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()[:20]

def add_baseline(fam, path, response_signature):
    req = {"headers": {}, "method": "GET", "path": path, "query": {}}
    fam["best_candidates"].append({"candidate_id": cid(path, {}),
                                   "parent_candidate_id": None,
                                   "mutation": {"operator": "BASELINE", "mutation": "identity"},
                                   "request": req,
                                   "response_signature": response_signature})
    print("added baseline:", fam["family_id"], "cid", cid(path, {}), path, "| sig:", response_signature[:3])

add_baseline(next(f for f in p["evolution_families"] if f["family_id"] == "fam_97_metrics_baseline"),
             "/metrics", [200, "a7b2798825457da8c187e452a68b2ca5f01ffbb20dd86aad49ed1295879e86a5",
                          "text/plain; version=0.0.4; charset=utf-8", 26141, ""])
add_baseline(next(f for f in p["evolution_families"] if f["family_id"] == "fam_76_security_policy"),
             "/security-policy", [200, "aa97229042ece5a31ad318e31c256a31ad318e31c256a15ec51a5005a5295580af6bcf6bdf36783",
                                  "text/html; charset=utf-8", 9393, ""])

json.dump(p, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("wrote", OUT, "| surfaces:", len(p["surfaces"]), "| families:", len(p["evolution_families"]))
for fid, n in ((f["family_id"], len(f["best_candidates"])) for f in p["evolution_families"]):
    print(" ", fid, "best_candidates:", n)
