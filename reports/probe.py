#!/usr/bin/env python3
"""Deterministic black-box probe harness for the Juice Shop benchmark target.

Usage: python3 probe.py <method> <url_encoded_path> [json_body]
Emits one JSON line: {ok,status,length,headers_json,body,trace,timestamp}
"""
import json, sys, time
from urllib.parse import quote
import urllib.request, urllib.error

BASE = "http://lab-mutator:3000"

def req(method, path, body=None, headers=None):
    h = {"User-Agent": "KiloSecurityResearch/1.0", "Accept": "*/*", "Accept-Encoding": "identity"}
    if headers: h.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    url = BASE + path
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            b = resp.read()
            return {"ok": True, "status": resp.getcode(), "length": len(b),
                    "headers": dict(resp.headers), "body": b.decode("utf-8", "replace"),
                    "trace": "ok", "timestamp": stamp}
    except urllib.error.HTTPError as e:
        b = e.read()
        return {"ok": False, "status": e.code, "length": len(b),
                "headers": dict(e.headers), "body": b.decode("utf-8", "replace"),
                "trace": f"HTTP{e.code}", "timestamp": stamp}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr); sys.exit(1)
    method = sys.argv[1].upper()
    path = sys.argv[2]
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    r = req(method, path, body)
    r["path"] = path
    r["method"] = method
    print(json.dumps(r, sort_keys=True))
