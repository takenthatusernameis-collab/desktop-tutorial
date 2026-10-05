#!/usr/bin/env python3
"""
Produce reports/benchmark_findings.json from independently-reproduced evidence.
Follows the worker-visible contract in HARDCORE_BENCHMARK.md.
"""
import json

with open("reports/reproduction.json") as f:
    repro = json.load(f)
controls = repro["controls"]

BASE = "http://lab-mutator:3000"
MEM = repro["verified"][0]
SA = repro["verified"][1]
SQL = repro["verified"][2]

findings = []

# ---------- BHB-001 ----------
findings.append({
    "id": "BHB-001",
    "title": "Unauthenticated /rest/memories exposes all user accounts with password hashes, deluxe tokens and TOTP secrets",
    "analysis": "Observation: GET http://lab-mutator:3000/rest/memories (no Authorization header) -> HTTP 200, ~6.1 KB. Every memory record embeds the full user object for that record, including fields not exposed anywhere in the public UI: email, username, password (32-hex), role, deluxeToken, lastLoginIp, profileImage, totpSecret, isActive, and audit timestamps. Reasoning: a separate, bogus Authorization header changes nothing (still 200), so the endpoint performs no authorization at all; it returns all user records unauthenticated. The exposed password values are 32-hex SHA-1-style hashes, deluxeToken values are reusable session tokens, and totpSecret values allow TOTP-based account takeover of the listed accounts. Impact: Sensitive Data Exposure. An unauthenticated actor can enumerate every registered email address and harvest credential-bearing data offline, matching the application's own 'Password Hash Leak' challenge family (id=1). This is a broad data-exposure finding, not an account-takeover claim.",
    "false_positive_check": "1) Control comparison: /rest/wallet/balance, /rest/user/authentication-details, /rest/basket and /api/SecurityAnswers/ all return HTTP 401 without an Authorization header, proving the application's authorization mechanism works elsewhere and the leak is route-specific. 2) The embedded objects contain non-public fields (password, deluxeToken, totpSecret) that no legitimate public listing would return. 3) The response is stable across independent fresh requests; the same user record (email + 32-hex password + token + totpSecret) was captured repeatedly.",
    "request": {
        "method": "GET",
        "url": BASE + "/rest/memories",
        "headers": {},
        "body": None
    },
    "status": "verified",
    "severity": "High",
    "category": "Sensitive Data Exposure",
    "evidence": {
        "sample_user_fields": MEM.get("sample_user_fields"),
        "sample_email": MEM.get("sample_user_email"),
        "password_hash": MEM.get("sample_password_hash"),
        "deluxe_token": MEM.get("sample_deluxe_token"),
        "totp_secret": MEM.get("sample_totp_secret"),
        "role": MEM.get("sample_role"),
        "controls": {k: {"status": v["status"]} for k, v in controls.items()}
    }
})

# ---------- BHB-002 ----------
findings.append({
    "id": "BHB-002",
    "title": "Unauthenticated POST /api/SecurityAnswers/ persists records (missing authentication on write endpoint)",
    "analysis": "Observation: GET http://lab-mutator:3000/api/SecurityAnswers/ (no auth) -> HTTP 401 'No Authorization header was found', so the read path is authorized. POST http://lab-mutator:3000/api/SecurityAnswers/ with Content-Type application/json, body {\"questionId\":7,\"answer\":\"answer-alpha\",\"email\":\"repro@example.com\"}, and NO Authorization header -> HTTP 201 'success' with a persisted record (id:38). A repeat POST of the identical payload -> HTTP 201 with a NEW record (id:39), proving server-side persistence without any ownership or input-validation checks: an empty-object POST also -> 201, and a POST with only an answer field -> 201 with the answer hashed to 64-hex server-side. Reasoning: the mutation selectively removed server-side authorization from writes on this endpoint while the read path and neighboring writes remain gated. Impact: Broken Access Control / Missing Authentication. An unauthenticated actor can create arbitrary security-answer records, which could be used to pollute security-question data or abuse account-recovery flows if those flows are wired to this store. Note: the answer is hashed server-side, so the payload's plaintext is not preserved, but the unauthorized write itself is the property.",
    "false_positive_check": "1) The identical route requires auth for GET (401), so this is not a public diagnostic endpoint; the gap is write-specific (read-gated, write-open). 2) A repeat POST of the identical payload created a new row (id 38 -> 39), proving server-side persistence without ownership checks. 3) POST with no body ({}) -> 201 and POST with missing fields -> 201, proving no input validation gates the write. 4) Neighboring POST endpoints (Complaints, Cards, Addresss, deluxe-membership, Feedbacks) correctly return 401 or require auth/captcha, so the behavior is endpoint-specific rather than a global server misconfiguration.",
    "request": {
        "method": "POST",
        "url": BASE + "/api/SecurityAnswers/",
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": {"questionId": 7, "answer": "answer-alpha", "email": "repro@example.com"}
    },
    "status": "verified",
    "severity": "High",
    "category": "Broken Access Control",
    "evidence": {
        "get_status": controls["/api/SecurityAnswers/"]["status"],
        "post_id_a": SA["post_response_a"]["status"],
        "post_id_repeat": SA["reproductions"][0]["note"] if SA["reproductions"] else None,
        "empty_post": SA["reproductions"][1]["note"] if len(SA["reproductions"]) > 1 else None
    }
})

# ---------- BHB-003 ----------
findings.append({
    "id": "BHB-003",
    "title": "SQL injection in GET /rest/products/search?q= bypasses the product filter, disclosing the complete dataset",
    "analysis": "Observation: GET http://lab-mutator:3000/rest/products/search?q=Apple -> HTTP 200, 921 bytes (filtered subset). GET http://lab-mutator:3000/rest/products/search?q=%27%20OR%20%271%27=%271 -> HTTP 200, 16563 bytes (the complete catalog). GET with malformed payloads -> 500 with raw SQLite errors ('near UNION: syntax error', 'unrecognized token', 'incomplete input'). Reasoning: the q parameter is concatenated into a SQL filter without safe parameterization; deduced query structure is WHERE name LIKE '%' || <q> || '%'. The injected string (a space-and-quote-only tautology) occurs in zero product names, yet the response returns the entire product set, so benign filtering cannot explain it. Impact: Injection (filter bypass). An unauthenticated actor can disclose the full product dataset and enumerate products beyond any intended search scope. Limitation: a boolean TRUE/FALSE extraction channel could not be reproduced because the trailing '|| %' interacts with SQLite operator precedence — an OR-branch condition always evaluates all-rows and an AND-branch condition always evaluates zero-rows regardless of the inner condition — so no user or password extraction via this parameter is claimed.",
    "false_positive_check": "1) Malformed payloads elicit raw 'SQLITE_ERROR' messages ('unrecognized token', 'near UNION'), proving raw input reaches a SQLite query layer rather than a client-side filter. 2) The injected payload text appears in no product catalog entry, yet returns the full catalog; a benign string filter cannot produce this. 3) Behavior is stable across independent fresh requests. 4) The finding is scoped strictly to filter bypass; data extraction (exfiltrating user/password columns) is explicitly unclaimed because the extraction channel was not reproducible.",
    "request": {
        "method": "GET",
        "url": BASE + "/rest/products/search?q=%27%20OR%20%271%27=%271",
        "headers": {},
        "body": None
    },
    "status": "verified",
    "severity": "Medium",
    "category": "Injection",
    "evidence": {
        "sql_evidence": SQL.get("sql_evidence"),
        "deduced_query": SQL.get("deduced_query_structure"),
        "literal_match_note": SQL.get("reproductions", [{}])[0].get("note") if SQL.get("reproductions") else None
    }
})

out = {"findings": findings}
with open("reports/benchmark_findings.json", "w") as f:
    json.dump(out, f, indent=2)

# Also update reports/reproduction.json to embed final findings status markers
with open("reports/benchmark_findings.json") as f:
    final = json.load(f)
repro["final_findings"] = final
with open("reports/reproduction.json", "w") as f:
    json.dump(repro, f, indent=2)

print("Wrote reports/benchmark_findings.json:", len(findings), "findings")
for f_ in findings:
    print(f"  {f_['id']}  {f_['status']}  {f_['severity']}  {f_['category']}")
