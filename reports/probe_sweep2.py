#!/usr/bin/env python3
"""Focused additional sweep: access logs, data export, pastebin, debug, admin, and other Juice Shop API routes."""
import json, subprocess, sys, os

OUT = "/workspace/reports/probes_live"
os.makedirs(OUT, exist_ok=True)

def run(method, path, body=None):
    args = [sys.executable, "/workspace/reports/probe.py", method, path]
    if body is not None:
        args.append(json.dumps(body))
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    out = (p.stdout.strip() or p.stderr.strip())
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "trace": "parsefail", "body": out[:200]}

ts = "2026-10-05T0437Z"
routes = [
    "/rest/access-logs", "/api/accessLogs", "/api/access-logs", "/access-logs", "/logs", "/debug", "/debug/trace",
    "/rest/user/export", "/rest/user/data-export", "/data-export", "/api/Export/",
    "/rest/pastebin", "/api/pastebin", "/pastebin", "/rest/paste", "/api/Feedbacks/",
    "/rest/admin", "/api/admin", "/admin", "/rest/score-board", "/api/challenges",
    "/rest/user/account", "/rest/user/profile", "/rest/user/settings",
    "/rest/coupons", "/api/Coupons/", "/rest/reviews", "/api/Reviews/",
    "/rest/products", "/rest/users", "/rest/orders", "/rest/basket-items",
    "/assets/public/images/uploads/", "/ftp", "/backups", "/secrets", "/credentials",
    "/.env", "/.git/config", "/config.json", "/api/Challenges/",
]
log = []
def rec(label, r):
    r["label"] = label
    r["ts"] = ts
    log.append(r)
    print("%-28s status=%s len=%s" % (label, r.get("status"), r.get("length")))

for i, p in enumerate(routes):
    rec("E-%d-%s" % (i, p.replace("/","_").replace("-","_")), run("GET", p))

with open(os.path.join(OUT, "probe_%s.json" % ts), "w") as f:
    json.dump(log, f, indent=1, sort_keys=True)
print("wrote", os.path.join(OUT, "probe_%s.json" % ts))
