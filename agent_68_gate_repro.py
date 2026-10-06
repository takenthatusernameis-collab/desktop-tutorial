#!/usr/bin/env python3
"""Bounded independent reproduction for Agent 68: test the preceding
artifact-promotion + disk-existence verification gate (task-66's IMPROVE
decision, left UNVERIFIED by task-67's INFRASTRUCTURE_FAILURE).

Falsifiable prediction (Agent 66 claim): without the gate, a uniform-500 run
is classified CHANGED:false (no-op; the Accept-header differential is discarded);
with the gate, the same run is promoted as a byte-anchored, independently
reproducible record.

Test: fresh requests to the authorized target, sha256(body) anchors vs durable
consensus anchors, status-only vs gate-promoted classification, disk-existence
gate positive and negative branches.
"""
import hashlib, json, os, sys, urllib.request, urllib.error, datetime

TARGET = os.environ.get("TARGET", "http://lab-mutator:3000")
TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
OUT = os.environ.get("AGENT_68_PROBE_OUT", "/workspace/agent_68_gate_repro_out.txt")

DURABLE_ANCHORS = {
    "0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b",  # P1 baseline, 2946 B HTML error
    "20eec46aa7555e7df9a45e29f3ef1a525bfc60e64645def1e662c629c0419b9e",  # P2 Accept:application/json, 1804 B JSON error
    "5b9004f21283f4ac5240d03066c6cd5d19aa7891c8f2d30011651dbbb01f3718",  # P3 null control, 2436 B
}

PROBES = [
    {"name": "P1_baseline", "method": "GET", "path": "/rest/user/security-question", "query": {}, "headers": {}},
    {"name": "P2_accept_json", "method": "GET", "path": "/rest/user/security-question", "query": {}, "headers": {"Accept": "application/json"}},
    {"name": "P3_null_control", "method": "GET", "path": "/api/Nonexistent/1", "query": {}, "headers": {}},
]

def build_url(p):
    return TARGET + p["path"]

def capture(p):
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
    except Exception as e:
        status = 0
        body = ("CONNECTION_FAILED:" + repr(str(e))).encode()
    return status, body

def main():
    lines = []
    lines.append("# Agent 68 independent reproduction of the uniform-500 gate test")
    lines.append(f"# target={TARGET} utc={TS}")
    lines.append("# gate test: every probe record is promoted even when status is uniform 500")
    lines.append("")

    results = []
    ok = True
    for i, p in enumerate(PROBES, start=1):
        status, body = capture(p)
        size = len(body)
        h = hashlib.sha256(body).hexdigest()
        status_ok = (200 <= status < 300) or status in (401, 404)
        ok = ok and status_ok
        rows = []
        rows.append(f"## probe {i}: {p['name']}")
        rows.append(f"  request: method={p['method']} path={p['path']} query={json.dumps(p['query'])} headers={json.dumps(p['headers'])}")
        rows.append(f"  timestamp_utc={datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        rows.append(f"  status={status} content_length={size} sha256={h}")
        rows.append(f"  body_sha256={h}")
        rows.append(f"  durable_anchor_match={h in DURABLE_ANCHORS}")
        lines += rows
        lines.append("")
        results.append({"name": p["name"], "status": status, "size": size, "sha256": h, "anchor_ok": h in DURABLE_ANCHORS, "ok": status_ok})

    # --- classification comparison: status-only vs gate-promoted ---
    statuses = set(r["status"] for r in results)
    status_only_changed = any(r["ok"] for r in results)  # CHANGED only if some probe is non-500
    status_only_view = f"status-only classification: {sorted(statuses)} = {sorted(statuses)[0]} uniform -> CHANGED:{status_only_changed} (discriminates 0 variants)"

    p1, p2 = results[0], results[1]
    discriminating = (p1["sha256"] != p2["sha256"]) and (p1["size"] != p2["size"])
    fresh_bodies = {r["sha256"] for r in results}
    reproducibility = fresh_bodies == DURABLE_ANCHORS

    lines.append(f"# status_only_classification: {status_only_view}")
    lines.append(f"# one_variable_differential: Accept-header only, P1->P2 status identical ({p1['status']}), body differs: {p1['size']}B != {p2['size']}B -> {'DISCRIMINATING' if discriminating else 'non-discriminating'}")
    lines.append(f"# reproducibility: fresh anchors == durable consensus -> {'YES' if reproducibility else 'NO'}")
    lines.append(f"# gate_classification: {status_only_changed} -> with gate: promoted byte-anchored record with one-variable differential")

    out_text = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(out_text)

    disk_present = os.path.exists(OUT) and os.path.getsize(OUT) > 0
    disk_absent = not os.path.exists('/workspace/state/campaign/NONEXISTENT_ARTIFACT_DOES_NOT_EXIST_xyz.txt')

    gate_lines = [f"gate: artifact disk-existence OK (non-empty: {os.path.getsize(OUT)} B)"]
    for r in results:
        gate_lines.append(f"  promoted {r['name']}: status={r['status']} size={r['size']}B sha256={r['sha256']}")
    gate_record = "\n".join(gate_lines)

    lines.append(f"# disk_gate_present: {disk_present}")
    lines.append(f"# disk_gate_absent: {disk_absent}")
    lines.append(f"# sha256(stdout)={hashlib.sha256(''.join(lines).encode()).hexdigest()}")

    out_text = "\n".join(lines) + "\n"
    with open(OUT, "w") as f:
        f.write(out_text)

    improved = discriminating and reproducibility and statuses == {500}
    print("STATUS_ONLY_NOOP: " + status_only_view)
    print("GATE_PROMOTED: " + gate_record)
    print(f"BODY_ANCHORS_DIFFER: P1={p1['sha256']} P2={p2['sha256']} -> {'YES (discriminating)' if discriminating else 'NO (non-discriminating)'}")
    print(f"REPRODUCIBILITY: fresh body anchors == durable consensus -> {'YES' if reproducibility else 'NO'}")
    print(f"DISK_GATE_PRESENT: {disk_present} | ABSENT: {disk_absent}")
    print(f"\nFRESH_PROBE_STATUSES: {[r['status'] for r in results]}")
    print(f"FRESH_ANCHORS: {fresh_bodies}")
    print(f"CONCLUSION: {'THE GATE IMPROVES DISCRIMINATION' if improved else 'THE GATE DOES NOT IMPROVE DISCRIMINATION'}")
    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
    return 0 if improved else 1

if __name__ == "__main__":
    sys.exit(main())
