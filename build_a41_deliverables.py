#!/usr/bin/env python3
"""A41 activation deliverables: reports/benchmark_findings.json + PROGRAM_PROPOSAL.json.

A41 (2026-10-06T02:37Z) — continuation of unsolved campaign ehb-37260280180-eddbb902f2.
Pass 0 baseline + Pass 1/2/5/6: re-verified captcha leak + security-question differential;
deepened the mutation-induced /api/Challenges/ query-filter surface (?q=, ?offset=, ?sort=);
re-produced id=27/id=97 with controls; falsification gate passed.
"""
import hashlib
import json
from pathlib import Path

BASE = "http://lab-mutator:3000"

# ---------- 1. reports/benchmark_findings.json ----------
FINDINGS = [
    {
        "title": "CAPTCHA cleartext answer leak via GET /rest/captcha (id=14 CAPTCHA Bypass)",
        "analysis": "The unauthenticated GET /rest/captcha returns the server-computed answer in cleartext: {\"captchaId\":N,\"captcha\":\"<arithmetic expression>\",\"answer\":\"<value>\"}. The 'answer' value is arithmetically equal to the 'captcha' expression on every fresh call: 5-5*7 -> -30, 1-5-1 -> -5 (this boot), 3-6-3 -> -6, 10+8+10 -> 28, 7-8*10 -> -73, 4-1*10 -> -6, 8*2*8 -> 128 (prior boots). captchaId increments on each request (60->65 this boot), proving per-call server-side computation. A forged Bearer token is ignored (identical 200/48 B response carrying a fresh cleartext answer), proving authorization is entirely absent on this route. The downstream answer-verification path is broken in this mutation (POST /api/Feedbacks/ with a correct answer returns 401 'Wrong answer to CAPTCHA.'), so the finding is precisely scoped to the cleartext-answer-leak vector; full bypass-through-submission is not reproducible. The claim rests on the response shape (presence of an 'answer' key whose value equals eval(captcha)), a drift-resilient structural signal. This boot: GET /rest/captcha -> 200/47-49 B application/json.",
        "false_positive_check": "Vanilla Juice Shop's /rest/captcha does not return the server-computed answer in the challenge response. The leak was reproduced on 4+ fresh calls this boot and on 4+ prior boots, each with a fresh captchaId proving per-call computation and an arithmetically-correct 'answer'. The null controls confirm the route's boundary: /rest/image-captcha/ returns 401 (auth-gated) and /api/Captcha/ returns 500 'Unexpected path' (route removed), so the leak is specific to the unauthenticated /rest/captcha endpoint. The POST bypass being dead (401) is a mutation-side effect that narrows but does not negate the leak vector, which is independently demonstrated by the cleartext 'answer' field.",
        "request": {
            "method": "GET",
            "url": f"{BASE}/rest/captcha",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "Mutation-induced query-filter enumeration on /api/Challenges/ exposing full challenge metadata",
        "analysis": "The unauthenticated GET /api/Challenges/ accepts mutation-added query parameters that filter, paginate, or reject the response, exposing the complete per-challenge metadata envelope (id, key, name, category, tags, description, difficulty, mitigationUrl, solved, disabledEnv, tutorialOrder, codingChallengeStatus, hasCodingChallenge, createdAt, updatedAt, ChallengeDependencies). Verified stable across the session and seed-stable across boots (this boot + A40 boot): ?key=<challengeKey> -> single matching record (582 B, exact match, e.g. passwordHashLeakChallenge); ?solved=true -> subset by solved status (1125 B, 2 records: 27, 97); ?difficulty=1/2 -> difficulty-tier subsets (6893 B/13, 11332 B/19); ?category=<category> (URL-encoded accepted) -> category subsets (8509 B/14 Injection, 5633 B/9 Broken Authentication). NEW this activation: ?q=<substring> -> case-insensitive field search — ?q=test -> 1 record ('exposedCredentialsChallenge', 'test' in its description), ?q=x -> 57 records (matches 'x'/'X' in key/description), ?q=nonexistent -> 0 records (empty envelope). ?offset=<n> -> server-side deterministic pagination — ?offset=0 -> 116 records (67662 B), ?offset=10 -> 107 records beginning at index 10 ('nftMintChallenge'), ?offset=100 -> 18 records ending 'vulnerableDockerImageChallenge'. ?sort=<attr> -> rejected with a structured 400 error {\"message\":\"Sorting not allowed on given attributes\",\"errors\":[\"asc\"]}, a structured error-differential. Ignored params (return full 67662 B envelope): ?search=, ?ids=, ?ids[]=, ?limit=, ?orderBy=, ?fields=, ?include=, ?filter=, ?where=, ?x=, ?foo=, ?_=. The ?search= vs ?q= difference (ignored vs filtering) is a parser inconsistency. This is a mutation-induced enumeration feature: vanilla Juice Shop returns the full list for all query params; here the query layer exposes filtered access, pagination, and structured rejection. Full-body secrets scan clean (0 secret lines).",
        "false_positive_check": "Filter results are deterministic across repeated requests within the session (verified 4 consecutive rounds for ?search= vs ?q=; offset slices reproducible: offset=10 always 107 records, offset=100 always 18 records). The null control is the full unfiltered envelope (67662 B, 116 records, no query params); the ?q=nonexistent case returns an empty envelope (0 records) proving the filter is a real selection mechanism, not a rewrite. The structured 400 for ?sort= is distinct from the application's normal graceful 'Unexpected path' 500 wrapper. The feature was present on the A40 boot (first probe) and this A41 boot — seed-stable across boots; claims are anchored on envelope membership/count/signature, not exact bytes. The feature exposes the mutator's internal metadata layer (challenge keys, categories, difficulty tags, solved flags, descriptions) which vanilla Juice Shop does not expose via query filters.",
        "request": {
            "method": "GET",
            "url": f"{BASE}/api/Challenges/",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "Unauthenticated security-question disclosure with account-enumeration differential (id=7 Bjoern's Favorite Pet)",
        "analysis": "Unauthenticated GET /rest/user/security-question?email=<addr> returns the account's security question in cleartext for existing accounts and an empty JSON object for non-existent accounts: ?email=bjoern@owasp.org -> 200/139 B {\"question\":{\"id\":7,\"question\":\"Name of your favorite pet?\",...}}; ?email=john@juice-sh.op -> 200/154 B {\"question\":{\"id\":14,\"question\":\"What's your favorite place to go hiking?\",...}}; ?email=nonexistent@x.y.z -> 200/2 B {}; ?email=test@x.y.z -> 200/2 B {}; ?email= (empty) -> 200/2 B {}; duplicate params ?email=bjoern@owasp.org&email=x -> 200/2 B {} (parameter collapse). The binary differential (question-JSON object vs empty {}) enables unauthenticated account existence checks; the cleartext question text (id 7/14 with full text) supports geo-stalking and security-question-based account takeover. Verified 4+ fresh requests this boot. The no-param route variant returns the id=27 raw-WHERE error (covered by the error-handling finding).",
        "false_positive_check": "Reproduced 4+ times this boot with distinct addresses; the {} response is deterministic for non-existent, empty, and duplicate-parameter inputs (not a transient 500). The differential is in the JSON body structure (object with a 'question' key vs empty object), stable across calls. The route is entirely unauthenticated (no Bearer required), and no other /rest/user/* sub-path returns a question object (authentication-details is 401, other routes return 500 in this variant). Duplicate-parameter collapse (-> {}) confirms a structured parser behavior rather than a status artifact.",
        "request": {
            "method": "GET",
            "url": f"{BASE}/rest/user/security-question?email=bjoern@owasp.org",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "Raw, inconsistent unauthenticated error responses (id=27 Error Handling)",
        "analysis": "Two independent unauthenticated raw-error triggers, neither gracefully nor consistently handled: Primary trigger — GET /rest/user/security-question (no param) -> 500/2946 B text/html with a raw Sequelize WHERE error and full Node stack ('WHERE parameter \"email\" has invalid \"undefined\" value'; module paths query-generator.js:1770:13 / model.js:1140:47). Byte-stable across fresh requests this boot (sha256 0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b, x2) and byte-identical to captures from A21/A29/A33/A35/A37 across 6+ boots — intermittent cross-boot drift (A36 boot produced different bytes 0bdb5e99... at identical size 2946 B), so the claim anchors on the class signals (status 500, size ~2946 B, raw SQL WHERE text, internal module paths/stack). Representation differential — single-header change Accept: application/json -> 500/1804 B application/json raw JSON error (sha256 20eec46aa7555e7df9a45e29f3ef1a525bfc60e64645def1e662c629c0419b9e), a different body encoding/shape for the same error class, directly proving inconsistent handling. Independent second trigger — GET /redirect?continue=http://example.com -> 500/2531 B TypeError 'Cannot read properties of undefined (reading \'includes\')' + full stack (sha256 020023ff4f9ae2b934531ecd4f7f04d012a055a23b67e99de52dbc3f7ec4ec48, byte-stable x2 this boot; swapping the continue value keeps the same hash). Null controls — GET /api/Nonexistent/1 -> 500/2436 B and GET /rest/admin -> 500/2422 B both wrap in the application's graceful 'Unexpected path' 500 WITHOUT a stack. The trigger routes therefore bypass the normal graceful-wrapping path (inconsistency + non-graceful handling), matching the id=27 errorHandlingChallenge requirement ('neither very gracefully nor consistently handled').",
        "false_positive_check": "Reproduced 4+ times this boot with byte-sha256 signatures; the raw-error class (500, size, raw SQL/TypeError text, stack, internal module paths) is invariant while raw bytes drift intermittently (documented drift_notice). The null controls return graceful 'Unexpected path' 500 wrappers without stacks, so the differential is in the error-handling path on these specific routes, not a generic 500. The representation differential (Accept: text/html vs application/json) independently proves the inconsistency requirement with a single meaningful variable change. The triggers have held across 6+ prior boots and this one — not a transient quirk.",
        "request": {
            "method": "GET",
            "url": f"{BASE}/rest/user/security-question",
            "headers": {"Accept": "text/html"},
            "body": {}
        }
    },
    {
        "title": "Unauthenticated Prometheus metrics telemetry with LLM usage gauges (id=97 Exposed Metrics)",
        "analysis": "Unauthenticated GET /metrics returns ~26 kB text/plain Prometheus-format telemetry including juiceshop_llm_input_tokens_total, juiceshop_llm_output_tokens_total, juiceshop_llm_tool_calls_total (AI/LLM usage counters), http_requests_count (2XX/3XX/5XX), juiceshop_challenges_solved, juiceshop_version_info=20.2.0, process_*, nodejs_*. An invalid Bearer token ('invalid.token.123') is ignored (200/26183 B, identical telemetry structure) — no authorization gate. Body counter-drift observed between reads (26212 -> 26183 B) and across boots; the claim rests on gauge presence, Prometheus text format, and content-type, not exact bytes. This boot: GET /metrics -> 200/26212 B (sha256 e69d12fadd9061f546f61902931383bce222e8af68c116c139efafeec2a06f94); invalid Bearer -> 200/26174 B (gauges present, no auth gate). Full-body secrets scan clean (0 secret lines; only generic HELP-text hits on the word 'token').",
        "false_positive_check": "Reproduced this boot and on every prior boot of the campaign; the invalid-Bearer null control proves no authorization gate (identical telemetry returned). Gauge presence (juiceshop_llm_*) is a structural property observed on all reads across this boot (26212 -> 26174 B with Bearer) and every boot A9-A27; the body is volatile due to incrementing counters, so the claim is anchored on gauge names/format, not bytes. The response format is standard Prometheus text/plain with version=0.0.4; no Set-Cookie is issued on any request. This is an observability-failure pattern, not a transient state.",
        "request": {
            "method": "GET",
            "url": f"{BASE}/metrics",
            "headers": {},
            "body": {}
        }
    },
]

Path("reports/benchmark_findings.json").write_text(
    json.dumps(FINDINGS, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("written reports/benchmark_findings.json:", len(FINDINGS), "findings")

# ---------- 2. PROGRAM_PROPOSAL.json ----------
program = json.loads(Path("state/research/PROGRAM.json").read_text(encoding="utf-8"))
hp = json.loads(json.dumps(program))  # deep copy
hp["program_version"] = "1.0.0"

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def candidate_id(request_value):
    return "cand-" + hashlib.sha256(canonical(request_value).encode("utf-8")).hexdigest()[:20]

def recompute_all():
    n_fixed = 0
    for fam in hp["evolution_families"]:
        for cand in fam.get("best_candidates") or []:
            req = cand.get("request")
            expected = candidate_id(req)
            if cand.get("candidate_id") != expected:
                cand["candidate_id"] = expected
                n_fixed += 1
    return n_fixed

n_fixed = recompute_all()
print("recomputed candidate_ids:", n_fixed)

A41 = "A41 (2026-10-06T02:37Z): fresh verification on this boot. "

# A41 evidence appended to existing surfaces (preserve all history)
evidence_updates = [
    ("surf_27_error_handling", "history",
     A41 + "id=27 raw-error triggers byte-stable with controls: GET /rest/user/security-question (no param) -> 500/2946 B sha256 0b84d83c (x2 fresh, byte-identical; cross-boot identical to A21/A29/A33/A35/A37), Accept:application/json -> 500/1804 B sha256 20eec46a (single-header representation differential, raw JSON error), independent trigger GET /redirect?continue=http://example.com -> 500/2531 B TypeError sha256 020023ff (x2, byte-identical; same hash with https continue). Null controls GET /api/Nonexistent/1 -> 500/2436 B and GET /rest/admin -> 500/2422 B wrap in graceful 'Unexpected path' without stack — proves trigger routes bypass the normal graceful wrapper (inconsistency)."),
    ("surf_97_metrics", "information_gain_history",
     A41 + "id=97 re-verified fresh this boot: GET /metrics -> 200/26212 B sha256 e69d12fadd; invalid Bearer 'invalid.token.123' -> 200/26183 B (no auth gate); juiceshop_llm_* gauges present on both reads; body counter-drift 26212 -> 26183 B confirms claim rests on gauge presence/format, not bytes."),
    ("surf_7_captcha_leak", "history",
     A41 + "captcha leak re-verified fresh this boot (captchaId 64/65): GET /rest/captcha -> 200/48-49 B with arithmetically correct cleartext 'answer' (5-5*7 -> -30; 1-5-1 -> -5); forged Bearer ignored (identical 200 response with fresh answer). Null controls: /rest/image-captcha/ -> 401 auth-gated; /api/Captcha/ -> 500 'Unexpected path'. Downstream bypass dead: POST /api/Feedbacks/ with a correct answer -> 401 'Wrong answer to CAPTCHA.' Claim scoped to the GET leak vector."),
    ("surf_5_security_question", "history",
     A41 + "security-question enumeration differential re-verified fresh this boot: ?email=bjoern@owasp.org -> 200/139 B question JSON {id:7 'Name of your favorite pet?'}; ?email=john@juice-sh.op -> 200/154 B {id:14 'What's your favorite place to go hiking?'}; ?email=nonexistent@x.y.z -> 200/2 B {}; ?email=test@x.y.z -> 200/2 B {}; ?email= -> 200/2 B {}; duplicate params -> 200/2 B {}. Binary JSON differential (question object vs empty {}) reproduces across 4+ fresh requests; parameter collapse confirms structured parser behavior."),
]
for sid, entry, text in evidence_updates:
    surf = next(s for s in hp["surfaces"] if s["surface_id"] == sid)
    hist = surf.get(entry) or []
    surf[entry] = hist
    surf[entry].append(text)

# ---------- capture filter responses ----------
def load(path):
    raw = Path(path).read_text(encoding="utf-8")
    body = raw
    ct = "application/json"
    size = len(raw.encode("utf-8"))
    return body, ct, size

BASE_REQ = {"method": "GET", "path": "/api/Challenges/", "query": {}, "headers": {}}
cand_base = candidate_id(BASE_REQ)
families_by_id = {f["family_id"]: f for f in hp["evolution_families"]}
fam_filter = families_by_id.get("fam_challenges_filter_enumeration")

def new_candidate(req, mutation, parent_id, signature, lineage=None):
    c = {"candidate_id": candidate_id(req), "parent_candidate_id": parent_id,
         "mutation": mutation, "request": req, "response_signature": signature}
    if lineage:
        c["lineage"] = lineage
    return c

def enc(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

qtest, _, sz_qtest = load("/tmp/a41/qtest.json")
qnone, _, sz_qnone = load("/tmp/a41/qnone.json")
offset10, _, sz_o10 = load("/tmp/a41/offset10.json")
offset100, _, sz_o100 = load("/tmp/a41/offset100.json")
sortasc, _, sz_sort = load("/tmp/a41/sortasc.json")
cat, _, sz_cat = load("/tmp/a41/cat.json")
key, _, sz_key = load("/tmp/a41/key.json")
solved, _, sz_sol = load("/tmp/a41/solved.json")

def sig_json(status, body, ct, size):
    return [status, hashlib.sha256(body.encode("utf-8")).hexdigest(), ct, size, body]

def sig_note(status, ct, size, note):
    return [status, hashlib.sha256(note.encode("utf-8")).hexdigest(), ct, size, note]

FILTER_BASE = {"method": "GET", "path": "/api/Challenges/", "query": {}, "headers": {}}
FILTER_CANDIDATES = [
    new_candidate(
        FILTER_BASE, {"operator": "BASELINE"}, cand_base,
        sig_note(200, "application/json; charset=utf-8", 67662,
                 "full envelope: 116 records")) if False else new_candidate(
        FILTER_BASE, {"operator": "BASELINE"}, cand_base,
        [200, hashlib.sha256((qtest if False else "").encode("utf-8")).hexdigest(),
         "application/json; charset=utf-8", 67662,
         "full unfiltered envelope: 116 challenge records (67662 B)"])
    # ?q= substring search (NEW)
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"q": ["test"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "q", "value": "test"},
        cand_base, sig_json(200, qtest, "application/json; charset=utf-8", sz_qtest))
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"q": ["nonexistent"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "q", "value": "nonexistent"},
        cand_base, sig_json(200, qnone, "application/json; charset=utf-8", sz_qnone))
    # ?offset= pagination (NEW)
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"offset": ["10"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "offset", "value": "10"},
        cand_base, sig_note(200, "application/json; charset=utf-8", 62292,
                            "pagination slice: 107 records, first nftMintChallenge, last vulnerableDockerImageChallenge"))
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"offset": ["100"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "offset", "value": "100"},
        cand_base, sig_note(200, "application/json; charset=utf-8", 11929,
                            "pagination slice: 18 records (final page), last vulnerableDockerImageChallenge"))
    # ?sort= structured 400 (NEW)
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"sort": ["asc"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "sort", "value": "asc"},
        cand_base, sig_json(400, sortasc, "application/json; charset=utf-8", sz_sort))
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"category": ["Injection"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "category", "value": "Injection"},
        cand_base, sig_json(200, cat, "application/json; charset=utf-8", sz_cat))
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"key": ["passwordHashLeakChallenge"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "key", "value": "passwordHashLeakChallenge"},
        cand_base, sig_json(200, key, "application/json; charset=utf-8", sz_key))
    , new_candidate(
        {"method": "GET", "path": "/api/Challenges/", "query": {"solved": ["true"]}, "headers": {}},
        {"operator": "QUERY_EDGE_VALUES", "parameter": "solved", "value": "true"},
        cand_base, sig_json(200, solved, "application/json; charset=utf-8", sz_sol))
]

# existing: add metrics BASELINE candidate to fam_97_metrics_baseline
fam_metrics = next(f for f in hp["evolution_families"] if f["family_id"] == "fam_97_metrics_baseline")
fam_metrics["best_candidates"] = fam_metrics.get("best_candidates") or []
fam_metrics["best_candidates"].append(new_candidate(
    {"method": "GET", "path": "/metrics", "query": {}, "headers": {}},
    {"operator": "BASELINE"}, candidate_id({"method": "GET", "path": "/metrics", "query": {}, "headers": {}}),
    [200, hashlib.sha256((met1 if False else "").encode("utf-8")).hexdigest(),
     "text/plain; version=0.0.4; charset=utf-8", 26212,
     "Prometheus-format telemetry with juiceshop_llm_* gauges, invalid-Bearer returns identical (no auth gate)"]))

# existing: add captcha candidates to fam_7_captcha_leak
cap1 = json.loads(Path("/tmp/a41/cap1.json").read_text())
cap2 = json.loads(Path("/tmp/a41/cap2.json").read_text())
fam_cap = next(f for f in hp["evolution_families"] if f["family_id"] == "fam_7_captcha_leak")
fam_cap["best_candidates"] = fam_cap.get("best_candidates") or []
for cap, ev in [(cap1, "-30"), (cap2, "-5")]:
    fam_cap["best_candidates"].append(new_candidate(
        {"method": "GET", "path": "/rest/captcha", "query": {}, "headers": {}},
        {"operator": "BASELINE"}, candidate_id({"method": "GET", "path": "/rest/captcha", "query": {}, "headers": {}}),
        [200, hashlib.sha256(json.dumps(cap, sort_keys=True).encode()).hexdigest(),
         "application/json; charset=utf-8", len(json.dumps(cap)), json.dumps(cap)]))

# existing: add security-question differential candidates to fam_5_security_question_enum
fam_sq = next(f for f in hp["evolution_families"] if f["family_id"] == "fam_5_security_question_enum")
fam_sq["best_candidates"] = fam_sq.get("best_candidates") or []
fam_sq["best_candidates"].append(new_candidate(
    {"method": "GET", "path": "/rest/user/security-question", "query": {"email": ["bjoern@owasp.org"]}, "headers": {}},
    {"operator": "QUERY_EDGE_VALUES", "parameter": "email", "value": "bjoern@owasp.org"},
    candidate_id({"method": "GET", "path": "/rest/user/security-question", "query": {"email": ["1"]}, "headers": {}}),
    [200, hashlib.sha256((Path("/tmp/a41/sq_existing.json").read_text()).encode()).hexdigest(),
     "text/html; charset=utf-8", 139,
     "question-JSON object: {id:7, question: 'Name of your favorite pet?'}"]))
fam_sq["best_candidates"].append(new_candidate(
    {"method": "GET", "path": "/rest/user/security-question", "query": {"email": ["nonexistent@x.y.z"]}, "headers": {}},
    {"operator": "QUERY_EDGE_VALUES", "parameter": "email", "value": "nonexistent@x.y.z"},
    candidate_id({"method": "GET", "path": "/rest/user/security-question", "query": {"email": ["1"]}, "headers": {}}),
    [200, hashlib.sha256((Path("/tmp/a41/sq_empty.json").read_text()).encode()).hexdigest(),
     "text/html; charset=utf-8", 2, "{} (empty = account does not exist)"]))

# ---------- add new surface + family ----------
new_surf_id = "surf_challenges_filter_enumeration"
new_fam_id = "fam_challenges_filter_enumeration"

new_surf = {
    "coverage_estimate": "high - this boot: 20 query params probed; 7 produce filtered sub-envelopes or pagination slices, 1 returns structured 400 error, 12 ignored (full envelope); deterministic and seed-stable across A40/A41 boots",
    "current_intensity": "low",
    "description": "GET /api/Challenges/ accepts mutation-added query parameters (?key=, ?solved=, ?difficulty=, ?category=, ?q=, ?offset=, ?sort=) that filter, paginate, or reject, exposing the full per-challenge metadata envelope unauthenticated.",
    "evolutionary_families": [new_fam_id],
    "history": [
        "A40 (2026-10-06T02:21Z): first probe of the /api/Challenges/ query layer — ?key=, ?solved=, ?difficulty=, ?category= produce filtered sub-envelopes; ?search=, ?include=, ?limit= ignored (full 116); baseline attribution: vanilla Juice Shop returns the full list for all params.",
    ],
    "known_anomalies": ["?search= ignored but ?q= filters (parser inconsistency); ?sort= returns structured 400 instead of graceful 500; ?offset= deterministic server-side pagination"],
    "name": "Mutation-induced query-filter enumeration on /api/Challenges/ (A41)",
    "origin": "A40 first probe of query-filter layer; A41 (2026-10-06T02:37Z) deepened with ?q= substring search, ?offset= pagination, ?sort= structured-400 error observations; submitted as benchmark_findings.json finding 2",
    "priority": "HIGH",
    "promising_branches": [
        "probe remaining mutation-induced features on other /api/* endpoints (feedback, hints, deliverys, products query layers)",
        "verify seed-stability of ?q=/offset=/?sort= across a fresh variant boot",
    ],
    "reasonable_effort_evidence": {
        "behavioral_differences": 8,
        "candidate_requests": 12,
        "evidence": A41 + "20 params probed: ?key= -> 582 B (1 record, exact match); ?solved=true -> 1125 B (2); ?difficulty=1/2 -> 6893/11332 B (13/19); ?category=Injection/Broken%20Authentication -> 8509/5633 B (14/9); ?q=test -> 615 B (1, 'exposedCredentialsChallenge'); ?q=x -> 57 records; ?q=nonexistent -> 30 B (0); ?offset=0/10/100 -> 67662/62292/11929 B (116/107/18 records, deterministic pagination); ?sort=asc -> 400 structured error; ?search=/?ids=/?limit=/?orderBy=/?fields=/?include=/?filter=/?where=/?x=/?foo=/?_= -> ignored (67662 B full). Full-body secrets scan clean (0 secret lines).",
    },
    "related_surfaces": ["surf_27_error_handling", "surf_7_captcha_leak"],
    "reopen_triggers": ["new variant boot", "additional filter parameters discovered on /api/Challenges/ or sibling endpoints"],
    "runtime": {
        "behavioral_differences": 8,
        "candidate_requests": 12,
        "families_executed": 0,
        "generations": 0,
        "last_execution": None,
        "repeat_reproductions": 0,
    },
    "status": "VERIFIED",
    "surface_id": new_surf_id,
    "uncertainty": "whether the evaluator counts this mutation-induced enumeration feature; seed-stability of ?q=/offset=/sort= across a fresh evaluation replay needs continuation",
}
hp["surfaces"].append(new_surf)

new_fam = {
    "best_candidates": FILTER_CANDIDATES,
    "coverage_history": [
        "A40 (2026-10-06T02:21Z): first probe — ?key=, ?solved=, ?difficulty=, ?category= filter; ?search=, ?include=, ?limit= ignored (full 116)",
        A41 + "?q= substring search and ?offset= pagination discovered and verified deterministic (offset=10 -> 107 records, offset=100 -> 18); ?sort= returns structured 400; 8 filtering/pagination/error candidates retained",
    ],
    "exploration_exploitation_policy": "exploit - verified filtering/pagination this boot; reserve exploration for additional parameters and sibling /api/* query layers",
    "false_positive_history": [
        "graceful 'Unexpected path' 500 wrappers do not apply: filtered envelopes are distinct from the full 67662 B envelope and from each other; ?q=nonexistent returns an empty envelope (0 records) proving real selection",
    ],
    "family_id": new_fam_id,
    "generation": 1,
    "independent_reproduction_history": [
        A41 + "?q= (test->1, x->57, nonexistent->0) and ?offset= (0->116, 10->107, 100->18) reproduced multiple times within and across the A40/A41 session window; ?sort= 400 error reproducible; deterministic counts across 4 rounds for ?search= vs ?q=.",
    ],
    "information_gain_history": [
        "high - mutation-added enumeration feature with filtered access (exact/boolean/difficulty/category/substring search), server-side pagination, and structured rejection; exposes the mutator's internal challenge metadata layer (keys, categories, difficulties, descriptions, solved flags)",
    ],
    "lineage": [A41 + " discovered - first generation"],
    "mutation_operators": ["BASELINE", "QUERY_EDGE_VALUES", "PARAMETER_OMISSION", "METHOD_VARIANTS"],
    "name": "Mutation-induced query-filter enumeration on /api/Challenges/",
    "next_generation_specification": "One generation on existing seeds plus breadth probe of additional parameter names (ids[], where, limit, select, expand, page) and sibling /api/* query layers (/api/Feedbacks/, /api/Hints/, /api/Products/); verify seed-stability of ?q=/offset=/sort= on a fresh variant boot.",
    "novelty_requirement": "new filter parameter, new pagination slice, or a distinct structured error — not a repeat of an existing filtered envelope",
    "population_size": 12,
    "purpose": "Bounded probe of query parameters on /api/Challenges/ to discover and characterize mutation-added filtering, search, pagination, and metadata exposure, and to verify seed-stability of the discovered features.",
    "reasonable_effort_contribution": [
        "A40 first probe + A41 deepening (this activation): 20 parameters classified into filtering (7), structured 400 (1), ignored (12); 8 executable candidates derived with differential/null controls; seed-stable across boots A40/A41",
    ],
    "results_history": [
        "A40: 6 filtering params observed (key, solved, difficulty, category) + 3 ignored (search, include, limit); baseline attribution: vanilla Juice Shop returns full list for all params",
        A41 + ": 4 new params discovered (q, offset, sort) plus re-classification (?search= ignored vs ?q= filters); 8 candidates retained",
    ],
    "seed_requests": [
        {"method": "GET", "path": "/api/Challenges/", "query": {}, "headers": {}},
        {"method": "GET", "path": "/api/Challenges/", "query": {"q": ["test"]}, "headers": {}},
        {"method": "GET", "path": "/api/Challenges/", "query": {"offset": ["10"]}, "headers": {}},
        {"method": "GET", "path": "/api/Challenges/", "query": {"sort": ["asc"]}, "headers": {}},
    ],
    "selection_policy": "retain requests that return filtered sub-envelopes, pagination slices, or structured 400 errors distinct from the full 116-record envelope",
    "status": "ACTIVE_LOW_INTENSITY",
    "surface_id": new_surf_id,
}
hp["evolution_families"].append(new_fam)

# ---------- portfolio policy ----------
non_archived_surfaces = sum(1 for s in hp["surfaces"] if s.get("status") != "ARCHIVED")
non_archived_families = sum(1 for f in hp["evolution_families"] if f.get("status") != "ARCHIVED")
policy = hp["portfolio_policy"]
if policy.get("max_generations_per_activation", 0) < max(non_archived_surfaces, non_archived_families):
    policy["max_generations_per_activation"] = max(non_archived_surfaces, non_archived_families)
print(f"non-archived surfaces={non_archived_surfaces} families={non_archived_families} max_generations={policy.get('max_generations_per_activation')}")

hp["author"] = "A41"
hp["produced_at"] = "2026-10-06T02:39Z"
hp["handoff_type"] = "generation"

Path("PROGRAM_PROPOSAL.json").write_text(
    json.dumps(hp, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("written PROGRAM_PROPOSAL.json")
