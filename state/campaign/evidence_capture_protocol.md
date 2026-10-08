# Enhanced Evidence Capture Protocol

## Purpose
Standardized capture and preservation of empirical evidence for all research activities, including process-comparison tests.

## Core Principles

### 1. Multi-Layer Persistence
Evidence is captured through three redundant pathways:
- **Primary Path**: Standard result-memo infrastructure
- **Proxy Path**: Enhanced proxy infrastructure (PROXI_INFRASTRUCTURE_FIX.py + infrastructure_fix.py)
- **Independent Path**: Standalone artifact preservation

### 2. Standardized Format
All evidence artifacts follow this structure:
```json
{
  "evidence_id": "unique_identifier",
  "timestamp": "UTC ISO 8601",
  "researcher": "agent_identifier",
  "task_id": "controller_assigned_task_id",
  "outcome_class": "NEW_EVIDENCE|NEW_HYPOTHESIS|FALSIFIED|NO_NEW_INFORMATION|INFRASTRUCTURE_FAILURE",
  "primary_question": "research_question_text",
  "evidence_type": "empirical_test|process_comparison|independent_reproduction",
  "quality_metrics": {
    "precision": "percentage_0-100",
    "discriminative_power": "percentage_0-100", 
    "independent_verification": "VERIFIED|PARTIAL|FAILED",
    "false_positive_rate": "percentage_0-100"
  },
  "methodology": "detailed_description",
  "artifacts": [
    {
      "artifact_id": "unique_id",
      "type": "test_output|comparison_result|validation_data",
      "path": "file_path",
      "hash": "SHA256_hash",
      "size": "bytes",
      "format": "json|text|binary"
    }
  ],
  "findings": ["key_discovery_1", "key_discovery_2"],
  "conclusion": "decision_summary",
  "reproducibility_status": "REPRODUCIBLE|PARTIAL|FAILED",
  "cross_reference_ids": ["linked_artifact_1", "linked_artifact_2"],
  "infrastructure_status": "primary_success|proxy_success|standalone_only"
}
```

### 3. Quality Gates
Before evidence is accepted, it must pass:
- **Structural Validation**: Valid JSON format and required fields
- **Hash Verification**: SHA256 hash integrity check
- **Cross-Reference Validation**: All referenced artifacts exist
- **Reproduction Validation**: Independent verification (when applicable)
- **Discrimination Assessment**: Evidence must discriminate between competing hypotheses

### 4. Storage Strategy

#### Primary Storage (Standard)
- `state/campaign/evidence/primary/` - Normal result-memo pathway
- JSON format with full metadata
- Automated integrity verification

#### Proxy Storage (Enhanced)
- `state/campaign/evidence/proxy/` - Proxy infrastructure fallback
- Compatible with PROXI_INFRASTRUCTURE_FIX.py
- Structured format for cross-validation

#### Independent Storage (Standalone)
- `state/campaign/evidence/standalone/` - Independent artifact preservation
- Raw test outputs and comparison results
- Reproducibility-focused capture

### 5. Automated Capture Workflow

```python
1. Execute research/test
2. Capture raw outputs
3. Validate structure and integrity
4. Generate enhanced metadata
5. Store in primary pathway
6. Automatically replicate to proxy and standalone
7. Create cross-references
8. Trigger independent verification (when applicable)
9. Generate summary for durable result-memo
```

### 6. Discriminative Testing Protocol
For process-comparison tests:

#### Required Components:
- **Competing Hypotheses**: Clear alternative explanations to test
- **Controlled Variables**: Consistent test conditions
- **Measurable Outcomes**: Quantitative metrics for comparison
- **Independent Reproducers**: Separate verification methods

#### Evidence Requirements:
- Must discriminate between hypotheses (one hypothesis significantly outperforms other)
- Must have independent verification (different researcher/method)
- Must preserve negative evidence (when hypothesis is falsified)
- Must document uncertainty (where applicable)

### 7. Integration with Existing Framework

#### Connection to Agent 146 Evidence:
```json
{
  "evidence_id": "agent146_reject_vs_retain_2026-10-08",
  "researcher": "Agent 146",
  "task_id": "task-146-test-prior-process-intervention-0fbe201625",
  "quality_metrics": {
    "precision": 94,
    "discriminative_power": 87,
    "independent_verification": "VERIFIED",
    "false_positive_rate": 6
  },
  "findings": [
    "REJECT approach improves evidence precision (+23% vs RETAIN)",
    "REJECT approach improves discriminative power (+29% vs RETAIN)",
    "REJECT approach enables 100% independent verification vs PARTIAL",
    "REJECT approach reduces false positives (-23% vs RETAIN)"
  ],
  "conclusion": "REJECT process decision IMPROVES research quality and discrimination",
  "artifacts": [
    {
      "artifact_id": "agent146_comparison_2026-10-08T030231Z",
      "type": "process_comparison",
      "path": "/workspace/state/campaign/agent_146_test_comparison_2026-10-08T030231Z.md"
    }
  ],
  "cross_reference_ids": ["agent146_result_2026-10-08", "agent149_proxy_fix_2026-10-08"],
  "infrastructure_status": "proxy_success"
}
```

### 8. Validation and Verification

#### Quality Validation:
- **Evidence Completeness**: All required fields present and valid
- **Metric Consistency**: Quality metrics within expected ranges
- **Reproduction Status**: Independent verification status documented

#### Durability Validation:
- **Multi-Path Preservation**: Evidence exists in at least one storage path
- **Hash Integrity**: All artifacts maintain their cryptographic hashes
- **Cross-Reference Completeness**: All linked artifacts are accessible

#### Discriminative Validation:
- **Hypothesis Discrimination**: Evidence must show clear superiority of one approach
- **Statistical Significance**: Improvements must be quantifiable and meaningful
- **Independent Confirmation**: Different verification methods support findings

### 9. Future-Proofing

#### Extensibility:
- Modular design allows new evidence types
- Configurable quality gates for different research domains
- Pluggable storage backends for scalability

#### Monitoring:
- Automated alerts for evidence capture failures
- Quality metric trending analysis
- Discriminative power assessment over time

## Implementation Status

This protocol is implemented in `infrastructure_fix.py` and integrates with:

1. **PROXI_INFRASTRUCTURE_FIX.py** - Proxy fallback mechanism
2. **run_comparison_test.py** - Process-comparison testing framework
3. **agent_146_test_comparison_2026-10-08T030231Z.md** - Empirical evidence
4. **Existing durable state** - Repository-level persistence

## Impact Assessment

### Immediate Impact:
- Agent 146's evidence now durably preserved
- Enhanced discrimination testing capabilities
- Standardized protocol for all future process-comparison tests

### Long-term Impact:
- Eliminates infrastructure failure as evidence bottleneck
- Provides consistent quality across all research activities
- Enables systematic process improvement through empirical comparison
- Establishes durable foundation for ongoing research learning

## Metrics and Success Criteria

### Success Indicators:
- 100% evidence preservation across all research activities
- Standardized format compliance > 99%
- Independent verification success rate > 95%
- Discriminative power improvement > 25% per cycle
- Infrastructure failure rate < 1%

### Quality Gates:
- Evidence must pass all validation checks before acceptance
- Multiple storage paths ensure durability
- Independent verification required for empirical findings
- Discriminative testing mandatory for process comparisons

This protocol provides the foundation for the enterprise's durable ability to choose, investigate, validate, document, and learn from authorized bug-bounty and ethical-security research tasks.