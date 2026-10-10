#!/usr/bin/env python3
"""
Controlled test to compare A39 breadth submission vs A40 mutation-feature submission
and determine if the A40 process decision improves research quality/discrimination.
"""

import hashlib
import json
import os
import urllib.request
import datetime

def test_a39_vs_a40_process_improvement():
    """
    Test whether the A40 mutation-feature + request-representation-matrix delta
    improves quality/discrimination compared to A39 breadth submission.
    """
    
    print("=== A39 vs A40 Process Decision Quality Comparison ===\n")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}")
    
    TARGET = "http://lab-mutator:3000"
    TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    
    # A39 Broad Approach (Rejected) - 5 findings across 5 security classes
    A39_MECHANISMS = {
        "id14_captcha": {
            "name": "CAPTCHA Cleartext Answer Leak",
            "path": "/rest/captcha",
            "method": "GET",
            "description": "GET /rest/captcha returns server-computed answer in cleartext"
        },
        "id1_memories": {
            "name": "Unauthenticated User-Object Exposure",
            "path": "/rest/memories", 
            "method": "GET",
            "description": "GET /rest/memories exposes other users' password hashes + emails"
        },
        "id7_security_question": {
            "name": "Security Question Disclosure",
            "path": "/rest/user/security-question",
            "method": "GET",
            "description": "GET /rest/user/security-question returns question JSON for existing accounts"
        },
        "id27_error_handling": {
            "name": "Raw Error Exposure",
            "path": "/rest/user/security-question",
            "method": "GET",
            "description": "Raw SQL error responses, inconsistent error handling"
        },
        "id97_metrics": {
            "name": "Unauthenticated Metrics Exposure", 
            "path": "/metrics",
            "method": "GET",
            "description": "GET /metrics exposes LLM telemetry and server info"
        }
    }
    
    # A40 Mutation-Feature Approach (Adopted) - 2 findings
    A40_MECHANISMS = {
        "id14_captcha": A39_MECHANISMS["id14_captcha"],  # CAPTCHA cleartext leak
        "id_challenge_filter": {
            "name": "Query-Filter Layer Enumeration",
            "path": "/api/Challenges/",
            "method": "GET",
            "description": "GET /api/Challenges/ with query filters exposes challenge metadata"
        }
    }
    
    def capture_probe(path, headers=None):
        """Send request and return status, body bytes, and size"""
        url = TARGET + path
        body = b""
        status = 0
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                body = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read()
        except Exception as e:
            status = 0
            body = str(e).encode()
        return status, body, len(body)
    
    def run_a39_broad_submission(output_path):
        """Run A39-style broad submission (5 mechanisms)"""
        print("Running A39 broad submission (5 mechanisms)...")
        
        probes = []
        for mech_id, mech in A39_MECHANISMS.items():
            probes.append({
                "name": f"A39_{mech_id}",
                "path": mech["path"],
                "method": mech["method"],
                "description": mech["description"]
            })
        
        lines = []
        lines.append(f"# A39 broad submission probe run - target={TARGET} utc={TS}")
        lines.append(f"# Mechanisms: {len(A39_MECHANISMS)} (5 security classes)")
        lines.append(f"# Note: A39 breadth delta (REJECTED with 0.0000 discovery)")
        lines.append("")
        
        anchors = {}
        
        for i, p in enumerate(probes, start=1):
            # Test with and without Accept header for differential evidence
            status1, body1, size1 = capture_probe(p["path"], {})
            status2, body2, size2 = capture_probe(p["path"], {"Accept": "application/json"})
            
            h1 = hashlib.sha256(body1).hexdigest()
            h2 = hashlib.sha256(body2).hexdigest()
            
            anchors[p["name"]] = {
                "baseline_body": h1,
                "variant_body": h2,
                "status_baseline": status1,
                "status_variant": status2,
                "body_size_baseline": size1,
                "body_size_variant": size2,
                "description": p["description"]
            }
            
            lines.append(f"## probe {i}: {p['name']}")
            lines.append(f"  description: {p['description']}")
            lines.append(f"  baseline (Accept:text/html): status={status1} size={size1} sha256={h1}")
            lines.append(f"  variant (Accept:application/json): status={status2} size={size2} sha256={h2}")
            lines.append(f"  differential: {'YES' if h1 != h2 else 'NO'}")
            lines.append("")
        
        # Write artifact to disk
        with open(output_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        
        print(f"   Wrote {output_path} ({os.path.getsize(output_path)} bytes)")
        
        return output_path, anchors
    
    def run_a40_mutation_submission(output_path):
        """Run A40-style mutation-feature submission (2 mechanisms)"""
        print("Running A40 mutation-feature submission (2 mechanisms)...")
        
        probes = []
        for mech_id, mech in A40_MECHANISMS.items():
            probes.append({
                "name": f"A40_{mech_id}",
                "path": mech["path"],
                "method": mech["method"], 
                "description": mech["description"]
            })
        
        lines = []
        lines.append(f"# A40 mutation-feature submission probe run - target={TARGET} utc={TS}")
        lines.append(f"# Mechanisms: {len(A40_MECHANISMS)} (targeted mutation features)")
        lines.append(f"# Note: A40 mutation-feature + request-representation-matrix delta (ADOPTED)")
        lines.append("")
        
        anchors = {}
        
        for i, p in enumerate(probes, start=1):
            status1, body1, size1 = capture_probe(p["path"], {})
            status2, body2, size2 = capture_probe(p["path"], {"Accept": "application/json"})
            
            h1 = hashlib.sha256(body1).hexdigest()
            h2 = hashlib.sha256(body2).hexdigest()
            
            anchors[p["name"]] = {
                "baseline_body": h1,
                "variant_body": h2,
                "status_baseline": status1,
                "status_variant": status2,
                "body_size_baseline": size1,
                "body_size_variant": size2,
                "description": p["description"]
            }
            
            lines.append(f"## probe {i}: {p['name']}")
            lines.append(f"  description: {p['description']}")
            lines.append(f"  baseline (Accept:text/html): status={status1} size={size1} sha256={h1}")
            lines.append(f"  variant (Accept:application/json): status={status2} size={size2} sha256={h2}")
            lines.append(f"  differential: {'YES' if h1 != h2 else 'NO'}")
            lines.append("")
        
        # Write artifact to disk
        with open(output_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        
        print(f"   Wrote {output_path} ({os.path.getsize(output_path)} bytes)")
        
        return output_path, anchors
    
    def analyze_process_improvement(a39_anchors, a40_anchors):
        """Analyze whether A40 improves quality/discrimination vs A39"""
        
        print("\n=== Process Improvement Analysis ===")
        
        # A39 Analysis
        a39_differentials = sum(1 for v in a39_anchors.values() if v["baseline_body"] != v["variant_body"])
        a39_differential_rate = a39_differentials / len(a39_anchors) if a39_anchors else 0
        
        a39_unique_bodies = len(set(v["baseline_body"] for v in a39_anchors.values()))
        a39_unique_variant_bodies = len(set(v["variant_body"] for v in a39_anchors.values()))
        
        # A40 Analysis
        a40_differentials = sum(1 for v in a40_anchors.values() if v["baseline_body"] != v["variant_body"])
        a40_differential_rate = a40_differentials / len(a40_anchors) if a40_anchors else 0
        
        a40_unique_bodies = len(set(v["baseline_body"] for v in a40_anchors.values()))
        a40_unique_variant_bodies = len(set(v["variant_body"] for v in a40_anchors.values()))
        
        print(f"A39 Broad Submission ({len(a39_anchors)} mechanisms):")
        print(f"   - Differential rate: {a39_differential_rate:.2f} ({a39_differentials}/{len(a39_anchors)})")
        print(f"   - Unique baseline bodies: {a39_unique_bodies}")
        print(f"   - Unique variant bodies: {a40_unique_variant_bodies}")
        print(f"   - Evidence diversity: {a39_unique_bodies + a39_unique_variant_bodies}")
        
        print(f"\nA40 Mutation-Feature Submission ({len(a40_anchors)} mechanisms):")
        print(f"   - Differential rate: {a40_differential_rate:.2f} ({a40_differentials}/{len(a40_anchors)})")
        print(f"   - Unique baseline bodies: {a40_unique_bodies}")
        print(f"   - Unique variant bodies: {a40_unique_variant_bodies}")
        print(f"   - Evidence diversity: {a40_unique_bodies + a40_unique_variant_bodies}")
        
        # Quality Discrimination Comparison
        print(f"\n=== Quality & Discrimination Comparison ===")
        
        # Differential power (higher is better)
        a39_differential_power = a39_differential_rate
        a40_differential_power = a40_differential_rate
        
        differential_improvement = ((a40_differential_power - a39_differential_power) / a39_differential_power * 100) if a39_differential_power > 0 else 0
        
        print(f"A39 Differential Power: {a39_differential_power:.2f}")
        print(f"A40 Differential Power: {a40_differential_power:.2f}")
        print(f"Differential Improvement: {differential_improvement:.1f}%")
        
        # Evidence Quality (higher diversity = better)
        a39_evidence_quality = a39_unique_bodies + a39_unique_variant_bodies
        a40_evidence_quality = a40_unique_bodies + a40_unique_variant_bodies
        
        evidence_improvement = ((a40_evidence_quality - a39_evidence_quality) / a39_evidence_quality * 100) if a39_evidence_quality > 0 else 0
        
        print(f"\nA39 Evidence Quality: {a39_evidence_quality}")
        print(f"A40 Evidence Quality: {a40_evidence_quality}")
        print(f"Evidence Quality Improvement: {evidence_improvement:.1f}%")
        
        # Efficiency (mechanisms per finding)
        a39_efficiency = len(a39_anchors) / 5  # 5 findings in A39
        a40_efficiency = len(a40_anchors) / 2  # 2 findings in A40
        
        efficiency_ratio = a40_efficiency / a39_efficiency if a39_efficiency > 0 else 0
        
        print(f"\nA39 Efficiency (mechanisms/finding): {a39_efficiency:.1f}")
        print(f"A40 Efficiency (mechanisms/finding): {a40_efficiency:.1f}")
        print(f"Efficiency Ratio (A40/A39): {efficiency_ratio:.1f}")
        
        # Determine if A40 process improves quality
        process_improves_quality = (
            a40_differential_power > a39_differential_power and  # Better discrimination
            a40_evidence_quality >= a39_evidence_quality and     # Same or better evidence quality
            a40_efficiency > a39_efficiency                      # Better efficiency
        )
        
        return {
            "a39": {
                "mechanisms": len(a39_anchors),
                "differential_power": a39_differential_power,
                "evidence_quality": a39_evidence_quality,
                "efficiency": a39_efficiency
            },
            "a40": {
                "mechanisms": len(a40_anchors),
                "differential_power": a40_differential_power,
                "evidence_quality": a40_evidence_quality,
                "efficiency": a40_efficiency
            },
            "differential_improvement": differential_improvement,
            "evidence_improvement": evidence_improvement,
            "efficiency_ratio": efficiency_ratio,
            "process_improves_quality": process_improves_quality
        }
    
    # Run the comparison
    a39_output = f"/workspace/state/campaign/agent_258_a39_broad_comparison_{TS}.txt"
    a40_output = f"/workspace/state/campaign/agent_258_a40_mutation_comparison_{TS}.txt"
    
    a39_result, a39_anchors = run_a39_broad_submission(a39_output)
    a40_result, a40_anchors = run_a40_mutation_submission(a40_output)
    
    # Apply disk-existence gate
    print(f"\n=== Applying Disk-Existence Verification Gates ===")
    
    a39_gate_pass = (os.path.exists(a39_output) and os.path.getsize(a39_output) > 0)
    a40_gate_pass = (os.path.exists(a40_output) and os.path.getsize(a40_output) > 0)
    
    print(f"A39 artifact exists and non-empty: {'✅ PASS' if a39_gate_pass else '❌ FAIL'}")
    print(f"A40 artifact exists and non-empty: {'✅ PASS' if a40_gate_pass else '❌ FAIL'}")
    
    if not (a39_gate_pass and a40_gate_pass):
        print("❌ Disk-existence gate failed")
        return None
    
    # Analyze process improvement
    analysis = analyze_process_improvement(a39_anchors, a40_anchors)
    
    print(f"\n=== FINAL ASSESSMENT ===")
    
    if analysis["process_improves_quality"]:
        print("✅ THE A40 PROCESS DECISION IMPROVES RESEARCH QUALITY AND DISCRIMINATION")
        print(f"   - Differential power improvement: {analysis['differential_improvement']:.1f}%")
        print(f"   - Evidence quality improvement: {analysis['evidence_improvement']:.1f}%")
        print(f"   - Efficiency ratio: {analysis['efficiency_ratio']:.1f}x better")
        decision = "IMPROVE"
        outcome_class = "NEW_EVIDENCE"
    else:
        print("❌ THE A40 PROCESS DECISION DOES NOT IMPROVE RESEARCH QUALITY")
        decision = "REJECT"
        outcome_class = "NO_NEW_INFORMATION"
    
    # Create deliverable
    deliverable = {
        "task_id": "task-258-test-prior-process-intervention-dfb14c881b",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
        "outcome_class": outcome_class,
        "decision": decision,
        "primary_question": "Does the preceding process decision improve the quality or discrimination of the next bounded research action?",
        "hypothesis_tested": "The A40 mutation-feature + request-representation-matrix delta improves quality/discrimination compared to the A39 breadth submission",
        "evidence_gathered": [
            {
                "observation": f"A39 broad submission: {analysis['a39']['mechanisms']} mechanisms, {analysis['a39']['differential_power']:.2f} differential power",
                "significance": "Baseline",
                "supports": "Context",
                "reason": "A39 breadth delta was rejected with 0.0000 discovery"
            },
            {
                "observation": f"A40 mutation-feature submission: {analysis['a40']['mechanisms']} mechanisms, {analysis['a40']['differential_power']:.2f} differential power",
                "significance": "Test condition",
                "supports": "Process evaluation",
                "reason": "A40 mutation-feature + request-representation-matrix delta was adopted"
            },
            {
                "observation": f"Differential power improvement: {analysis['differential_improvement']:.1f}%",
                "significance": "Key measure",
                "supports": "A40 superiority",
                "reason": "Higher differential power indicates better discrimination"
            },
            {
                "observation": f"Evidence quality improvement: {analysis['evidence_improvement']:.1f}%",
                "significance": "Key measure", 
                "supports": "A40 superiority",
                "reason": "Higher evidence diversity indicates better information gain"
            },
            {
                "observation": f"Efficiency ratio: {analysis['efficiency_ratio']:.1f}x",
                "significance": "Efficiency measure",
                "supports": "A40 superiority",
                "reason": "Better mechanisms per finding indicates process improvement"
            }
        ],
        "discriminating_power": f"{analysis['a40']['differential_power']:.2f}" if decision == "IMPROVE" else f"{analysis['a39']['differential_power']:.2f}",
        "recommendation": "IMPROVE" if decision == "IMPROVE" else "REJECT"
    }
    
    # Write deliverable
    deliverable_path = f"/workspace/state/campaign/agent_258_deliverable_{TS}.json"
    with open(deliverable_path, "w") as f:
        json.dump(deliverable, f, indent=2)
    
    print(f"\n✅ DELIVERABLE CREATED: {deliverable_path}")
    print(f"   Outcome Class: {deliverable['outcome_class']}")
    print(f"   Decision: {deliverable['decision']}")
    print(f"   Artifact Size: {os.path.getsize(deliverable_path)} bytes")
    
    return deliverable

if __name__ == "__main__":
    print("=" * 90)
    print("AGENT 258: A39 vs A40 Process Decision Quality Comparison")
    print("Testing whether A40 mutation-feature submission improves")
    print("quality/discrimination over A39 breadth submission")
    print("=" * 90)
    
    result = test_a39_vs_a40_process_improvement()
    
    if result:
        print(f"\n🎉 SUCCESS: Process decision comparison completed successfully")
        if result["decision"] == "IMPROVE":
            print(f"   The A40 mutation-feature + request-representation-matrix delta")
            print(f"   IMPROVES research quality by providing better discrimination")
            print(f"   and evidence efficiency compared to A39 breadth submission.")
        else:
            print(f"   The A40 process decision does not improve research quality over A39.")
        exit(0)
    else:
        print(f"\n❌ FAILURE: Could not complete the comparison")
        exit(1)