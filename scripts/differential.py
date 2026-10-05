#!/usr/bin/env python3
"""Pass 2-3: hypothesis-driven differential testing against the benchmark target.
Controlled request pairs; one variable changed at a time.
"""
import re, json, sys, urllib.request, urllib.error, time

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/differential.json"

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
    """cases: list of (name, (status, headers, body))."""
    out = {"label": label, "cases": []}
    for name, (st, h, b) in cases:
        out["cases"].append({
            "name": name,
            "status": st,
            "content_type": h.get("Content-Type", ""),
            "cors": h.get("Access-Control-Allow-Origin", ""),
            "body": b[:500].replace("\n", " "),
            "body_length": len(b)
        })
    return out

results = []

# F1: /rest/captcha — does it leak the answer? differential: correct vs wrong on same captchaId.
cases = []
status, h, b = req("/rest/captcha")
j = json.loads(b)
cid = j["captchaId"]; expr = j["captcha"]; ans = j["answer"]
cases.append(("GET /rest/captcha (baseline)", (status, h, b)))
cases.append(("POST /api/Feedbacks/ wrong answer on same captchaId",
              req("/api/Feedbacks/", "POST",
                  {"Content-Type": "application/json"},
                  json.dumps({"captchaId": cid, "captcha": expr, "answer": "999"}))))
cases.append(("POST /api/Feedbacks/ leaked answer on same captchaId",
              req("/api/Feedbacks/", "POST",
                  {"Content-Type": "application/json"},
                  json.dumps({"captchaId": cid, "captcha": expr, "answer": ans}))))
# also try without captcha fields
cases.append(("POST /api/Feedbacks/ no captcha fields",
              req("/api/Feedbacks/", "POST",
                  {"Content-Type": "application/json"},
                  json.dumps({"message": "hello", "email": "a@b.com"}))))
results.append(dump("captcha_answer_leak_vs_wrong_vs_none", cases))

# F2: /rest/memories — public data exposure; compare with an auth-gated control.
memories = req("/rest/memories")
controls = [
    ("/rest/wallet/balance", req),
    ("/rest/user/whoami", req),
    ("/rest/user/authentication-details", req),
    ("/rest/basket", req),
]
cases = [("GET /rest/memories", memories)] + [(p, req(p)) for p, f in controls]
results.append(dump("memories_public_vs_auth_gated_controls", cases))

# F3: /api/Challenges/ ?key= — test mutation-specific keys mentioned in bundle.
cases = []
base = req("/api/Challenges/")
cases.append(("GET /api/Challenges/ (baseline)", base))
for key in ["nftMintChallenge", "nftChallenge", "captcha", "9", "14"]:
    cases.append((f"GET /api/Challenges/?key={key}", req(f"/api/Challenges/?key={key}")))
results.append(dump("challenges_key_parameter", cases))

# F4: /rest/products/search?q= — parameter mutations.
cases = []
cases.append(("GET /rest/products/search", req("/rest/products/search")))
cases.append(("GET /rest/products/search?q=Apple", req("/rest/products/search?q=Apple")))
cases.append(("GET /rest/products/search?q=", req("/rest/products/search?q=")))
cases.append(("GET /rest/products/search?q=test", req("/rest/products/search?q=test")))
for q in ["' OR '1'='1", "1' OR '1'='1'--", "; DROP", "<script>", "%27", "apple%00", "test?q="]:
    cases.append((f"GET /rest/products/search?q={q}", req(f"/rest/products/search?q={q}")))
results.append(dump("products_search_param_mutation", cases))

# F5: /rest/continue-code-findIt and /rest/continue-code-fixIt — query/apply variants.
cases = [("GET /rest/continue-code-findIt", req("/rest/continue-code-findIt")),
         ("GET /rest/continue-code-fixIt", req("/rest/continue-code-fixIt")),
         ("GET /rest/continue-code-findIt?apply", req("/rest/continue-code-findIt?apply")),
         ("GET /rest/continue-code-fixIt?apply", req("/rest/continue-code-fixIt?apply")),
         ("GET /rest/continue-code-findIt?continueCode=123", req("/rest/continue-code-findIt?continueCode=123")),
         ("GET /rest/continue-code-fixIt?continueCode=123", req("/rest/continue-code-fixIt?continueCode=123"))]
results.append(dump("continue_code_variants", cases))

# F6: /rest/deluxe-membership — 400 body.
cases = [("GET /rest/deluxe-membership", req("/rest/deluxe-membership")),
         ("POST /rest/deluxe-membership no data", req("/rest/deluxe-membership", "POST", {}, "")),
         ("POST /rest/deluxe-membership paymentMode=credit", req("/rest/deluxe-membership", "POST",
                  {"Content-Type": "application/json"}, json.dumps({"paymentMode": "credit"})))]
results.append(dump("deluxe_membership", cases))

# F7: /rest/languages, /rest/repeat-notification, /rest/country-mapping bodies.
cases = [("GET /rest/languages", req("/rest/languages")),
         ("GET /rest/repeat-notification", req("/rest/repeat-notification")),
         ("GET /rest/country-mapping", req("/rest/country-mapping")),
         ("OPTIONS /rest/repeat-notification", req("/rest/repeat-notification", "OPTIONS"))]
results.append(dump("languages_repeat_country", cases))

# F8: /rest/chat — test POST variant.
cases = [("GET /rest/chat", req("/rest/chat")),
         ("POST /rest/chat", req("/rest/chat", "POST",
                  {"Content-Type": "application/json"}, json.dumps({"message": "hi"}))),
         ("GET /rest/chat?msg=test", req("/rest/chat?msg=test"))]
results.append(dump("chat_routes", cases))

# F9: CORS on a public route vs a 401-gated route.
cases = [("GET /rest/memories CORS", req("/rest/memories")),
         ("OPTIONS /rest/memories", req("/rest/memories", "OPTIONS")),
         ("OPTIONS /api/Feedbacks/", req("/api/Feedbacks/", "OPTIONS"))]
results.append(dump("cors_wildcard", cases))

with open(OUT, "w") as f:
    json.dump(results, f, indent=1)
print(f"Wrote {OUT}: {len(results)} tests", file=sys.stderr)
