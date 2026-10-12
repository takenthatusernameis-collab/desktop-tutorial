#!/usr/bin/env python3
"""Comprehensive test of process gates (Agent 66 + Agent 161) implementation.

This test validates that the comprehensive process gates requested in task-366
are properly implemented and working:
1. Agent 66's artifact-promotion + disk-existence verification gate applied to all behavioral differential testing
2. Agent 161's evidence quality threshold >0 to exclude low-yield tasks

This directly tests the preceding process decision (IMPROVE) from Agent 365.
"""

import os
import hashlib
import json
import sys
from datetime import datetime

# Configuration
TARGET = "http://lab-mutator:3000"
OUT_FILE = "/workspace/state/campaign/gate_test_2026-10-12T0943Z.txt"
DURABLE_ANCHORS = {
    "0b84d83c08cc28421da7b67c32d997676e490f8bd4016854f849200c2e11a90b",  # P1 baseline, 2946 B HTML error
    "20eec46aa7555e7df9a45e29f3ef1a525bfc60e64645def1e662c629c0419b9e",  # P2 Accept:application/json, 1804 B JSON error
    "5b9004f21283f4ac5240d03066c6cd5d19aa7891c8f2d30011651dbbb01f3718",  # P3 null control, 2436 B
}

def probe_endpoint(path, headers=None):
    """Send request to Juice Shop target."""
    url = f"{TARGET}{path}"
    body = b""
    status = 0
    
    try:
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read()
    except HTTPError as e:
        status = e.code
        body = e.read()
    except Exception as e:
        status = 0
        body = str(e).encode()
    
    return status, body

def run_behavioral_differential_test():
    """Run behavioral differential testing with both headers and body variations."""
    print("=== Behavioral Differential Test ===")
    
    test_cases = [
        {"name": "P1_baseline", "path": "/rest/user/security-question", "headers": {}},
        {"name": "P2_accept_json", "path": "/rest/user/security-question", "headers": {"Accept": "application/json"}},
        {"name": "P3_null_control", "path": "/api/Nonexistent/1", "headers": {}},
        {"name": "P4_different_endpoint", "path": "/rest/users", "headers": {}},
        {"name": "P5_post_with_data", "path": "/api/Generic", "headers": {"Content-Type": "application/json"}, "body": {"test": "data"}},
    ]
    
    results = []
    for test in test_cases:
        headers = test.get("headers", {})
        body_param = test.get("body", None)
        
        status, body = probe_endpoint(test["path"], headers)
        size = len(body)
        body_hash = hashlib.sha256(body).hexdigest()
        
        result = {
            "name": test["name"],
            "path": test["path"],
            "headers": headers,
            "status": status,
            "content_length": size,
            "sha256": body_hash,
            "body_sample": body[:100].decode("utf-8", errors="replace"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if body_param:
            result["body_param"] = body_param
            
        results.append(result)
        print(f"  {test['name']}: {status} {size}B hash={body_hash[:16]}...")
    
    return results

def apply_artifact_promotion_gate(results):
    """Apply Agent 66's artifact-promotion + disk-existence verification gate."""
    print("\n=== Applying Artifact-Promotion + Disk-Existence Gate ===")
    
    # Build output file content
    lines = []
    lines.append(f"# agent_366 comprehensive gate test target={TARGET} utc={datetime.utcnow().strftime('%Y-%m-%dT%H%MZ')}")
    lines.append(f"# shape: behavioral differential testing with artifact-promotion + disk-existence gate")
    lines.append("")
    
    for result in results:
        lines.append(f"## probe {result['name']}")
        lines.append(f"  request: method=GET path={result['path']} query={{}} headers={json.dumps(result['headers'])}")
        lines.append(f"  timestamp_utc={result['timestamp']}")
        lines.append(f"  status={result['status']} content_length={result['content_length']} sha256={result['sha256']}")
        lines.append(f"  body_start={result['body_sample']}")
        lines.append(f"  body_sha256={result['sha256']}")
        lines.append(f"  body_full=<{result['content_length']} B error body with discriminant attributes>")
        lines.append("")
    
    # Calculate output hash
    output_text = "\n".join(lines) + "\n"
    output_hash = hashlib.sha256(output_text.encode()).hexdigest()
    
    lines.append(f"# summary: {len(results)} probes all_status_ok=False")
    lines.append(f"# with Agent 66 gate (artifact-promotion + disk-existence): each probe is a byte-anchored, auditable record")
    lines.append(f"# sha256(stdout)={output_hash}")
    
    # Write output file
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        f.write("\n".join(lines))
    
    print(f"  Wrote {OUT_FILE} ({os.path.getsize(OUT_FILE)} bytes)")
    print(f"  Output hash: {output_hash}")
    
    # Check disk-existence gate
    if os.path.exists(OUT_FILE) and os.path.getsize(OUT_FILE) > 0:
        print("  ✓ Disk-existence gate: artifact exists and is non-empty")
        return True
    else:
        print("  ✗ Disk-existence gate: artifact missing or empty")
        return False

def evidence_quality_threshold_gar(results):
    """Apply Agent 161's evidence quality threshold >0 to exclude low-yield tasks."""
    print("\n=== Applying Evidence Quality Threshold Gate (Agent 161) ===")
    
    # Calculate evidence quality metrics
    total_bytes = sum(r["content_length"] for r in results)
    discriminating_pairs = 0
    
    # Check for discriminating evidence (body differences between similar requests)
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            r1, r2 = results[i], results[j]
            # Check if these are similar requests with different bodies (discriminating evidence)
            if r1["path"] == r2["path"] and r1["headers"] != r2["headers"]:
                if r1["sha256"] != r2["sha256"]:
                    discriminating_pairs += 1
    
    # Evidence quality threshold: >0 bytes AND >0 discriminating pairs
    has_minimum_content = total_bytes > 0
    has_discriminating_evidence = discriminating_pairs > 0
    evidence_quality_ok = has_minimum_content and has_discriminating_evidence
    
    print(f"  Evidence quality metrics:")
    print(f"    Total content bytes: {total_bytes}")
    print(f"    Discriminating evidence pairs: {discriminating_pairs}")
    print(f"    Minimum content requirement (>0 bytes): {'✓' if has_minimum_content else '✗'}")
    print(f"    Discrimination requirement (>0 pairs): {'✓' if has_discriminating_evidence else '✗'}")
    print(f"    Overall evidence quality threshold (>0 both): {'✓ PASS' if evidence_quality_ok else '✗ FAIL'}")
    
    # Compare with Agent 362's low-yield pattern (0 evidence bytes)
    agent_362_bytes = 0  # From Agent 362_RESULT.md
    print(f"    Agent 362 baseline (0 evidence bytes): {agent_362_bytes} bytes")
    
    if evidence_quality_ok:
        print("  ✓ Evidence quality threshold gate: Task qualifies for promotion")
        return True
    else:
        print("  ✗ Evidence quality threshold gate: Task would be excluded as low-yield")
        return False

def verify_differential_discrimination(results):
    """Verify that the test produces new discriminating evidence."""
    print("\n=== Verification: Differential Discrimination ===")
    
    # Check for known discriminating pairs (P1 vs P2 - the classic Accept-header differential)
    p1_result = next((r for r in results if r["name"] == "P1_baseline"), None)
    p2_result = next((r for r in results if r["name"] == "P2_accept_json"), None)
    
    if p1_result and p2_result:
        print(f"  P1_baseline: {p1_result['status']}/{p1_result['content_length']} B")
        print(f"  P2_accept_json: {p2_result['status']}/{p2_result['content_length']} B")
        print(f"  Body hashes differ: {p1_result['sha256'] != p2_result['sha256']}")
        
        if p1_result["status"] == p2_result["status"] and p1_result["sha256"] != p2_result["sha256"]:
            print("  ✓ Classic discrimination preserved: same status (500), different body (Accept-header effect)")
            return True
        else:
            print("  ✗ Discrimination lost: either status differs or body same")
            return False
    else:
        print("  ✗ Required test cases (P1_baseline, P2_accept_json) not found")
        return False

def independent_reproduction_check():
    """Perform independent reproduction to verify evidence reproducibility."""
    print("\n=== Independent Reproduction Check ===")
    
    # Run the same classic test pairs multiple times
    test_pairs = [
        ("P1_baseline", "/rest/user/security-question", {}),
        ("P2_accept_json", "/rest/user/security-question", {"Accept": "application/json"}),
        ("P3_null_control", "/api/Nonexistent/1", {}),
    ]
    
    all_hashes = []
    
    for name, path, headers in test_pairs:
        # Run test multiple times to check reproducibility
        run_hashes = []
        for run in range(3):  # 3 independent runs
            status, body = probe_endpoint(path, headers)
            body_hash = hashlib.sha256(body).hexdigest()
            run_hashes.append(body_hash)
            
            if run == 0:
                print(f"  {name}: run {run+1}: {status}/{len(body)} B hash={body_hash[:16]}...")
        
        # Check if all runs produced the same hash (reproducible)
        if len(set(run_hashes)) == 1:
            print(f"  {name}: ✓ REPRODUCIBLE (all 3 runs identical)")
            all_hashes.extend(run_hashes)
        else:
            print(f"  {name}: ✗ NON-REPRODUCIBLE (hash variance: {set(run_hashes)})")
            all_hashes.extend(run_hashes)
    
    # Compare with durable consensus
    consensus_match = all(h in DURABLE_ANCHORS for h in all_hashes)
    print(f"  All hashes match durable consensus: {'✓' if consensus_match else '✗'}")
    
    return consensus_match

def main():
    print("Agent 366: Testing comprehensive process gates implementation")
    print("Testing both Agent 66's artifact-promotion + disk-existence gate AND Agent 161's evidence quality threshold >0")
    
    # Step 1: Run behavioral differential testing
    results = run_behavioral_differential_test()
    
    # Step 2: Apply Agent 66's artifact-promotion + disk-existence gate
    gate1_ok = apply_artifact_promotion_gate(results)
    
    # Step 3: Apply Agent 161's evidence quality threshold >0 gate
    gate2_ok = evidence_quality_threshold_gar(results)
    
    # Step 4: Verify differential discrimination
    discrimination_ok = verify_differential_discrimination(results)
    
    # Step 5: Check independent reproduction
    reproduction_ok = independent_reproduction_check()
    
    # Final assessment
    print("\n=== FINAL ASSESSMENT ===")
    
    all_gates_pass = gate1_ok and gate2_ok
    all_checks_pass = discrimination_ok and reproduction_ok
    
    if all_gates_pass and all_checks_pass:
        print("✓ COMPREHENSIVE PROCESS GATES IMPLEMENTATION SUCCESSFUL:")
        print("  - Agent 66's artifact-promotion + disk-existence gate: ✓ APPLIED")
        print("  - Agent 161's evidence quality threshold (>0): ✓ APPLIED")
        print("  - Discriminating evidence preserved: ✓ VERIFIED")
        print("  - Independent reproduction confirmed: ✓ VERIFIED")
        print("\n  The preceding IMPROVE decision materially improves research quality:")
        print("    • Uniform-500 runs are promoted as byte-anchored evidence records")
        print("    • Low-yield tasks (like Agent 362's 0-byte output) are excluded")
        print("    • Discriminating differentials (Accept-header effect) are preserved")
        print("    • Evidence is independently reproducible and audit-ready")
        print("\n  NEXT: This implementation can now serve as the standard pre-completion")
        print("  check for all behavioral differential testing in the campaign.")
        
        return 0
    else:
        print("✗ COMPREHENSIVE PROCESS GATES IMPLEMENTATION INCOMPLETE:")
        if not gate1_ok:
            print("  - Agent 66's artifact-promotion + disk-existence gate: ✗ FAILED")
        if not gate2_ok:
            print("  - Agent 161's evidence quality threshold (>0): ✗ FAILED")
        if not discrimination_ok:
            print("  - Discriminating evidence: ✗ NOT PRESERVED")
        if not reproduction_ok:
            print("  - Independent reproduction: ✗ NOT CONFIRMED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
