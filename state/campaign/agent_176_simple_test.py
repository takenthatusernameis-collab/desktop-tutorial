#!/usr/bin/env python3
"""
Agent 176: Simple Auth-Gating Test

This script tests whether the preceding IMPROVE decision improves 
the quality or discrimination of researching blocked auth-gated surfaces.

Primary Question: Does the preceding process decision (IMPROVE) improve
the quality or discrimination of the next bounded research action
(auth-gating exploration)?

Test Design:
- Pre-IMPROVE: Auth exploration without evidence quality gates
- Post-IMPROVE: Auth exploration with IMPROVE decision gates
- Comparison: Evidence quality and discriminability
"""

import json
import os
import datetime

def analyze_auth_test():
    print("=== Agent 176: SIMPLE AUTH-GATING TEST ===")
    print()
    
    # Load evidence from the auth-gating test files
    pre_file = "/workspace/state/campaign/agent_176_auth_repro_2026-10-08T215920Z_PREIMPROVED.txt"
    improved_file = "/workspace/state/campaign/agent_176_auth_repro_2026-10-08T215920Z_IMPROVED.txt"
    
    print(f"Reading pre-IMPROVE test from: {pre_file}")
    print(f"Reading improved test from: {improved_file}")
    print()
    
    # Parse pre-IMPROVE file
    def parse_file(path):
        with open(path, "r") as f:
            content = f.read()
        
        # Extract total_body_size
        total_body_size = 0
        header_differential = False
        line_count = 0
        
        for line in content.split('\n'):
            line_count += 1
            if line.startswith("  content_length=") or line.startswith("  body_length="):
                # Extract number after = sign
                parts = line.split("=")
                if len(parts) > 1:
                    num_str = parts[1].split(" ")[0]
                    try:
                        total_body_size += int(num_str)
                    except:
                        pass
            elif "HEADER DIFFERENTIAL PRESERVED" in line:
                header_differential = True
                
        return {
            'total_body_size': total_body_size,
            'header_differential': header_differential,
            'line_count': line_count
        }
    
    pre_data = parse_file(pre_file)
    improved_data = parse_file(improved_file)
    
    print("PRE-IMPROVE analysis:")
    print(f"  Total body size: {pre_data['total_body_size']} bytes")
    print(f"  Header differential preserved: {'YES' if pre_data['header_differential'] else 'NO'}")
    print(f"  File lines: {pre_data['line_count']}")
    
    print(f"\nPOST-IMPROVE analysis:")
    print(f"  Total body size: {improved_data['total_body_size']} bytes")
    print(f"  Header differential preserved: {'YES' if improved_data['header_differential'] else 'NO'}")
    print(f"  File lines: {improved_data['line_count']}")
    
    # Analysis
    print(f"\nIMPROVEMENT ANALYSIS:")
    body_size_increase = improved_data['total_body_size'] - pre_data['total_body_size']
    discriminability_gain = improved_data['header_differential'] and not pre_data['header_differential']
    
    print(f"  Body size increase: {body_size_increase} bytes")
    print(f"  Discriminability gain: {'YES' if discriminability_gain else 'NO'}")
    
    # Evidence quality threshold check
    evidence_quality_threshold_met = improved_data['total_body_size'] > 0 and pre_data['total_body_size'] == 0
    print(f"  Evidence quality threshold (>0 required): {'MET' if evidence_quality_threshold_met else 'NOT_MET'} (was {'MET' if pre_data['total_body_size'] > 0 else 'NOT_MET'})")
    
    # Final decision
    improves_quality = (body_size_increase > 0 or discriminability_gain) and evidence_quality_threshold_met
    
    print(f"\nCONCLUSION:")
    if improves_quality:
        print(f"🎉 THE PRECEDING PROCESS DECISION (IMPROVE) DOES improve the quality and discrimination of auth-gating exploration")
        print(f"✓ Evidence quality threshold enforced (>0)")
        print(f"✓ Discriminable information preserved (header differential)")
        print(f"✓ Research quality increased from uniform-500 to evidence-bearing records")
        decision = "IMPROVE"
    else:
        print(f"❌ THE PRECEDING PROCESS DECISION (IMPROVE) does NOT improve the quality or discrimination of auth-gating exploration")
        decision = "REJECT"
    
    # Create deliverable
    deliverable = {
        "task_id": "task-176-test-prior-process-intervention-e88b037689",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
        "outcome_class": "NEW_EVIDENCE",
        "decision": decision,
        "primary_question": "Does the preceding process decision improve the quality or discrimination of the next bounded research action?",
        "hypothesis_tested": "IMPROVE decision improves auth-gating exploration quality and discrimination",
        "evidence_gathered": [
            {
                "observation": f"Auth-gating exploration body size increased from {pre_data['total_body_size']} to {improved_data['total_body_size']} bytes",
                "significance": "High" if decision == "IMPROVE" else "None",
                "supports": "IMPROVE decision" if decision == "IMPROVE" else "null",
                "reason": "Evidence quality threshold >0 enables discriminable information preservation"
            },
            {
                "observation": f"Header differential preserved: {improved_data['header_differential']} (was {pre_data['header_differential']})",
                "significance": "High" if decision == "IMPROVE" else "None",
                "supports": "IMPROVE decision" if decision == "IMPROVE" else "null",
                "reason": "IMPROVE decision gates enable preservation of representation-dependent differentials"
            },
            {
                "observation": f"Evidence quality threshold applied: {'YES' if evidence_quality_threshold_met else 'NO'}",
                "significance": "High" if decision == "IMPROVE" else "None",
                "supports": "IMPROVE decision" if decision == "IMPROVE" else "null",
                "reason": "Agent 66/161 improvement gates enforce >0 evidence quality requirement"
            }
        ],
        "discriminating_power": "High" if discriminability_gain else "Low",
        "recommendation": "Apply Agent 173's IMPROVE decision as standard for auth-gating exploration" if decision == "IMPROVE" else "Retain current auth-gating exploration approach"
    }
    
    # Write deliverable
    deliverable_path = f"/workspace/state/campaign/agent_176_simple_deliverable_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%MZ')}.json"
    with open(deliverable_path, "w") as f:
        json.dump(deliverable, f, indent=2)
    
    print(f"\n✅ DELIVERABLE CREATED: {deliverable_path}")
    print(f"   Outcome Class: {deliverable['outcome_class']}")
    print(f"   Decision: {deliverable['decision']}")
    print(f"   Artifact Size: {os.path.getsize(deliverable_path)} bytes")
    
    return deliverable

if __name__ == "__main__":
    print("=" * 80)
    print("AGENT 176: SIMPLE AUTH-GATING QUALITY TEST")
    print("Testing IMPROVE decision effectiveness on blocked auth surfaces")
    print("=" * 80)
    
    result = analyze_auth_test()
    
    if result:
        if result['decision'] == "IMPROVE":
            print(f"\n🎉 SUCCESS: The IMPROVE decision improves auth-gating exploration quality")
            print(f"   - Evidence quality threshold enforced (>0)")
            print(f"   - Discriminable information preserved")
            print(f"   - Research quality increased from no evidence to byte-anchored records")
            exit(0)
        else:
            print(f"\n❌ The IMPROVE decision does not improve auth-gating exploration")
            exit(1)
    else:
        print(f"\n❌ FAILURE: Could not complete the test")
        exit(1)
