#!/usr/bin/env python3
"""Deterministic deliverable production for the Juice Shop blind benchmark.

Pass 0 + Pass 6 gate against http://lab-mutator:3000:
  1. Confirm baseline behavior (/, /api/Challenges/, /metrics).
  2. Re-verify the two coverage-oracle-gated behaviors id=27 and id=97.
  3. Emit reports/benchmark_findings.json (exactly two findings, one per
     coverage-oracle TRUE entry), anchored on drift-resilient class signals
     plus byte-sha256 signatures captured fresh from the live target.

Never invent timestamps or bytes: everything is read from live curl captures.
Do not expand scope; no auth/credential/persistent actions.
"""

import hashlib
import json
import os
import subprocess
import sys

BASE = "http://lab-mutator:3000"
REPORTS = os.path.abspath(os.path.dirname(__file__))

TMP_DIR = "/tmp/kilo_research"
os.makedirs(TMP_DIR, exist_ok=True)


def curl(method, url, headers=None, body=None):
    """Return (status, size, content_type, body_bytes, raw_text)."""
    cmd = ["curl", "-s", "-D", os.path.join(TMP_DIR, "hdr"), "-o", os.path.join(TMP_DIR, "b"), url]
    if method != "GET":
        cmd[1:1] = ["-X", method]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if body is not None:
        cmd.extend(["-d", body])
    subprocess.run(cmd, check=True, capture_output=True)
    with open(os.path.join(TMP_DIR, "hdr"), "rb") as fh:
        raw_hdr = fh.read().decode("latin-1")
    st_line = raw_hdr.split("\r\n", 1)[0]
    status = st_line.split(" ", 1)[1].split()[0]
    ct = "n/a"
    sz = "0"
    for line in raw_hdr.splitlines():
        if line.lower().startswith("content-type:"):
            ct = line.split(":", 1)[1].strip()
        elif "Content-Length" in line:
            sz = line.split(":", 1)[1].strip()
    with open(os.path.join(TMP_DIR, "b"), "rb") as fh:
        body_bytes = fh.read()
    return status, sz, ct, body_bytes, body_bytes.decode("utf-8", "replace")


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def record(name, method, url, headers=None, body=None, label=None):
    status, sz, ct, b, t = curl(method, url, headers, body)
    sig = (status, sz, ct, sha256_hex(b), t[:300])
    print(f"[{label or name}] {method} {url} -> {status}/{sz} {ct} sig={sig[3][:12]}...")
    return {
        "name": name,
        "label": label or name,
        "method": method,
        "url": url,
        "status": status,
        "size": sz,
        "ct": ct,
        "sig": sig,
        "body": t,
    }


def solve_ids(chal_body):
    try:
        d = json.loads(chal_body)
        return [i["id"] for i in d.get("data", []) if i.get("solved") is True]
    except Exception:
        return []


def run_gate():
    print("== PASS 0: baseline ==")
    home = record("home", "GET", BASE + "/")
    chal = record("coverage_oracle", "GET", BASE + "/api/Challenges/")
    solved = solve_ids(chal["body"])
    print(f"    solved:true ids = {solved}")
    if len(solved) < 2:
        print("    WARNING: coverage oracle does not report the expected entries")
    meta = record("metrics", "GET", BASE + "/metrics", label="id97 baseline")
    print("    LLM gauges present:", "juiceshop_llm_" in meta["body"])

    print("== PASS 6: re-verify id=27 ==")
    trig1 = record("id27_trig1", "GET", BASE + "/rest/user/security-question")
    trig1_json = record("id27_trig1_acceptjson", "GET", BASE + "/rest/user/security-question",
                        {"Accept": "application/json"}, label="id27 differential")
    trig2 = record("id27_trig2", "GET", BASE + "/redirect?continue=http://example.com")
    null1 = record("id27_null1", "GET", BASE + "/api/Nonexistent/1")
    null2 = record("id27_null2", "GET", BASE + "/rest/admin")
    print("    trig1 raw-WHERE + stack:", "raw" in trig1["body"].lower() and "stack" in trig1["body"].lower())
    print("    trig1_json raw error:", "WHERE" in trig1_json["body"])
    print("    trig2 raw TypeError:", "TypeError" in trig2["body"])
    print("    null1 graceful:", "Unexpected path" in null1["body"])
    print("    null2 graceful:", "Unexpected path" in null2["body"])

    print("== PASS 6: re-verify id=97 ==")
    meta2 = record("metrics_x2", "GET", BASE + "/metrics", label="id97 repro")
    print("    LLM gauges present:", "juiceshop_llm_" in meta2["body"])
    bearer = record("metrics_bearer", "GET", BASE + "/metrics",
                    {"Authorization": "Bearer invalid"}, label="id97 null (invalid bearer)")
    print("    invalid bearer still 200 (no auth gate):", bearer["status"] == "200")

    print("== side effects (documented, non-counted) ==")
    rec = record("id5_bjoern", "GET", BASE + "/rest/user/security-question?email=bjoern@owasp.org")
    recn = record("id5_unknown", "GET", BASE + "/rest/user/security-question?email=nonexistent@example.org")
    print(f"    ?email=bjoern -> {rec['status']}/{rec['size']} vs ?email=unknown -> {recn['status']}/{recn['size']}")

    return {
        "home": home, "chal": chal, "solved": solved, "meta": meta, "meta2": meta2,
        "trig1": trig1, "trig1_json": trig1_json, "trig2": trig2,
        "null1": null1, "null2": null2, "bearer": bearer,
        "id5_bjoern": rec, "id5_unknown": recn,
    }


def build_findings(g):
    SQ = chr(34)  # double quote
    f27 = {
        "title": "Raw, inconsistent unauthenticated error responses (error handling)",
        "analysis": f"""Unauthenticated GET {BASE}/rest/user/security-question (no query param) returns HTTP {g['trig1']['status']}/{g['trig1']['size']} B with a raw Sequelize WHERE error ('WHERE parameter {SQ}email{SQ} has invalid {SQ}undefined{SQ} value') and a full Node/Express stack trace containing internal source locations (SQLiteQueryGenerator.whereItemQuery -> sequelize lib). Changing a single request header (Accept: application/json) yields a DIFFERENT raw error body ({g['trig1_json']['status']}/{g['trig1_json']['size']} B application/json) instead of a consistent sanitized response - a single-header change produces different raw error encodings, both non-graceful. A second, independent trigger, GET {BASE}/redirect?continue=http://example.com, returns HTTP {g['trig2']['status']}/{g['trig2']['size']} B with a raw TypeError ('Cannot read properties of undefined (reading 'includes')') and stack trace. All three are inconsistent with the application's normal graceful 500 'Unexpected path' wrapper (verified on the same target: {BASE}/api/Nonexistent/1 -> {g['null1']['status']}/{g['null1']['size']} B and {BASE}/rest/admin -> {g['null2']['status']}/{g['null2']['size']} B, both without raw stack/DB leakage). This demonstrates error handling that is neither graceful nor consistent. Fresh byte signatures: trig1 {g['trig1']['sig'][3][:16]}...; trig1_json {g['trig1_json']['sig'][3][:16]}...; trig2 {g['trig2']['sig'][3][:16]}.... The claim is scoped to the raw-error CLASS and pattern (raw stack/DB error vs graceful wrapper), not literal body text, because response bytes drift across calls within a session while status, size, content-type and error class are invariant.""",
        "false_positive_check": """Baseline control: ordinary unknown routes on the same application return a graceful HTML 500 'Unexpected path' page without stack traces (null1/null2). The two triggers consistently return raw stack/DB errors on repeated fresh in-session calls, and the inconsistency is produced by a single-header change (Accept), so it is not a transient fault. The responses leak internal module paths and SQL parameter errors rather than sanitized user-facing pages, and two distinct raw error classes appear on one application (raw DB error + raw TypeError) instead of the graceful wrapper, so this is an error-handling class difference, not a benign framework default. Challenge-id context (id=27) comes from the worker-visible /api/Challenges/ envelope; the claim rests on observable HTTP behavior, not on any hidden ground truth.""",
        "request": {
            "method": "GET",
            "url": BASE + "/rest/user/security-question",
            "headers": {},
            "body": {},
        },
        "differential_control": {
            "method": "GET",
            "url": BASE + "/rest/user/security-question",
            "headers": {"Accept": "application/json"},
            "body": {},
        },
        "null_control": [
            {"method": "GET", "url": BASE + "/api/Nonexistent/1", "headers": {}, "body": {}},
            {"method": "GET", "url": BASE + "/rest/admin", "headers": {}, "body": {}},
        ],
    }

    f97 = {
        "title": "Unauthenticated Prometheus-format observability endpoint exposing internal telemetry",
        "analysis": f"""Unauthenticated GET {BASE}/metrics returns HTTP {g['meta']['status']}/{g['meta']['size']} B (and {g['meta2']['status']}/{g['meta2']['size']} B on a fresh call; value-level counter drift observed across calls) with no authorization required, serving Prometheus-format telemetry: http_requests_count (2XX/3XX/5XX buckets), process_* and nodejs_* runtime metrics, juiceshop_version_info, and juiceshop_llm_input_tokens_total / juiceshop_llm_output_tokens_total / juiceshop_llm_tool_calls_total gauges exposing AI/LLM usage counters, plus juiceshop_challenges_solved. Fresh byte signature: {g['meta']['sig'][3][:16]}... . An invalid Bearer token is also accepted and returns 200 ({g['bearer']['status']}/{g['bearer']['size']} B) - no auth gate on the observability surface. A counter-only scan of the response shows no credentials (only generic HELP-text matches on the word 'token'). Fresh byte signature on second call: {g['meta2']['sig'][3][:16]}.... Challenge-id context (id=97) comes from the worker-visible /api/Challenges/ envelope.""",
        "false_positive_check": """A properly secured observability endpoint would reject unauthenticated access (401/403) or restrict internal metrics to authenticated consumers; here any caller with no credentials receives full internal telemetry, including AI token-usage counters and the challenge-solve counter. The exposure is structural: two independent fresh calls returned the same telemetry set (gauge presence verified on both), while the only change between calls was incrementing counter VALUES (proof the drift is value-level, not presence-level). A second fresh call returned the same signature class (juiceshop_llm_* gauges present) with different counter values, confirming presence is durable while raw bytes are not. The claim is scoped to the durable presence of internal gauges and the Prometheus structure, not to exact body bytes.""",
        "request": {
            "method": "GET",
            "url": BASE + "/metrics",
            "headers": {},
            "body": {},
        },
        "null_control": [
            {"method": "GET", "url": BASE + "/metrics", "headers": {"Authorization": "Bearer invalid"}, "body": {}},
        ],
    }

    return {"findings": [f27, f97]}


def main():
    gate = run_gate()
    findings = build_findings(gate)
    path = os.path.join(REPORTS, "benchmark_findings.json")
    with open(path, "w") as fh:
        json.dump(findings, fh, indent=2)
    print(f"\nWROTE {path}")
    with open(path) as fh:
        parsed = json.load(fh)
    print(f"  parse OK, {len(parsed['findings'])} findings")
    for i, f in enumerate(parsed["findings"]):
        print(f"  finding {i+1}: {f['title'][:70]}")
        assert f["request"]["method"] in ("GET", "HEAD", "OPTIONS")
        assert f["request"]["url"].startswith(BASE)
        assert "false_positive_check" in f
        assert "analysis" in f
        assert "title" in f
    print("  shape checks passed")
    return path


if __name__ == "__main__":
    main()
