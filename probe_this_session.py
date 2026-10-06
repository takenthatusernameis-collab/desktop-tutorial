#!/usr/bin/env python3
"""Fresh live probe of the lab-mutator:3000 surface. Records status, size, sha256, content-type, body for byte-stability tracking."""
import json, hashlib, time, urllib.request, sys
BASE = "http://lab-mutator:3000"

def make_req(method, path, headers=None, body=None):
    h = dict(headers or {})
    if body and not isinstance(body, bytes):
        h.setdefault("Content-Type", "application/json")
        body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, method=method, data=body, headers=h)
    return req

def probe(method, path, headers=None, body=None, label=""):
    req = make_req(method, path, headers, body)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            code = r.status
            ctype = r.headers.get("Content-Type", "")
            md = hashlib.sha256(data).hexdigest()
            print(f"{label}|{code}|{len(data)}|{md}|{ctype}|{time.time()-t0:.3f}|{path}")
            return data
    except urllib.error.HTTPError as e:
        data = e.read()
        ctype = e.headers.get("Content-Type", "")
        md = hashlib.sha256(data).hexdigest()
        print(f"{label}|{e.code}|{len(data)}|{md}|{ctype}|{time.time()-t0:.3f}|{path}")
        return data

print("## PASS 0: baseline")
probe("GET", "/", label="home")
probe("GET", "/metrics", label="metrics")
r = probe("GET", "/api/Challenges/", label="challenges")
d = json.loads(r)
ids = [c.get("id") for c in d["data"] if c.get("solved")]
print("solved:true ids =", ids)

print("## PASS 1: candidate mechanisms (3x each for byte-stability)")
targets = [
    ("GET", "/rest/user/security-question", {}, "sq_noemail_A"),
    ("GET", "/rest/user/security-question", {"Accept": "application/json"}, "sq_json_A"),
    ("GET", "/rest/user/security-question", {}, "sq_noemail_B"),
    ("GET", "/redirect?continue=http://example.com", {}, "redir_A"),
    ("GET", "/redirect?continue=http://example.com", {}, "redir_B"),
    ("GET", "/rest/captcha", {}, "cap_A"),
    ("GET", "/rest/captcha", {}, "cap_B"),
    ("GET", "/rest/memories", {}, "mem_A"),
    ("GET", "/rest/memories", {}, "mem_B"),
    ("GET", "/rest/memories", {"Authorization": "Bearer invalidtoken"}, "mem_nox_A"),
    ("GET", "/rest/user/security-question", {}, "sq_noemail_C"),
    ("GET", "/redirect?continue=http://example.com", {}, "redir_C"),
]
for m, p, h, l in targets:
    probe(m, p, h, label=l)

print("## PASS 2: null / control routes")
for l in ["n1","n2","n3"]:
    probe("GET", f"/api/Nonexistent/{l}", label=l+"-ctrl")
probe("GET", "/rest/admin", label="ctrl-admin")

print("## PASS 3: security-question enumeration differential (known vs unknown email)")
known = ["bjoern@owasp.org", "emma@juice-sh.op", "nonexistent@x.y.z", "a@b.c"]
for addr in known:
    probe("GET", f"/rest/user/security-question?email={addr}", label=f"sq_email_{addr.replace('@','_')}")
# duplicate param
probe("GET", "/rest/user/security-question?email=bjoern@owasp.org&email=bjoern@owasp.org", label="sq_dupemail")
# edge values
for ev in ["1", "null", "false", "%", ""]:
    probe("GET", f"/rest/user/security-question?email={ev}", label=f"sq_email_{ev.replace('%','pct')}")

print("## PASS 4: challenge filter layer")
for q in ["?key=passwordHashLeakChallenge","?solved=true","?difficulty=1","?category=Injection","?category=Broken%20Authentication","?search=x","?include=details","?limit=3"]:
    probe("GET", "/api/Challenges/"+q, label="ch"+q[:6].replace("=","_"))

print("## PASS 5: write / neighbors")
probe("POST", "/api/SecurityAnswers/", {}, {})
probe("POST", "/api/SecurityAnswers/", {}, {"questionId":7,"answer":"hello"})
probe("OPTIONS", "/api/SecurityAnswers/", {})
probe("GET", "/api/SecurityAnswers/", label="sa_get")
for ep in ["/api/Deliverys","/api/Feedbacks","/api/Hints","/api/Products","/api/Quantitys","/api/SecurityQuestions"]:
    probe("GET", ep, label="api"+ep)
for m,p in [("PUT","/api/Products/1"),("DELETE","/api/Products/1"),("PATCH","/api/Products/1"),("POST","/api/Products/")]:
    probe(m, p, label=m+"prod")
probe("GET", "/rest/user/change-password", label="cpw")
probe("GET", "/rest/user/login", label="login_page")
probe("POST", "/rest/user/login", {}, {"email":"x@y.z","password":"x"})
probe("POST", "/rest/user/register", {}, {"email":"x@y.z","password":"x","confirmPassword":"x"})

print("## PASS 6: method / encoding variants on live routes")
for m,p in [("HEAD","/rest/captcha"),("OPTIONS","/rest/captcha"),("HEAD","/metrics"),("HEAD","/rest/memories")]:
    probe(m, p, label=m+p.replace("/","_"))
probe("GET", "/rest/memories/%2e%2e/", label="mem_enc")
probe("GET", "/rest/user/security-question/./", label="sq_dot")
probe("GET", "/rest/user/security-question?email=bjoern@owasp.org%20", label="sq_trail")
