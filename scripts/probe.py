#!/usr/bin/env python3
"""Multi-method probe campaign: passes all discovered REST/SPA routes through
GET/HEAD/OPTIONS/PUT/DELETE/PATCH, records status/CT/body hints.
"""
import re, json, sys, os, urllib.request, urllib.error, time
from collections import defaultdict

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/probes.json"
BUNDLE = "/tmp/main.js"

def load_endpoints(js):
    routes = set()
    for m in re.finditer(r'/(rest|api)/[a-zA-Z0-9_${}+/-]*[a-zA-Z0-9_]*/?[a-zA-Z0-9_]*', js):
        p = m.group(0)
        p = re.sub(r"\$\{[^}]*\}", "", p)
        p = p.rstrip("/").rstrip("+")
        p = re.sub(r"/${e}/?","/", p)
        routes.add(p)
    return sorted(routes)

def req(path, method="GET", body=None):
    h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    data = body.encode() if isinstance(body, str) else body
    r = urllib.request.Request(TARGET + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, dict(e.headers), body
    except Exception as e:
        return None, {}, str(e)

def main():
    js = open(BUNDLE).read() if os.path.exists(BUNDLE) else ""
    if not js:
        js = urllib.request.urlopen(TARGET + "/main.js", timeout=30).read().decode("utf-8", "replace")
    routes = load_endpoints(js)
    print(f"Probing {len(routes)} routes", file=sys.stderr)

    results = {}
    anomalies = []  # (path, method, status, body[:60])
    for i, path in enumerate(routes):
        info = {}
        for method in ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"]:
            st, hdrs, body = req(path, method)
            info[method] = {"status": st, "ct": hdrs.get("Content-Type", ""),
                            "body": body[:80].replace("\n", " "),
                            "headers": {k: hdrs.get(k) for k in ("Allow", "Access-Control-Allow-Origin", "WWW-Authenticate")}}
            if st not in (200, 201, 204, 301, 302, 304, 401, 403, 404, 500):
                anomalies.append((path, method, st, body[:80], "other_status"))
            elif st in (500, 400, 401, 403) and "body" not in results.get(path, {}).get("GET", {}):
                anomalies.append((path, method, st, body[:80], "error_status"))
        results[path] = info
        if (i + 1) % 30 == 0:
            print(f"  probed {i+1}/{len(routes)}", file=sys.stderr)
        time.sleep(0.02)

    out = {"routes": list(results.keys()), "details": results,
           "anomalies": [{"path": p, "method": m, "status": s, "body": b, "kind": k} for p, m, s, b, k in anomalies]}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"Wrote {OUT}: {len(anomalies)} anomalies", file=sys.stderr)

if __name__ == "__main__":
    main()
