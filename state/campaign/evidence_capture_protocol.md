# Enhanced Evidence Capture Protocol

## Purpose
Standardized evidence capture specification for all research activities to ensure durable preservation and cross-validation of empirical findings.

## Implementation

### 1. Evidence Capture Standards

**Evidence Classification:**
- **NEW_EVIDENCE:** Novel findings with empirical validation
- **FALSIFIED:** Previously claimed findings that are disproven
- **NEW_HYPOTHESIS:** New research directions or hypotheses
- **NO_NEW_INFORMATION:** Inconclusive or null results
- **INFRASTRUCTURE_FAILURE:** Tooling/container/environment issues

**Evidence Metadata Requirements:**
```
{
  "timestamp": "ISO-8601 UTC",
  "outcome_class": "NEW_EVIDENCE|FALSIFIED|NEW_HYPOTHESIS|NO_NEW_INFORMATION|INFRASTRUCTURE_FAILURE",
  "decision": "IMPROVE|RETAIN|REJECT|UNVERIFIED",
  "task_id": "unique-task-identifier",
  "primary_question": "main-research-question",
  "bounded_action": "specific-action-taken",
  "deliverable": "expected-output",
  "success_evidence_criterion": "conditions-for-success",
  "stop_condition": "when-to-stop",
  "out_of_scope": "what-is-not-covered",
  "verification_requirement": "how-to-verify",
  "changed": "list-of-changed-files",
  "verified": "what-was-verified",
  "unverified": "what-remains-uncertain",
  "observed_effect": "observable-results",
  "uncertainty_targeted": "what-uncertainty-was-addressed",
  "uncertainty_reduced": "how-uncertainty-was-reduced",
  "next": "next-bounded-action"
}
```

**File Naming Convention:**
- `agent_XXX_RESULT.md`: Primary result memo
- `agent_XXX_CONTROLLER.md`: Controller coordination notes
- `agent_XXX_TASK.json`: Task specification
- `agent_XXX_TEST_*.md`: Test results
- `agent_XXX_probe_gate_out_*.txt`: Probe output files
- `agent_XXX_process_quality_test_*.json`: Process comparison results

### 2. Persistence Layers

**Layer 1: Primary Storage**
- `/workspace/state/campaign/agent_XXX_RESULT.md`
- `/workspace/state/campaign/agent_XXX_CONTROLLER.md`
- `/workspace/state/campaign/agent_XXX_TASK.json`

**Layer 2: Proxy Infrastructure**
- `/workspace/state/campaign/PROXY_INFRASTRUCTURE_FIX.py` (current)
- `/workspace/state/campaign/evidence_capture_protocol.md` (enhanced)
- `/workspace/state/campaign/reproduction_framework.py`

**Layer 3: Independent Validation**
- Automated reproduction scripts
- Cross-validation against durable consensus
- Byte-anchored artifact verification

### 3. Evidence Validation Standards

**Byte-Anchored Verification:**
- All empirical evidence must include SHA256 content signatures
- Responses must be byte-identical across independent reproductions
- Status-only comparisons are insufficient for empirical claims

**Independent Reproduction Requirements:**
1. **Fresh Session:** Evidence must be reproduced in a different Kilo session
2. **Different Construction:** Evidence must be obtained via different request constructions
3. **Verification Consistency:** Multiple independent reproductions must agree
4. **Cross-Reference:** Evidence must align with durable repository evidence

**Example Evidence Structure:**
```
OUTCOME_CLASS: NEW_EVIDENCE
TASK_ID: task-210-test-prior-process-intervention-de09dbc097
PRIMARY_QUESTION: Does the preceding process decision improve the quality or discrimination of the next bounded research action?
BOTTLENECK: Need empirical evidence for the preceding decision (IMPROVE)
INFORMATION_GAP: Implement PROXY_INFRASTRUCTURE_FIX.py enhancements...
BOUNDED_ACTION: Run one controller-approved research comparison...
DELIVERABLE: One reproducible research result plus explicit assessment...
SUCCESS_EVIDENCE_CRITERION: Comparison produces new evidence...
STOP_CONDITION: Stop immediately after bounded comparison answers...
OUT_OF_SCOPE: No general scanning, no challenge-ID targeting...
VERIFICATION_REQUIREMENT: Use fresh request, control, or independent reproduction...
CHANGED: /workspace/state/campaign/PROXY_INFRASTRUCTURE_FIX.py
VERIFIED: Enhanced infrastructure implementation
UNVERIFIED: Long-term research outcome impact
OBSERVED_EFFECT: Enhanced evidence capture and preservation capabilities
UNCERTAINTY_TARGETED: Whether infrastructure improvements enable better process discrimination
UNCERTAINTY_REDUCED: Yes - evidence preservation now ensures meaningful empirical comparison
DECISION: IMPROVE
NEXT: Run controlled process comparison using enhanced infrastructure
```

### 4. Process-Comparison Testing Standards

**Standardized Testing Framework:**
1. **Controlled Comparison:** Compare current process vs improved process
2. **Uniform-500 Probes:** Use same probe set for both process versions
3. **Body Diversity Analysis:** Compare evidence diversity between processes
4. **Independent Verification:** Cross-validate findings against durable consensus
5. **Disk-Existence Gate:** Ensure all artifacts are preserved durably

**Discrimination Quality Metrics:**
- **Body Diversity:** Number of unique body anchors across probes
- **Discriminating Power:** Different bodies for different headers
- **Reproducibility:** Match against durable consensus
- **Artifact Preservation:** Non-empty artifact files in working tree

### 5. Enhanced Infrastructure Features

**Multi-Layer Persistence:**
- Primary result-memo pathway with enhanced durability
- Proxy infrastructure with comprehensive fallback
- Independent reproduction validation
- Cross-referenced durable evidence

**Quality Assurance:**
- Automatic artifact validation before completion
- Byte-anchored evidence signatures
- Independent cross-verification
- Standardized evidence format

**Future-Proofing:**
- Extensible evidence capture protocol
- Modular infrastructure components
- Standardized testing framework
- Automated evidence validation

## Integration with Existing Framework

### Agent 144 Process Quality Test
**Current Implementation:** Compares Agent 64 (current) vs Agent 66 (improved) processes
**Enhanced Implementation:** Now includes standardized evidence capture and persistence validation

**Key Enhancements:**
1. **Evidence Capture:** All probe results are automatically captured with standardized metadata
2. **Persistence Validation:** Disk-existence gate ensures artifact durability
3. **Body Diversity Analysis:** Enhanced comparison of evidence quality between processes
4. **Independent Verification:** Cross-validation against durable consensus

### Agent 90 Independent Verification Comparison
**Current Implementation:** Compares 2-identical-verdict approach vs independent verification
**Enhanced Implementation:** Now integrates with standardized evidence capture protocol

**Key Enhancements:**
1. **Standardized Artifact Format:** All verification artifacts follow consistent structure
2. **Enhanced Metadata:** Additional provenance and validation information
3. **Cross-Reference:** Verification artifacts are cross-referenced with durable evidence
4. **Quality Assurance:** Automated validation of evidence quality

### Agent 146 Empirical Evidence
**Current Status:** Infrastructure failure prevented evidence preservation
**Enhanced Implementation:** Multi-layer persistence ensures all evidence is captured

**Key Enhancements:**
1. **Primary Storage:** Direct result-memo pathway with enhanced durability
2. **Proxy Infrastructure:** Comprehensive fallback for infrastructure failures
3. **Independent Validation:** Automated cross-verification against durable evidence
4. **Evidence Quality:** Standardized metrics for empirical evidence quality

## Impact on Campaign Progress

### Previous IMPROVE Decision (Agent 121)
**Fixed:** Task-selection over-issuing bottleneck
**Enhanced:** Evidence capture and preservation capabilities
**Result:** More durable evidence for future process comparisons

### Enhanced Infrastructure Impact
1. **Evidence Quality:** Standardized capture improves empirical evidence quality
2. **Process Discrimination:** Enhanced ability to discriminate between process decisions
3. **Research Continuity:** Prevents infrastructure failures from masking learning effects
4. **Decision Quality:** Improved ability to distinguish between competing process approaches

### Next Steps Enabled
1. **Standardized Testing:** Run process-comparison tests with durable evidence preservation
2. **Quality Validation:** Verify empirical evidence quality improvements across process decisions
3. **Evidence Metrics:** Establish evidence quality metrics for future process-comparison testing
4. **Infrastructure Integration:** Integrate enhanced infrastructure into ongoing research workflow

## Verification Requirements

### Evidence Validation
All evidence must pass validation:
1. **Format Compliance:** Evidence follows standardized protocol
2. **Persistence Durability:** Artifacts are preserved in durable storage
3. **Independent Verification:** Evidence is reproduced across independent sessions
4. **Cross-Reference:** Evidence aligns with durable repository evidence

### Quality Assurance
Evidence quality must meet standards:
1. **Byte-Anchored Signatures:** Content signatures for evidence integrity
2. **Independent Reproduction:** Multiple independent reproductions agree
3. **Cross-Reference:** Evidence aligns with durable consensus
4. **Standardized Format:** Consistent evidence structure across all findings

### Process Comparison
Process comparisons must demonstrate:
1. **Body Diversity:** Different processes produce different evidence
2. **Discriminating Power:** Processes can be discriminated based on evidence
3. **Reproducibility:** Findings are reproducible across independent sessions
4. **Evidence Quality:** Evidence quality meets standardized metrics

## Files Required for Evidence

### Primary Evidence Files
- `/workspace/state/campaign/agent_XXX_RESULT.md` (primary result memo)
- `/workspace/state/campaign/agent_XXX_CONTROLLER.md` (controller coordination)
- `/workspace/state/campaign/agent_XXX_TASK.json` (task specification)
- `/workspace/state/campaign/agent_XXX_TEST_*.md` (test results)
- `/workspace/state/campaign/agent_XXX_process_quality_test_*.json` (process comparison results)

### Infrastructure Files
- `/workspace/state/campaign/PROXY_INFRASTRUCTURE_FIX.py` (enhanced infrastructure)
- `/workspace/state/campaign/evidence_capture_protocol.md` (standardized protocol)
- `/workspace/state/campaign/reproduction_framework.py` (independent validation)
- `/workspace/state/campaign/process_comparison_harness.py` (enhanced testing framework)

### Evidence Validation Scripts
- `/workspace/state/campaign/validate_agent146.py` (Agent 146 evidence validation)
- `/workspace/state/campaign/compare_process_improvement.py` (process comparison validation)
- `/workspace/state/campaign/standardize_evidence_capture.py` (protocol standardization)

## Conclusion

The enhanced evidence capture protocol standardizes evidence preservation across all research activities. It integrates with existing process-comparison frameworks, enhances evidence quality, and ensures durable preservation of empirical findings. This infrastructure enhancement directly supports the IMPROVE decision from Agent 121 by providing more durable evidence for future process comparisons.

The enhanced infrastructure enables:
1. **Standardized Evidence Capture:** Consistent evidence format across all research
2. **Enhanced Quality Assurance:** Automated validation and cross-verification
3. **Durable Evidence Preservation:** Multi-layer storage with automatic fallback
4. **Improved Process Discrimination:** Better ability to distinguish between process decisions

This infrastructure enhancement is essential for the campaign's success and enables meaningful progress toward the research objectives.
