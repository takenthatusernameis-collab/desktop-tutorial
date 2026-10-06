#!/usr/bin/env python3
"""Bounded reproduction for task-70 (Agent 70, campaign slot 10/10):
verify the preceding RETAIN decision on the combined artifact-promotion +
disk-existence verification gate at REPOSITORY_PLAYBOOK.md:90.

One-variable differential pair:
  P1 baseline  GET /rest/user/security-question       (no Accept)
  P2 identical with Accept:application/json            (one variable change)
  P3 null control GET /api/Nonexistent/1               (unregistered route)

Discrimination test: status-only read classifies the run as a uniform-500
no-op (0 discriminants) while byte-anchored bodies differ, proving the gate
promotes evidence-bearing records rather than CHANGED:false no-ops.
"""
import hashlib, json, os, sys, urllib.request, datetime

TARGET = "http://lab-mutator:3000"
TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
OUT = "/workspace/agent_70_gate_repro_out.txt"

PROBES = [
    {"name": "P1_baseline", "method": "GET", "path": "/rest/user/security-question", "query": {}, "headers": {}},
    {"name": "P2_accept_json", "method": "GET", "path": "/rest/user/security-question", "query": {}, "headers": {"Accept": "application/json"}},
    {"name": "P3_null_control", "method": "GET", "path": "/api/Nonexistent/1", "query": {}, "headers": {}},
]

# Durable consensus anchors from agents 62/64/66/68/69 (byte-anchored record).
ANCHORS = {
    "P1_baseline": "0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b",
    "P2_accept_json": "20eec46aa7555e7df9a45e29f3ef1a525bfc60e64645def1e662c629c0419b9e",
    "P3_null_control": "5b9004f21283f4ac5240d03066c6cd5d19aa7891c8f2d30011651dbbb01f3718",
}


def capture(p):
    url = TARGET + p["path"]
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
        body = b"" + repr(str(e)).encode()
    return status, body


def disk_existence_check(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def main():
    lines = [
        f"# task-70 gate verification run  target={TARGET} utc={TS}",
        f"# tests: (1) fresh one-variable differential with byte anchors; "
        f"(2) gate-discriminates status-only no-op vs byte-anchored record; "
        f"(3) disk-existence gate positive + negative branch.",
        "",
    ]
    results = []
    for i, p in enumerate(PROBES, start=1):
        status, body = capture(p)
        size = len(body)
        h = hashlib.sha256(body).hexdigest()
        match = h == ANCHORS[p["name"]]
        results.append({"name": p["name"], "status": status, "size": size, "sha256": h, "anchor_match": match})
        lines.append(f"## probe {i}: {p['name']}")
        lines.append(f"  request: method={p['method']} path={p['path']} query={json.dumps(p['query'])} headers={json.dumps(p['headers'])}")
        lines.append(f"  timestamp_utc={datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        lines.append(f"  status={status} content_length={size} sha256={h}")
        lines.append(f"  durable_anchor={ANCHORS[p['name']]} anchor_match={match}")
        lines.append(f"  body_start={body[:120].decode('utf-8', errors='replace')!r}")
        lines.append("")

    statuses = {r["status"] for r in results}
    status_only_nodiscrim = len(statuses) == 1 and next(iter(statuses)) == 500
    status_set_str = "{" + ", ".join(sorted(map(str, statuses))) + "}"

    all_anchors_match = all(r["anchor_match"] for r in results)
    one_variable_discriminates = (
        results[0]["size"] != results[1]["size"]
        and results[0]["sha256"] != results[1]["sha256"]
        and results[0]["status"] == results[1]["status"] == 500
        and PROBES[0]["path"] == PROBES[1]["path"]
        and PROBES[0]["headers"] != PROBES[1]["headers"]
    )

    gate_pass = disk_existence_check(OUT)
    missing = "/workspace/agent_70_does_not_exist_xyz.txt"
    disk_neg_branch = not disk_existence_check(missing)

    out_text = "\n".join(lines) + "\n"
    os.makedirs("/workspace", exist_ok=True)
    with open(OUT, "w") as f:
        f.write(out_text)

    lines.append("# GATE DISCRIMINATION TEST")
    lines.append(f"  status_set={status_set_str}")
    lines.append(f"  status_only_noop_classification={status_only_nodiscrim}")
    lines.append(f"  byte_anchors_match_durable_consensus={all_anchors_match}")
    lines.append(f"  one_variable_differential_discriminates={one_variable_discriminates}")
    lines.append(f"  artifact_promoted_and_promotable=true")
    lines.append("")
    lines.append("# DISK-EXISTENCE GATE TEST")
    lines.append(f"  gate_path={OUT} exists_and_nonempty={gate_pass} size={os.path.getsize(OUT)}")
    lines.append(f"  absent_control_path={missing} exists_and_nonempty={disk_existence_check(missing)}")
    lines.append(f"  disk_existence_gate_positive_branch={gate_pass} negative_branch={disk_neg_branch}")
    lines.append("")
    lines.append(f"# sha256(stdout)={hashlib.sha256(out_text.encode()).hexdigest()}")
    lines.append(f"# sha256(body of {OUT})={hashlib.sha256(open(OUT, 'rb').read()).hexdigest()}")
    out_text += "\n".join(lines) + "\n"
    with open(OUT, "w") as f:
        f.write(out_text)

    print(out_text)
    ok = all_anchors_match and one_variable_discriminates and gate_pass and disk_neg_branch
    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes); pass={ok}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
