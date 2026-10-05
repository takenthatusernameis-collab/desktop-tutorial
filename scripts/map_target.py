#!/usr/bin/env python3
"""Black-box surface mapper for the authorized benchmark target.
Pass 0-1: baseline + broad attack-surface mapping.
Probes endpoints extracted from the client bundle; records status, CT, body hints.
"""
import re, json, sys, urllib.request, urllib.error
from collections import defaultdict

TARGET = "http://lab-mutator:3000"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/reports/mapping.json"

def req(path, method="GET", headers=None, body=None):
    h = headers or {}
    h["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    data = body.encode() if isinstance(body, str) else body
    r = urllib.request.Request(TARGET + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, dict(e.headers), body
    except Exception as e:
        return None, {}, str(e)

def extract_endpoints(js):
    seen = set()
    for pat in [
        r'["\']([^"\']+/[^"\']*)["\']\s*[),;]',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.\w+?\(["\']([^"\']+)["\']',
        r'router\.get\(["\']([^"\']+)["\']',
        r'router\.post\(["\']([^"\']+)["\']',
        r'["\']/(rest|api|npm|assets|i18n|public)/[^"\']*["\']',
    ]:
        for m in re.finditer(pat, js):
            p = m.group(1)
            if not p.startswith("/"):
                continue
            p = re.sub(r"\?[^,)*]*$", "", p)
            p = re.sub(r"\{[^}]*\}", "", p)
            if p in seen or p == "/":
                continue
            seen.add(p)
    return sorted(seen)

def main():
    print("Getting main.js...", file=sys.stderr)
    status, hdrs, js = req("/assets/js/main.js")
    if status != 200:
        print(f"main.js fetch failed: {status}", file=sys.stderr)
        sys.exit(1)
    endpoints = extract_endpoints(js)
    print(f"Extracted {len(endpoints)} candidate endpoints", file=sys.stderr)

    results = {}
    options = []
    errors = []
    for path in endpoints:
        method_info = {}
        for method in ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"]:
            st, h, b = req(path, method)
            prefix = b[:100].replace("\n", " ")
            method_info[method] = {"status": st, "ct": h.get("Content-Type", ""), "body": prefix}
        results[path] = method_info
        _, h, b = req(path, "GET")
        if h.get("Allow") or "options" in path.lower():
            options.append((path, h.get("Allow")))
        if h.get("Allow") is None and "options" not in path.lower():
            # capture Allow header from OPTIONS when GET gives none
            _, oh, _ = req(path, "OPTIONS")
            if oh.get("Allow"):
                options.append((path, oh.get("Allow")))
        if method_info["GET"]["status"] == 500:
            errors.append((path, method_info["GET"]["body"][:80], method_info))

    by_status = defaultdict(list)
    for path, info in results.items():
        statuses = sorted(set(x["status"] for x in info.values() if x["status"] is not None))
        by_status[str(statuses)].append(path)

    output = {"endpoints": list(results.keys()), "by_status": dict(by_status),
              "options": options[:60], "500_routes": [{"path": p, "body": b} for p, b, _ in errors[:40]]}
    with open(OUT, "w") as f:
        json.dump(output, f, indent=1)
    print(f"Wrote {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
