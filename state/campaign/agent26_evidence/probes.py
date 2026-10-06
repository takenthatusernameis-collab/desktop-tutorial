#!/usr/bin/env python3
import hashlib, urllib.request, datetime
BASE="http://lab-mutator:3000"
TS=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%M%SZ')
OUT=f"agent26_fresh_probes3_{TS}.txt"
probes=[
    ("REPR1 no-accept","GET","rest/user/security-question",{}),
    ("REPR2 accept-json","GET","rest/user/security-question",{"Accept":"application/json"}),
    ("REPR3 redirect","GET","redirect?continue=http://example.com",{}),
    ("CONTROL","GET","api/Nonexistent/1",{}),
]
def get(method,path,headers):
    req=urllib.request.Request(f"{BASE}/{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read(), r.headers.get_content_type()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get_content_type()
with open(OUT,"w") as f:
    f.write(f"Fresh id=27 trigger-class reproduction — {OUT}\n")
    f.write(f"Target: {BASE} ; session started UTC: {TS}\n")
    f.write("="*70+"\n")
    for label,method,path,headers in probes:
        for i in range(1,3):
            status,data,ct=get(method,path,headers)
            h=hashlib.sha256(data).hexdigest()
            head=data[:200].decode("utf-8","replace").replace("\n"," ")
            f.write(f"{label} (probe {i}): status={status} size={len(data)} B content-type={ct} sha256={h}\n")
            f.write(f"   body head=[{head}]\n")
    f.write("DONE: "+OUT+"\n")
print("Wrote",OUT)
