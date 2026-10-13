# Agent 388: Independent Process Decision Test

## Test Purpose

This test independently verifies whether the preceding IMPROVE decision (from Agent 382/385) actually improves the quality or discrimination of the next bounded research action compared to the UNVERIFIED baseline (from Agent 381).

The test directly addresses the contradiction revealed by examining Agent 382's IMPROVE RESULT.md vs Agent 384's REJECT comparison result.

## Test Design

### Baseline (UNVERIFIED - Agent 381)
- Infrastructure failure with no valid result memo
- Limited to controlled scope only
- Constrained evidence discrimination
- Scope-limited quality maintenance

### IMPROVE Decision (Agent 382)
- Enhanced evidence capture with comprehensive metadata
- Independent reproduction validation
- Multi-layer artifact persistence
- Quality assurance standards

### Test Objective
- Measure objective quality improvement through enhanced evidence capture
- Compare discrimination power between UNVERIFIED and IMPROVE approaches
- Verify whether IMPROVE decision actually meets improvement thresholds
- Provide clear discrimination between competing explanations

## Test Methodology

This test uses the same enhanced process comparison framework as Agent 384 but with independent implementation and verification.

### Test Probes
1. **P1_baseline**: Error response without Accept header
2. **P2_accept_json**: JSON error response with Accept header
3. **P3_null_control**: Graceful 'Unexpected path' error response

### Quality Metrics Assessed
- Evidence diversity (unique body signatures)
- Discrimination power (header-dependent response variation)
- Reproducibility (match against durable consensus)
- Artifact preservation (disk-existence gate compliance)

### Decision Criteria
Based on Agent 384's comparison results:
- **IMPROVE**: Must meet minimum improvement threshold (≥0.23)
- **Discrimination gain**: Must show improvement
- **Reproducibility enhancement**: Must show improvement
- **Artifact preservation improvement**: Must show improvement
- **Quality preservation improvement**: Must show improvement
- **Evidence discrimination improvement**: Must show improvement

## Independent Test Implementation

This test creates a completely fresh, independent comparison to verify the IMPROVE decision effectiveness.