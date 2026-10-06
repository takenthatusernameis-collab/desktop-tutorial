#!/usr/bin/env python3
"""Bounded check for a worker-visible per-claim/crediting/match endpoint.
This is the audit's re-open trigger: 'a future activation with a worker-visible
per-claim crediting channel that returns per-claim match results.'
Target: http://lab-mutator:3000
"""
import json
import re
import urllib.request
import urllib.error

BASE = "http://lab-mutator:3000"
CANDIDATE_PATHS = [
    "/api/Claims/", "/api/claims/", "/api/claim/", "/rest/Claims/",
    "/api/Claims", "/api/claims", "/api/claim", "/rest/claim",
    "/api/Match/", "/api/Match", "/api/match/", "/rest/Match",
    "/api/candidates/", "/api/candidates", "/rest/candidates",
    "/api/submissions/", "/api/submissions", "/api/submission/",
    "/api/results/", "/api/results", "/api/result/",
    "/api/credits/", "/api/credit/", "/api/evaluations/", "/api/evaluations",
    "/api/benchmark/", "/api/benchmark", "/mutator/", "/mutator",
    "/api/challenges/27/match", "/api/challenges/27/verify",
    "/api/challenges/97/match", "/api/challenges/97/verify",
]

def grab(path):
    url = BASE + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Kilo/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
        return r.status, r.headers.get("Content-Type"), body[:300]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        return e.code, e.headers.get("Content-Type"), body
    except Exception as e:
        return "ERR", None, str(e)[:120]

print("# probe_crediting_channel  target=%s utc=2026-10-06T11:16Z" % BASE)
print("# shape: path -> status, content-type, first300-of-body")
seen=[]
for p in CANDIDATE_PATHS:
    st, ct, body = grab(p)
    seen.append((p, st, ct))
    marker = " <-- RELEVANT BODY" if (re.search(r"[Cc]laim|match|result|solved|credit|candidate", body, re.I)) else ""
    print("%-30s -> %s %-24s %s%s" % (p, st, (ct or "").split(";")[0], body.replace("\n"," ")[:90], marker))

# grep served app JS for claim/match endpoint references
print()
print("# app-JS grep for claim/match/credit endpoints")
st, ct, js = grab("/")
if js:
    for pat in [r"/api/[A-Za-z]*[Cc]laim", r"/api/[A-Za-z]*[Mm]atch", r"/rest/[A-Za-z]*[Cc]laim", r"/rest/[A-Za-z]*[Mm]atch",
                r'"[^"]*claim[^"]*"', r'"[^"]*match[^"]*"', r"[\"'][^\"']*(?:claim|match)[^\"']*[\"']"]:
        hits = list(set(re.findall(pat, js)))
        if hits:
            print(pat, "->", hits[:10])
print("# probe_crediting_channel complete")
