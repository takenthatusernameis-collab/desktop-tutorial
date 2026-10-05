#!/usr/bin/env python3
"""Print bodies of key probes with labels, for evidence capture."""
import json, sys

path = sys.argv[1]
log = json.load(open(path))

want = ["L0-memories","L0-search-benign","L0-search-taut","L0-secans-post-empty","L0-secans-post-qid7",
        "L0-sq-bjoern","L0-sq-bjoern-owasp","L0-whoami","L1-login-bjoern-juice","L1-login-nonexistent",
        "L1-order-history","L1-basket","L1-2fa-setup","L1-register-empty","L1-reset-empty",
        "L0-secans-get","L1-login-empty","L0-metrics","L2-redirect","L0-root","L2-continuecode-get","L2-web3-nftUnlocked","L2-captcha"]
for r in log:
    if r["label"] in want:
        h = (r.get("headers", {}) or {})
        print("===== %s [status=%s len=%s ct=%s] =====" % (r["label"], r.get("status"), r.get("length"), h.get("Content-Type","?")[:40]))
        b = r.get("body","")
        print(b[:2500])
        print()
