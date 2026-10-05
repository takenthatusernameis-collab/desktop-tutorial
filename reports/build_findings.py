#!/usr/bin/env python3
"""Build reports/benchmark_findings.json from verified evidence (per HARDCORE_BENCHMARK.md contract)."""
import json

F = json.load(open("/workspace/reports/final_verify.json"))
TS = F["timestamp"]
T = F["target"]

F = json.load(open("/workspace/reports/final_verify.json"))
TS = F["timestamp"]
T = F["target"]

f1 = F["f1"]
f2 = F["f2"]
f3 = F["f3"]

findings = [
    {
        "title": "Unauthenticated GET /rest/memories exposes all user accounts with password hashes, deluxe tokens and TOTP secrets",
        "analysis": "Observation (" + TS + "): GET " + T + "/rest/memories with no Authorization header returns HTTP 200 (application/json; charset=utf-8, " + str(f1['length']) + " bytes) and embeds the full user object for each of the " + str(f1['user_count']) + " memory records. Each embedded user object contains fields never exposed by the public UI: " + ", ".join(f1['user_fields']) + ". Example record: email=" + f1['sample']['email'] + ", password=" + f1['sample']['password'][:32] + "..., role=" + f1['sample']['role'] + ", deluxeToken=" + f1['sample']['deluxeToken'][:16] + "... Reasoning: a bogus Authorization: Bearer header changes nothing (response identical), so the endpoint performs no authorization at all; it returns every user's record unauthenticated. Impact: Sensitive Data Exposure (OWASP ASVS L1-L2 excessive data exposure; maps to the app's own Password Hash Leak challenge family, id=1). An unauthenticated actor can enumerate all registered email addresses and harvest credential-bearing data (password hashes and deluxe session tokens) for offline analysis and session hijacking. The delivery of the complete catalog via SQL injection (below) further confirms the endpoint returns every row.",
        "false_positive_check": "1) Control comparison: /rest/wallet/balance, /rest/basket, /rest/user/authentication-details and /api/SecurityAnswers/ all return HTTP 401 without an Authorization header, proving the application's authorization mechanism works elsewhere and the leak is route-specific, not a global misconfiguration. 2) The embedded objects contain non-public fields (password, deluxeToken, totpSecret) that no legitimate public memory listing would return. 3) Response is stable across independent fresh requests; the same user record was captured repeatedly (same email + 32-hex password + token + role). 4) Query parameters (orderBy/limit/skip/where) on /rest/memories are ignored by this endpoint's own logic and do not restrict the returned users, ruling out a pagination-only misconfiguration.",
        "request": {
            "method": "GET",
            "url": T + "/rest/memories",
            "headers": {},
            "body": None
        }
    },
    {
        "title": "Unauthenticated POST /api/SecurityAnswers/ persists records (missing authentication on write endpoint)",
        "analysis": "Observation (" + TS + "): GET " + T + "/api/SecurityAnswers/ (no Authorization header) -> HTTP " + str(f2['get_status']) + ", so the read path is authorized. POST /api/SecurityAnswers/ with Content-Type application/json, body {\"questionId\":7,\"answer\":\"verify-new\",\"email\":\"verify@repro.test\"} and NO Authorization header -> HTTP " + str(f2['post1_status']) + " with a persisted record (id=" + str(f2['post1_id']) + "). A repeat POST of the identical payload -> HTTP " + str(f2['post2_status']) + " with a NEW record (id=" + str(f2['post2_id']) + "), proving server-side persistence without ownership or deduplication checks. An empty-object POST -> HTTP " + str(f2['empty_post_status']) + " with no input validation. Reasoning: the mutation selectively removed server-side authorization from writes on this endpoint while the read path and neighboring writes remain gated. Impact: Broken Access Control / Missing Authentication on write. An unauthenticated actor can create arbitrary security-answer records in this store, which could pollute security-question data or abuse account-recovery flows wired to this store. Note: answers are hashed server-side (64-hex), so the payload's plaintext is not preserved; the unauthorized write itself is the verified property.",
        "false_positive_check": "1) The identical route requires auth for GET (" + str(f2['get_status']) + "), so this is not a public diagnostic endpoint; the gap is write-specific (read-gated, write-open). 2) A repeat POST of the identical payload created a new row (id " + str(f2['post1_id']) + " -> " + str(f2['post2_id']) + "), proving server-side persistence without ownership checks. 3) Empty-object POST -> " + str(f2['empty_post_status']) + " success, proving no input validation gates the write. 4) Neighboring POST endpoints (Complaints, Cards, Addresses, Feedbacks) correctly return 401 or require auth/captcha, so the behavior is endpoint-specific rather than a global server misconfiguration.",
        "request": {
            "method": "POST",
            "url": T + "/api/SecurityAnswers/",
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": {"questionId": 7, "answer": "verify-new", "email": "verify@repro.test"}
        }
    },
    {
        "title": "SQL injection in GET /rest/products/search?q= bypasses the product filter, disclosing the complete product catalog",
        "analysis": "Observation (" + TS + "): GET " + T + "/rest/products/search?q=Apple -> HTTP " + str(f3['filtered_status']) + ", " + str(f3['filtered_len']) + " bytes, " + str(len(f3['filtered_ids'])) + " products (filtered subset). GET " + T + "/rest/products/search?q=%27%20OR%20%271%27=%271 -> HTTP " + str(f3['tautology_status']) + ", " + str(f3['tautology_len']) + " bytes, " + str(len(f3['tautology_ids'])) + " products (the complete catalog). The injected tautology string '%27%20OR%20%271%27=%271' (i.e., ' OR '1'='1) occurs in zero product catalog names (" + str(f3['payload_in_catalog_names']) + "), yet the response returns the entire product set, so benign string filtering cannot explain it. Malformed payloads (e.g., ?q=%27%20UNION%20SELECT%201,2,3--) -> HTTP " + str(f3['malformed_status']) + " with raw SQLite errors, proving raw input reaches a SQLite query layer rather than a client-side filter. DROP TABLE probe -> HTTP " + str(f3['drop_status']) + " with the products table intact, corroborating that the SQL is executed against real tables. The deduced query structure is a LIKE filter concatenating the raw q value (WHERE name LIKE '%' || <q> || '%'). Impact: Injection (filter bypass). An unauthenticated actor can disclose the full product dataset beyond any intended search scope. Explicit limitation: a boolean TRUE/FALSE data-extraction channel could not be reproducibly established because the trailing '|| %' interacts with SQLite operator precedence \u2014 an OR-branch tautology always evaluates all-rows and an AND-branch contradiction always evaluates zero-rows regardless of the inner condition \u2014 so no column-level extraction (users/passwords) via this parameter is claimed.",
        "false_positive_check": "1) Malformed payloads elicit raw 'SQLITE_ERROR' messages ('unrecognized token', 'near UNION'), proving raw input reaches a SQLite query layer. 2) The injected tautology payload occurs in 0 of " + str(len(f3['tautology_ids'])) + " product names, yet returns the full catalog; a benign filter cannot produce this. 3) Behavior is stable across independent fresh requests. 4) The finding is scoped strictly to filter bypass and full-catalog disclosure; data extraction via this parameter is explicitly unclaimed because the extraction channel was not reproducible. 5) Query parameters orderBy/limit/skip/where are ignored by this endpoint's own logic (all return the full catalog), consistent with the q value being the sole (and unsafely concatenated) filter.",
        "request": {
            "method": "GET",
            "url": T + "/rest/products/search?q=%27%20OR%20%271%27=%271",
            "headers": {},
            "body": None
        }
    },
    {
        "title": "Unauthenticated GET /metrics exposes mutation-introduced operational telemetry (Prometheus endpoint not present in pinned v20.2.0 baseline)",
        "analysis": "Observation (" + TS + "): GET " + T + "/metrics with no Authorization header returns HTTP 200 with Content-Type 'text/plain; version=0.0.4; charset=utf-8' (~26 kB). Output includes Prometheus-format counters (juiceshop_llm_input_tokens_total, output_tokens, llm_tool_calls_total), http_requests_count by status_code, and juiceshop_startup_duration_seconds gauges, plus standard process/CPU metrics. The pinned v20.2.0 base image serves no /metrics endpoint, so this is a mutation-introduced observability surface. Reasoning: the endpoint is accessible with zero authorization, exposing internal operational telemetry (request counts by status, startup timing, and LLM usage counters) to any unauthenticated actor. Impact: Observability Failure (maps to the app's own Exposed Metrics challenge family, id=97). Scanning all metric lines for secret/password/token/key/credential/x-api patterns found no emitted secrets or credentials; the exposure is limited to operational telemetry. Behavior is stable across independent fresh requests with byte-identical output.",
        "false_positive_check": "1) The pinned v20.2.0 base image (bkimminich/juice-shop@sha256:8739101ade29358abb5469ee66ae78e582c97ed0a5543a4ad102e5fa5193526b) serves no /metrics endpoint, so this is a mutation-introduced route rather than baseline behavior. 2) Authorization: the endpoint returns 200 with no Authorization header while auth-gated routes (e.g., /rest/basket, /rest/user/authentication-details) correctly return 401, proving the app's auth mechanism works elsewhere and exposure is route-specific. 3) Output was scanned for secret/password/token/key/credential/api_key/bearer/x-api patterns; only HELP text lines match the generic word 'token', with no emitted secrets. 4) Response is stable across independent fresh requests (byte-identical), ruling out a transient or one-off leak.",
        "request": {
            "method": "GET",
            "url": T + "/metrics",
            "headers": {},
            "body": None
        }
    }
]

output = {"findings": findings}
json.dump(output, open("/workspace/reports/benchmark_findings.json", "w"), ensure_ascii=False, indent=1)
print("wrote /workspace/reports/benchmark_findings.json with", len(findings), "findings")
