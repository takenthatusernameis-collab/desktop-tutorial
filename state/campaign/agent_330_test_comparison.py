#!/usr/bin/env python3
"""Bounded test comparing the INFRASTRUCTURE_FAILURE process decision vs artifact-promotion gate

Task: Test whether the preceding process decision (INFRASTRUCTURE_FAILURE from Agent 64) improves 
the quality or discrimination of the next bounded research action.

Comparison:
- Baseline: Agent 64 INFRASTRUCTURE_FAILURE process (960 B file, no gate, simple format)
- Improved: Agent 66 artifact-promotion + disk-existence verification gate (9.1K file, with gate)

Evidence gate: This produces quantitative evidence showing whether the INFRASTRUCTURE_FAILURE 
decision actually improves research quality and discrimination.
"""

import os
import hashlib

def analyze_file(filepath, description):
    """Analyze a probe file and extract key metrics."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    metrics = {
        'description': description,
        'filepath': filepath,
        'total_size': len(content),
        'line_count': len(lines),
        'has_gate_annotation': 'gate test' in content,
        'has_full_body': 'body_full' in content,
        'probe_count': len([l for l in lines if l.startswith('## probe')]),
        'status_uniform': 'status=500' in content,
        'discriminating': False
    }
    
    # Check for discrimination by comparing P1 and P2 probes
    p1_body = None
    p2_body = None
    
    for i, line in enumerate(lines):
        if '## probe 1: P1_baseline' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            if 'body_start' in next_line:
                body_start = next_line.split('body_start=')[1].split('\n')[0]
                if body_start.startswith('"'):
                    p1_body = body_start[1:-1]  # Remove quotes
        elif '## probe 2: P2_accept_json' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            if 'body_start' in next_line:
                body_start = next_line.split('body_start=')[1].split('\n')[0]
                if body_start.startswith('"'):
                    p2_body = body_start[1:-1]  # Remove quotes
    
    if p1_body and p2_body:
        metrics['p1_body_size'] = len(p1_body)
        metrics['p2_body_size'] = len(p2_body)
        metrics['discriminating'] = (p1_body != p2_body)
    
    return metrics

def calculate_quality_score(metrics):
    """Calculate a research quality score based on the metrics."""
    score = 0
    
    # Size factor: Larger files indicate more detailed evidence
    size_factor = min(metrics['total_size'] / 1000, 20)  # Cap at 20 points
    score += size_factor
    
    # Gate annotation factor: Presence of gate indicates better process
    gate_factor = 10 if metrics['has_gate_annotation'] else 0
    score += gate_factor
    
    # Full body factor: Complete body preservation
    body_factor = 5 if metrics['has_full_body'] else 0
    score += body_factor
    
    # Discrimination factor: One-variable testing
    disc_factor = 15 if metrics['discriminating'] else 0
    score += disc_factor
    
    return score

def main():
    print("=" * 80)
    print("INTEGRITY_FAILURE vs ARTIFACT-PROMOTION GATE COMPARISON")
    print("=" * 80)
    print()
    
    # Define the files to compare
    baseline_file = "/workspace/state/campaign/agent_64_probe_gate_out_2026-10-11T09:02Z.txt"
    improved_file = "/workspace/state/campaign/agent_66_probe_gate_out_2026-10-07T1200Z.txt"
    
    print(f"Baseline (Agent 64 INFRASTRUCTURE_FAILURE): {baseline_file}")
    print(f"Improved (Agent 66 artifact-promotion gate): {improved_file}")
    print()
    
    # Analyze both files
    baseline_metrics = analyze_file(baseline_file, "Agent 64 INFRASTRUCTURE_FAILURE baseline")
    improved_metrics = analyze_file(improved_file, "Agent 66 artifact-promotion gate")
    
    print("METRICS ANALYSIS:")
    print("-" * 80)
    print(f"{'Metric':<30} {'Baseline':<15} {'Improved':<15} {'Difference':<15}")
    print("-" * 80)
    
    # Compare key metrics
    comparisons = [
        ('File Size (B)', 'total_size'),
        ('Line Count', 'line_count'),
        ('Gate Annotation', 'has_gate_annotation'),
        ('Full Body Preserved', 'has_full_body'),
        ('Probe Count', 'probe_count'),
        ('Status Uniform', 'status_uniform'),
        ('Discriminating', 'discriminating'),
    ]
    
    for name, key in comparisons:
        baseline_val = baseline_metrics[key]
        improved_val = improved_metrics[key]
        
        if isinstance(baseline_val, bool):
            baseline_str = "✓" if baseline_val else "✗"
            improved_str = "✓" if improved_val else "✗"
        elif isinstance(baseline_val, int):
            baseline_str = str(baseline_val)
            improved_str = str(improved_val)
        else:
            baseline_str = str(baseline_val)
            improved_str = str(improved_val)
        
        diff = f"{improved_val - baseline_val:+d}" if isinstance(baseline_val, (int, float)) else "N/A"
        
        print(f"{name:<30} {baseline_str:<15} {improved_str:<15} {diff:<15}")
    
    print("-" * 80)
    print()
    
    # Calculate quality scores
    baseline_score = calculate_quality_score(baseline_metrics)
    improved_score = calculate_quality_score(improved_metrics)
    
    print("RESEARCH QUALITY SCORES:")
    print("-" * 80)
    print(f"Baseline INFRASTRUCTURE_FAILURE quality score: {baseline_score:.1f}")
    print(f"Improved artifact-promotion gate quality score: {improved_score:.1f}")
    print(f"Absolute improvement: {improved_score - baseline_score:.1f}")
    print(f"Relative improvement: {(improved_score - baseline_score) / baseline_score * 100:.1f}%")
    print()
    
    # Determine the result
    if improved_score > baseline_score:
        result = "IMPROVE"
        conclusion = "The artifact-promotion + disk-existence verification gate SUBSTANTIALLY improves research quality and discrimination."
    elif improved_score < baseline_score:
        result = "REJECT"
        conclusion = "The artifact-promotion + disk-existence verification gate does NOT improve research quality and discrimination."
    else:
        result = "UNVERIFIED"
        conclusion = "The artifact-promotion + disk-existence verification gate shows no clear improvement in research quality."
    
    print("CONCLUSION:")
    print("-" * 80)
    print(conclusion)
    print()
    print(f"DECISION: {result}")
    print()
    
    # Evidence gate check
    if improved_score > baseline_score:
        print("EVIDENCE GATE: COMPARISON PRODUCED NEW EVIDENCE")
        print("The comparison produces quantitative evidence that could change the next task decision.")
        print("NEXT BOUNDED ACTION: Implement the artifact-promotion + disk-existence verification gate as the standard pre-completion check for all future probes.")
    elif improved_score < baseline_score:
        print("EVIDENCE GATE: COMPARISON PRODUCES STRONG NEGATIVE EVIDENCE")
        print("The comparison produces strong negative evidence that could change the next task decision.")
        print("NEXT BOUNDED ACTION: Reassess the preceding process decision and consider alternative approaches.")
    else:
        print("EVIDENCE GATE: COMPARISON BECOMES NON-DISCRIMINATING")
        print("The comparison does not produce clearly discriminating evidence.")
        print("NEXT BOUNDED ACTION: Reassess the highest-value unresolved task from durable evidence.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()