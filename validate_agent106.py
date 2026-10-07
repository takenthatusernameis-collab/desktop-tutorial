#!/usr/bin/env python3
"""Validate Agent 106's research result and artifact completeness."""

import json
import os
import sys

def validate_agent106():
    print("Validating Agent 106 research result...")
    
    # Check RESULT.md exists and has proper fields
    result_path = "/workspace/state/campaign/RESULT.md"
    if not os.path.exists(result_path):
        print("ERROR: RESULT.md not found")
        return False
    
    with open(result_path, 'r') as f:
        content = f.read()
    
    # Check required field prefixes
    required_fields = [
        "OUTCOME_CLASS:",
        "TASK_ID:",
        "PRIMARY_QUESTION:",
        "BOTTLENECK:",
        "INFORMATION_GAP:",
        "BOUNDED_ACTION:",
        "DELIVERABLE:",
        "SUCCESS_EVIDENCE_CRITERION:",
        "STOP_CONDITION:",
        "OUT_OF_SCOPE:",
        "VERIFICATION_REQUIREMENT:",
        "CHANGED:",
        "VERIFIED:",
        "UNVERIFIED:",
        "OBSERVED_EFFECT:",
        "UNCERTAINTY_TARGETED:",
        "UNCERTAINTY_REDUCED:",
        "DECISION:",
        "NEXT:"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in content:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"ERROR: Missing required fields: {', '.join(missing_fields)}")
        return False
    
    # Check DECISION token validity
    lines = content.split('\n')
    decision_line = None
    for line in lines:
        if line.startswith("DECISION: "):
            decision_line = line.split(" ", 1)[1]
            break
    
    valid_decisions = ["IMPROVE", "RETAIN", "REJECT", "UNVERIFIED"]
    if decision_line not in valid_decisions:
        print(f"ERROR: Invalid DECISION token: {decision_line}")
        return False
    
    # Check artifact was created
    artifact_path = "/workspace/state/campaign/artifacts/agent106_validation_comparison.json"
    if not os.path.exists(artifact_path):
        print("ERROR: Required artifact not found")
        return False
    
    # Validate artifact structure
    try:
        with open(artifact_path, 'r') as f:
            artifact = json.load(f)
        
        required_artifact_fields = ["validation_comparison", "test_metadata"]
        for field in required_artifact_fields:
            if field not in artifact:
                print(f"ERROR: Missing required artifact field: {field}")
                return False
        
        # Check test metadata contains agent number
        if "Agent 106" not in artifact.get("test_metadata", {}).get("researcher", ""):
            print("ERROR: Artifact should reference Agent 106")
            return False
            
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in artifact: {e}")
        return False
    
    print("SUCCESS: Agent 106 validation completed")
    print(f"Result: {decision_line}")
    print(f"Next action: {content.split('NEXT:')[1].strip() if 'NEXT:' in content else 'Not found'}")
    return True

if __name__ == "__main__":
    success = validate_agent106()
    sys.exit(0 if success else 1)
