import urllib.request, urllib.error, json, time, sys
B="http://lab-mutator:3000"
paths = sys.argv[1:]
def probe(p):
    for m in ["GET"]:
        try:
            r=urllib.request.Request(B+p, method=m, headers={"User-Agent":"Mozilla/5.0 (research)"})
            with urllib.request.urlopen(r,timeout=8) as rr:
                return m, "200", len(rr.read()), rr.headers.get("content-type","")
        except urllib.error.HTTPError as e:
            return m, str(e.code), len(e.read()), "text/html"
        except Exception as ex:
            return m, "ERR", 0, f"{type(ex).__name__}"
results=[]
for p in paths:
    m, st, sz, ct = probe(p)
    results.append([p, st, sz, ct])
    time.sleep(0.02)
json.dump(results, open("/workspace/reports/sweep_paths.json","w"))
print(f"wrote {len(results)}")
for r in results:
    if r[1] not in ("500","ERR") and int(r[1]) < 400:
        print(r)
