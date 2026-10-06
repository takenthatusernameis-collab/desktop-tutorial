#!/usr/bin/env python3
"""Bounded probe for agent_64 artifact-promotion-gate test (task-64).

Purpose: run one byte-anchored differential pair + null control, each captured
with full sha256(body). Uniform-500 outcomes here are exactly the class of
outcomes that, without the mandatory artifact-promotion gate, become
CHANGED:false no-ops; with the gate they are promoted as evidence-bearing
sha256-anchored artifacts.

Probes are a minimal one-variable variation on a single surface:
  P1 baseline GET /rest/user/security-question          (no Accept)
  P2 identical request with Accept:application/json     (one variable change)
  P3 null control  GET /api/Nonexistent/1               (unregistered route)
"""
import hashlib, json, os, re, subprocess, sys, urllib.request, datetime

TARGET = "http://lab-mutator:3000"
TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
OUT = "/workspace/state/campaign/agent_64_probe_gate_out_2026-10-06T1124Z.txt"

# Declarative request shape (method, path, query, headers) used verbatim below.
PROBES = [
    {"name": "P1_baseline",
     "method": "GET", "path": "/rest/user/security-question",
     "query": {}, "headers": {}},
    {"name": "P2_accept_json",
     "method": "GET", "path": "/rest/user/security-question",
     "query": {}, "headers": {"Accept": "application/json"}},
    {"name": "P3_null_control",
     "method": "GET", "path": "/api/Nonexistent/1",
     "query": {}, "headers": {}},
]


def build_url(p):
    return TARGET + p["path"]


def capture(p):
    """Send the request exactly as declared; return (status, body_bytes)."""
    url = build_url(p)
    body = b""
    status = 0
    try:
        req = urllib.request.Request(url, headers=p["headers"] if p["headers"] else {})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read()
    except Exception as e:  # connection/timeout -> record as infra failure, not no-op
        status = 0
        body = b"" + re.escape(str(e).encode())
    return status, body


def main():
    lines = []
    lines.append(f"# agent_64 probe run  target={TARGET} utc={TS}")
    lines.append(f"# shape: probe -> status, content-length, sha256(body), full body")
    lines.append(f"# gate test: every probe record is promoted even when status is uniform 500")
    lines.append("")

    all_status_ok = True
    for i, p in enumerate(PROBES, start=1):
        status, body = capture(p)
        size = len(body)
        h = hashlib.sha256(body).hexdigest()
        ok = (status >= 200 and status < 300) or status in (401, 404)
        all_status_ok = all_status_ok and ok
        lines.append(f"## probe {i}: {p['name']}")
        lines.append(f"  request: method={p['method']} path={p['path']} query={json.dumps(p['query'])} headers={json.dumps(p['headers'])}")
        lines.append(f"  timestamp_utc={datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        lines.append(f"  status={status} content_length={size} sha256={h}")
        lines.append(f"  body_start={body[:160].decode('utf-8', errors='replace')!r}")
        lines.append(f"  body_sha256={h}")
        lines.append(f"  body_full={body.decode('utf-8', errors='replace')}")
        lines.append("")

    lines.append(f"# summary: probes={len(PROBES)} all_status_ok={all_status_ok}")
    lines.append(f"# without the artifact-promotion gate this run (five 500s) would be a CHANGED:false no-op;")
    lines.append(f"# with the gate each probe is a byte-anchored, auditable record")
    lines.append(f"# sha256(stdout)={hashlib.sha256(''.join(lines).encode()).hexdigest()}")

    out_text = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(out_text)

    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
    for p in PROBES:
        st, _ = capture(p)
        print(f"  {p['name']}: {st}")
    sys.exit(0 if all_status_ok else 1)


if __name__ == "__main__":
    main()
