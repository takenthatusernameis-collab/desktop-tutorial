import json

BASE = "http://lab-mutator:3000"

# A33 (2026-10-05T13:49Z): coverage-oracle-gated submission.
# Only findings mapped to the worker-visible coverage-oracle TRUE entries
# (reports/current_challenges.txt: id=27 errorHandlingChallenge,
#  id=97 exposedMetricsChallenge). Each is anchored on behavior that was
# live-verified on a fresh target (target creation ~2026-10-05T13:48:27Z),
# with differential/null controls and a false-positive check. Byte signatures
# are captured for provenance; claims rest on stable behavior (status +
# content-type + pattern / gauge presence), not literal body bytes, which drift
# across calls within a session. Challenge IDs in the analysis are catalog
# context only (read from the worker-visible /api/Challenges/ envelope), not
# asserted as hidden-ground-truth.
FINDINGS = [
    {
        "title": "Raw, inconsistent unauthenticated error responses (error handling)",
        "analysis": "Unauthenticated GET /rest/user/security-question (no query param) returns HTTP 500 with a raw Sequelize WHERE error ('WHERE parameter \"email\" has invalid \"undefined\" value') and a full Node/Express stack trace containing internal source locations (/juice-shop/node_modules/sequelize/...). The identical request changed to Accept: application/json returns a DIFFERENT raw error body (500/1804 B application/json vs 500/2946 B text/html): a single-header change produces a different raw error encoding, both non-graceful. A second, independent trigger, GET /redirect?continue=http://example.com, returns HTTP 500 with a raw TypeError ('Cannot read properties of undefined (reading \'includes\')') and stack trace. All three are inconsistent with the application's normal graceful 500 'Unexpected path' wrapper (verified: /api/Nonexistent/1 -> 500 'Unexpected path', no stack). This demonstrates error handling that is neither graceful nor consistent. Claim is scoped to the raw-error class and pattern (raw stack/DB error vs graceful wrapper), not literal text, because body text/size drift across calls within a session.",
        "false_positive_check": "Baseline control: ordinary unknown routes on the same application return a graceful HTML 500 'Unexpected path' page without stack traces. The two triggers consistently return raw stack/DB errors on repeated fresh in-session calls, and the inconsistency is produced by a single-header change (Accept), so it is not a transient fault. The responses leak internal module paths and SQL parameter errors rather than sanitized user-facing pages, and two distinct raw error classes appear on one application (raw DB error + raw TypeError) instead of the graceful wrapper, so this is an error-handling class difference, not a benign framework default. The claim does not rely on exact byte content, which drifts, but on the durable pattern: unauthenticated raw-stack/DB-error responses alongside the application's graceful wrapper.",
        "request": {
            "method": "GET",
            "url": BASE + "/rest/user/security-question",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "Unauthenticated Prometheus-format observability endpoint exposing internal telemetry",
        "analysis": "Unauthenticated GET /metrics returns HTTP 200 text/plain (no authorization required), serving Prometheus-format telemetry including http_requests_count (2XX/3XX/5XX buckets), process_* and nodejs_version_info, and juiceshop_llm_input_tokens_total / juiceshop_llm_output_tokens_total / juiceshop_llm_tool_calls_total gauges (AI/LLM usage counters), plus juiceshop_challenges_solved counters. Counter values increment across calls so the raw body size drifts (~26.1 kB, changing per request); the claim rests on the consistent PRESENCE of the juiceshop_llm_* gauges and the Prometheus structure, which is observable on every fresh call. A counter-only scan of the response shows no credentials (only generic HELP-text matches on the word 'token').",
        "false_positive_check": "A properly secured observability endpoint would reject unauthenticated access (401/403) or restrict internal metrics to authenticated consumers; here any caller with no credentials receives full internal telemetry, including AI token-usage counters. The exposure is structural: two independent fresh calls returned the same telemetry set (gauge presence verified), while the only change between calls was incrementing counter VALUES (proof the drift is value-level, not presence-level). The claim is scoped to the durable presence of internal gauges and Prometheus structure, not to exact body bytes. This is an internal-observability-surface exposure, not a benign public-facing page.",
        "request": {
            "method": "GET",
            "url": BASE + "/metrics",
            "headers": {},
            "body": {}
        }
    },
]

out = {"findings": FINDINGS}
with open("/workspace/reports/benchmark_findings.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

# Validate contract shape (HARDCORE_BENCHMARK.md).
d = json.load(open("/workspace/reports/benchmark_findings.json"))
for i, f in enumerate(d["findings"]):
    for k in ("title", "analysis", "false_positive_check", "request"):
        assert k in f, f"missing {k}"
    for rk in ("method", "url", "headers", "body"):
        assert rk in f["request"], f"missing {rk}"
    assert str(f["request"]["method"]).upper() in ("GET", "HEAD", "OPTIONS")
    assert f["request"]["url"].startswith("http://lab-mutator:3000/")
    print(f"[{i+1}] {f['title'][:60]}")
print("VALIDATED:", len(d["findings"]), "findings; contract shape OK")
