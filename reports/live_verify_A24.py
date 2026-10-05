#!/usr/bin/env python3
"""Live verification pass for activation A24 on the current target variant.
Records exact reproducible requests + observations.
"""
import json, hashlib, urllib.request, time, os

TARGET = "http://lab-mutator:3000"
os.environ.setdefault("TZ", "UTC")

def probe(method, path, headers=None, body=None, q=None):
    url = f"{TARGET}{path}"
    if q:
        url += ("&" if "?" in path else "?") + q
    if isinstance(body, str):
        body = body.encode("utf-8")
    req = urllib.request.Request(url, method=method, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        return dict(status=r.status, body=data.decode("utf-8", "replace"),
                    ct=r.headers.get("Content-Type") or "", len=len(data),
                    h=dict(r.headers), resp=None, error=None)
    except urllib.error.HTTPError as e:
        data = e.read()
        return dict(status=e.code, body=data.decode("utf-8", "replace"),
                    ct=e.headers.get("Content-Type") or "", len=len(data),
                    h=dict(e.headers), resp=None, error=str(e.reason))
    except Exception as e:
        return dict(status=None, body="", ct="", len=0, h={}, resp=None,
                    error=f"{type(e).__name__}: {e}")

def rec(tag, result):
    return {"tag": tag, "status": result["status"], "ct": result["ct"],
            "len": result["len"], "hash": hashlib.sha256(result["body"].encode()).hexdigest(),
            "snippet": result["body"][:400], "error": result["error"]}

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
out = []

out.append(rec("T0_root", probe("GET", "/")))

# Pass 0/1: envelope + challenge inventory
out.append(rec("T1_challenges", probe("GET", "/api/Challenges/")))
out.append(rec("T1a_challenges_data", probe("GET", "/api/Challenges/1")))
out.append(rec("T1_metrics", probe("GET", "/metrics")))

# Pass 2/3: known high-value surfaces + differential pairs
out.append(rec("T2_secq_noparam", probe("GET", "/rest/user/security-question")))
out.append(rec("T2_secq_bjoern", probe("GET", "/rest/user/security-question?email=bjoern@owasp.org")))
out.append(rec("T2_secq_nonexistent", probe("GET", "/rest/user/security-question?email=nobody@example.org")))
out.append(rec("T2_secq_dot", probe("GET", "/rest/user/security-question/.")))
out.append(rec("T2_secq_nullq", probe("GET", "/rest/user/security-question?q=")))
out.append(rec("T2_redirect", probe("GET", "/redirect?continue=http://example.com")))
out.append(rec("T2_redirect_dot", probe("GET", "/redirect/.", q="continue=http://example.com")))

# Error triggers on write routes
out.append(rec("T2_fb_textplain", probe("POST", "/api/Feedbacks/",
            headers={"Content-Type": "text/plain; charset=utf-8"},
            body="garbage unparseable")))
out.append(rec("T2_fb_invalidjson", probe("POST", "/api/Feedbacks/",
            headers={"Content-Type": "application/json"},
            body="{not valid json")))
out.append(rec("T2_fb_benign", probe("POST", "/api/Feedbacks/",
            headers={"Content-Type": "application/json"},
            body='{"name":"test","email":"t@t.com","subject":"s","message":"m"}')))
out.append(rec("T2_products_post", probe("POST", "/api/Products/",
            headers={"Content-Type": "application/json"},
            body='{"name":"x"}')))
out.append(rec("T2_products_put", probe("PUT", "/api/Products/1",
            headers={"Content-Type": "application/json"},
            body='{"name":"x"}')))

# Write-gap surfaces
# Write-gap surfaces
out.append(rec("T2_sa_get", probe("GET", "/api/SecurityAnswers/")))
out.append(rec("T2_sa_post_empty", probe("POST", "/api/SecurityAnswers/",
            headers={"Content-Type": "application/json"}, body="{}")))
out.append(rec("T2_sa_post_populated", probe("POST", "/api/SecurityAnswers/",
            headers={"Content-Type": "application/json"},
            body='{"questionId":7,"answer":"test"}')))

# Memor
out.append(rec("T2_memories", probe("GET", "/rest/memories")))
out.append(rec("T2_memories_dot", probe("GET", "/rest/memories/.")))
out.append(rec("T2_memories_id", probe("GET", "/rest/memories/1")))

# Captcha
out.append(rec("T2_captcha", probe("GET", "/rest/captcha")))

# Auth surface
out.append(rec("T2_login", probe("POST", "/rest/user/login",
            headers={"Content-Type": "application/json"},
            body='{"email":"bjoern@owasp.org","password":"test"}')))
out.append(rec("T2_register", probe("POST", "/rest/user/register")))
out.append(rec("T2_whoami", probe("GET", "/rest/user/whoami")))
out.append(rec("T2_admin", probe("GET", "/admin")))

# Static/info probes
out.append(rec("T2_robots", probe("GET", "/robots.txt")))

results = {"generated_at": now, "target": TARGET, "probes": out}
with open("/workspace/reports/live_verify_A24_out.json", "w") as f:
    json.dump(results, f, indent=1)
print(now, "wrote", len(out), "probe results")
for p in out:
    print(f"{p['tag']:18} status={p['status']} len={p['len']:5} hash={p['hash'][:12]}")
