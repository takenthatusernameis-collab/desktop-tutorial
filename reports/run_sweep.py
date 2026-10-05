import json, subprocess, time, sys
routes = json.load(open("/workspace/reports/routes_candidates.json"))
seen = {}
seen_200 = []
seen_401 = []
seen_others = {}
for i, r in enumerate(routes):
    try:
        out = subprocess.run(["curl","-s","-m","3","-w","\nSTATUS=%{http_code}\nSIZE=%{size_download}\nTIME=%{time_total}\n","http://lab-mutator:3000"+r], capture_output=True, text=True, timeout=3)
        code = int(out.stdout.split("STATUS=")[1].split("\n")[0])
        size = out.stdout.split("SIZE=")[1].split("\n")[0]
        time_s = out.stdout.split("TIME=")[1].split("\n")[0]
        if code == 200:
            seen_200.append((r, size, time_s))
        elif code == 401:
            seen_401.append(r)
        else:
            seen_others.setdefault(code, []).append((r, size, time_s))
    except Exception as e:
        seen_others.setdefault("ERR", []).append((r, str(e)))
    if i % 50 == 0:
        print(f"progress {i}/{len(routes)} 200={len(seen_200)} 401={len(seen_401)} others={sum(len(v) for v in seen_others.values())}", flush=True)
json.dump({"200": seen_200, "401": seen_401, "others": seen_others}, open("/workspace/reports/sweep_results.json","w"), indent=0)
print("DONE", len(routes), "probed", flush=True)
