import json, hashlib, urllib.request
BASE="http://lab-mutator:3000"
def req(path,h=None,b=None):
    h=dict(h or {}); 
    if b and not isinstance(b,bytes): h["Content-Type"]="application/json"; b=json.dumps(b).encode()
    r=urllib.request.Request(BASE+path,method="GET",headers=h,data=b if b else None)
    with urllib.request.urlopen(r,timeout=20) as f: return f.read()

print("== CAPTCHA structure ==")
d=req("/rest/captcha")
print("call1:", d.decode())
d=req("/rest/captcha")
print("call2:", d.decode())
print()
print("== MEMORIES structure (first record) ==")
d=req("/rest/memories")
m=json.loads(d)
print(json.dumps(m[0], indent=1)[:900])
print()
print("== SQ question for bjoern ==")
d=req("/rest/user/security-question?email=bjoern@owasp.org")
print(d.decode())
print()
print("== SQ for emma ==")
d=req("/rest/user/security-question?email=emma@juice-sh.op")
print(d.decode())
