import json

BASE = "http://lab-mutator:3000"
def get(path):
    r = urllib.request.Request(BASE + path)
    resp = urllib.request.urlopen(r, timeout=15)
    return resp.read().decode("utf-8", "replace")

import urllib.request
b = get("/api/Challenges/")
data = json.loads(b)
challs = data['data']
print("count:", len(challs))
print("solved:", [c['id'] for c in challs if c.get('solved')])
print("disabledEnv:", sorted(c['id'] for c in challs if c.get('disabledEnv')))

stored = {c[0]: c for c in json.load(open('/workspace/reports/focus.json'))[3]['challenges']}
keys_fetched = {c['key'] for c in challs}
keys_stored = set(stored)
print("\nfetched keys:", len(keys_fetched))
print("stored keys:", len(keys_stored))
print("fetched not stored:", sorted(keys_fetched - keys_stored))
print("stored not fetched:", sorted(keys_stored - keys_fetched))

# Map: id -> key
fetched_map = {c['id']: c['key'] for c in challs}
print("\n=== id->key mapping (first 20) ===")
for i in range(1, 21):
    print(f"  {i}: {fetched_map.get(i)}")

print("\n=== categories present ===")
from collections import Counter
print(dict(Counter(c.get('category','?') for c in challs)))
print("\n=== challenges referencing mutation/hint keywords in desc ===")
keywords = ["mutat","hidden","new","secret","leak","bounty","capture","flag","benchmark","ehb","gateway","jailbreak","system","injection","override","bypass","unauth","public","direct","raw","capture","jailbreak","escape","poison","inject","exfil"]
found = []
for c in challs:
    text = (c.get('description') or '') + (c.get('name') or '')
    if any(kw in text.lower() for kw in keywords):
        found.append((c['id'], c['key'], text[:200]))
for i, k, t in found:
    print(f"  id={i} key={k} desc={t}")
if not found:
    print("  none")
