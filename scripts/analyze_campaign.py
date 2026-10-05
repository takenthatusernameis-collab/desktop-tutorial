#!/usr/bin/env python3
"""Analyze campaign.json output: extract status summaries and differential differences."""
import json

with open("reports/campaign.json") as f:
    raw = json.load(f)

print("=== 1. Baseline GET status map ===")
for path, m in raw["baseline"]["paths"].items():
    g = m.get("GET", {})
    status = g.get("status", "?")
    body_prefix = g.get("body", "")[:80].replace("\n", " ")
    print(f"{status:5}  {path:55}  {body_prefix}")

print("\n=== 2. Methodsweep: non-200 GET status map ===")
seen = {}
for path, m in raw["methodsweep"]["paths"].items():
    g = m.get("GET", {})
    status = g.get("status", "?")
    if status != 200:
        body_prefix = g.get("body", "")[:70].replace("\n", " ")
        print(f"{status:5}  {path:55}  {body_prefix}")

print("\n=== 3. Methods with non-200 responses on key endpoints ===")
for path, m in raw["methodsweep"]["paths"].items():
    if path.startswith("/rest/") or path.startswith("/api/"):
        nonzero = {meth: v.get("status") for meth, v in m.items() if v.get("status") != 200}
        if nonzero:
            print(f"{path}: {nonzero}")

print("\n=== 4. Differentials ===")
for d in raw["differentials"]:
    print(f"\n--- {d['label']} ---")
    for c in d["cases"]:
        body = c.get("body", "")[:120].replace("\n", " ")
        print(f"  [{c['status']:5}] {c['name']:35} len={c['length']:6}  {body}")

print("\n=== 5. web3 GET status ===")
for path, m in raw["web3_get"]["paths"].items():
    g = m.get("GET", {})
    print(f"{path:35} GET={g.get('status')}: {g.get('body','')[:70].replace(chr(10),' ')}")

print("\n=== 6. web3 POST status ===")
for path, m in raw["web3_methods"]["paths"].items():
    for meth, v in m.items():
        if v.get("status") is not None:
            print(f"{path:35} {meth}: {v['status']}  {v.get('body','')[:70].replace(chr(10),' ')}")
