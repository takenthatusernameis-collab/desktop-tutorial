#!/usr/bin/env python3
"""Final gate confirmation: 2x security-question, F1/F2/F3 sizes, F5 status."""
import json, subprocess, sys

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

log = []
def rec(label, r):
    r["label"] = label
    log.append(r)
    print("%-22s status=%s len=%s" % (label, r.get("status"), r.get("length")))

rec("SQ-1", run("GET", "/rest/user/security-question", {"email": "bjoern@juice-sh.op"}))
rec("SQ-2", run("GET", "/rest/user/security-question", {"email": "bjoern@juice-sh.op"}))
rec("SQ-3", run("GET", "/rest/user/security-question", {"email": "nobody@nobody.com"}))
rec("F1-1", run("GET", "/rest/memories"))
rec("F1-2", run("GET", "/rest/memories"))
rec("F2-get", run("GET", "/api/SecurityAnswers/"))
rec("F2-post", run("POST", "/api/SecurityAnswers/", {}))
rec("F3-apple", run("GET", "/rest/products/search", {"q": "Apple"}))
rec("F3-taut", run("GET", "/rest/products/search", {"q": "'%20OR%20%271%27=%271"}))
rec("F3-empty", run("GET", "/rest/products/search", {}))

json.dump(log, open("reports/probes_live/probe_2026-10-05T0438Z.json","w"), indent=1, sort_keys=True)
print("wrote probe_2026-10-05T0438Z.json")
