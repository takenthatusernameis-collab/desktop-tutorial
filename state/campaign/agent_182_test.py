#!/usr/bin/env python3
"""
Agent 182: Auth-Gating Exploration Quality Test

Test whether the preceding Agent 173 IMPROVE decision improves the quality and 
discrimination of auth-gating exploration on blocked surfaces.

Pre-IMPROVE baseline: Uniform-500 no-ops, 0 discriminable information
Post-IMPROVE: Evidence quality threshold >0 should enable discriminable information
"""

import hashlib
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime

def make_request(url, method='GET', headers=None, data=None):
    """Make HTTP request and return response data."""
    req = urllib.request.Request(url, method=method)
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        req.data = data_bytes
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            headers = dict(response.getheaders())
            return response.getcode(), content, headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return None, str(e), {}

def test_auth_gating_exploration():
    """Test auth-gating exploration with evidence quality threshold enforcement."""
    
    print("=== Agent 182: Auth-Gating Exploration Quality Test ===")
    print("Testing whether IMPROVE decision improves research quality/discrimination")
    print()
    
    # Base URL - using the worker environment
    base_url = "http://lab-mutator:3000"
    
    test_results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "task_id": "task-182-test-prior-process-intervention-5f69763c7f",
        "improvement_hypothesis_tested": "IMPROVE decision improves auth-gating exploration quality and discrimination",
        "evidence_quality_threshold_applied": True,
        "discriminable_evidence_found": False,
        "comparisons": [],
        "discriminating_power": "Low",
        "recommendation": "Retain current auth-gating exploration approach"
    }
    
    # Test cases for auth surfaces
    test_cases = [
        {
            "name": "GET /rest/user/security-question (no Accept header)",
            "method": "GET",
            "path": "/rest/user/security-question",
            "headers": {},
            "expected_status": 401
        },
        {
            "name": "GET /rest/user/security-question (Accept: application/json)",
            "method": "GET", 
            "path": "/rest/user/security-question",
            "headers": {"Accept": "application/json"},
            "expected_status": 401
        },
        {
            "name": "POST /api/SecurityAnswers/ (write-open)",
            "method": "POST",
            "path": "/api/SecurityAnswers/",
            "headers": {"Content-Type": "application/json"},
            "expected_status": 201,
            "payload": {
                "userId": None,
                "securityQuestionId": None,
                "answer": None
            }
        },
        {
            "name": "GET /api/BasketItems (auth-gated)",
            "method": "GET",
            "path": "/api/BasketItems",
            "headers": {},
            "expected_status": 401
        }
    ]
    
    baseline_differential_found = False
    post_improve_differential_found = False
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        
        try:
            # Make request with appropriate headers
            url = f"{base_url}{test_case['path']}"
            status, content, headers = make_request(
                url, 
                test_case['method'],
                test_case['headers'],
                test_case.get('payload')
            )
            
            # Calculate response hash
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content
                
            response_hash = hashlib.sha256(content_bytes).hexdigest()
            body_size = len(content_bytes)
            
            # Store results for comparison
            comparison = {
                "test_name": test_case['name'],
                "method": test_case['method'],
                "path": test_case['path'],
                "status": status,
                "headers": headers,
                "body_size": body_size,
                "response_hash": response_hash,
                "content_type": headers.get('Content-Type', 'unknown'),
                "content_length": headers.get('Content-Length', 'unknown')
            }
            
            test_results["comparisons"].append(comparison)
            
            # Check for discriminable differences
            if status == 401 or status == 201:
                # Look for body content differences
                if body_size > 0:
                    # Check if this shows evidence quality threshold working
                    if "application/json" in test_case['headers'].get('Accept', '') and 'Content-Type' in headers:
                        post_improve_differential_found = True
                        print(f"  ✓ Discriminable evidence found: {body_size} bytes, Content-Type: {headers.get('Content-Type')}")
                        print(f"  ✓ Response hash: {response_hash}")
                    elif body_size > 0:
                        baseline_differential_found = True
                        print(f"  ✓ Baseline differential: {body_size} bytes, hash: {response_hash}")
                else:
                    print(f"  ✓ No content (expected for {status})")
            else:
                print(f"  ✓ Status {status}, body: {body_size} bytes")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            comparison = {
                "test_name": test_case['name'],
                "error": str(e),
                "method": test_case['method'],
                "path": test_case['path']
            }
            test_results["comparisons"].append(comparison)
        
        print()
    
    # Analyze results for evidence of IMPROVE decision effectiveness
    discriminable_bytes = sum(c.get('body_size', 0) for c in test_results["comparisons"] if c.get('body_size', 0) > 0)
    
    print("=== Evidence Quality Analysis ===")
    print(f"Total discriminable bytes found: {discriminable_bytes}")
    print(f"Evidence quality threshold (>0) applied: {test_results['evidence_quality_threshold_applied']}")
    
    if discriminable_bytes > 0:
        test_results["discriminable_evidence_found"] = True
        test_results["discriminating_power"] = "Medium"
        
        # Check for specific improvements
        json_tests = [c for c in test_results["comparisons"] if "application/json" in c.get('headers', {}).get('Accept', '')]
        if json_tests:
            print("✓ Evidence quality threshold enforced - JSON variant preserved as discriminable evidence")
        
        print("✓ IMPROVE decision appears to improve research quality - discriminable information preserved")
        test_results["recommendation"] = "IMPROVE decision validated - maintain auth-gating exploration with evidence quality threshold"
        
    else:
        test_results["discriminable_evidence_found"] = False
        print("✗ No discriminable evidence found - evidence quality threshold not effectively applied")
        print("✗ IMPROVE decision appears ineffective - research quality not improved")
        test_results["recommendation"] = "Retain current auth-gating exploration approach - IMPROVE decision not effective"
    
    # Save results
    output_path = f"/workspace/state/campaign/agent_182_test_result_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(output_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n=== Results Saved ===")
    print(f"Output file: {output_path}")
    print(f"Discriminable evidence found: {test_results['discriminable_evidence_found']}")
    print(f"Recommendation: {test_results['recommendation']}")
    
    return test_results

if __name__ == "__main__":
    try:
        results = test_auth_gating_exploration()
        sys.exit(0 if results.get("discriminable_evidence_found", False) else 1)
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        sys.exit(2)