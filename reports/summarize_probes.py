#!/usr/bin/env python3
import json, sys

path = sys.argv[1]
log = json.load(open(path))
print("total probes: %d\n" % len(log))

def show(r):
    if "trace" in r:
        return "%s: TRACE=%s" % (r["label"], r["trace"])
    h = r.get("headers", {}) or {}
    ct = h.get("Content-Type", "?")
    return "%s: status=%d len=%d ct=%s body=%s" % (
        r["label"], r.get("status"), r.get("length"),
        ct.split(";")[0][:40], (r.get("body","")[:120] or "").replace("\n"," "))

groups = {
    "BASELINE (F1-F5 re-verify)": ["L0-root","L0-metrics","L0-memories","L0-search-benign","L0-search-taut","L0-secans-get","L0-secans-post-empty","L0-secans-post-qid7","L0-sq-bjoern","L0-sq-bjoern-owasp","L0-sq-nonexistent","L0-sq-empty"],
    "AUTH SURFACE": ["L1-login-empty","L1-login-bjoern-juice","L1-login-bjoern-owasp","L1-login-emmajuice","L1-login-bender","L1-login-nonexistent","L1-login-onlyemail","L1-register-empty","L1-reset-empty","L1-order-history","L1-basket","L1-whoami","L1-2fa-setup"],
    "DIFFERENTIAL METHODS": [l["label"] for l in log if l["label"][:4] in ["L2-PUT","L2-PATCH","L2-DELETE","L2-OPTIONS"]],
    "CONTINUE-CODE": [l["label"] for l in log if l["label"].startswith("L2-continuecode")],
    "WEB3/CAPTCHA/REDIRECT": ["L2-web3-nftUnlocked","L2-captcha-get","L2-redirect","L2-redirect-continue"],
    "SSRF": ["L2-internal-docker","L2-internal-containers"],
}

for gname, labels in groups.items():
    hits = [r for r in log if r["label"] in labels]
    print("=== %s (%d probes) ===" % (gname, len(hits)))
    for r in hits:
        print("  " + show(r))
    print()

print("=== ALL PRObes ===")
for r in log:
    print("  " + show(r))
