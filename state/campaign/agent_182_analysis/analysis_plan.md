# Test: Does the preceding IMPROVE decision improve auth-gating exploration quality/discrimination?

## Objective
Test whether the Agent 173 IMPROVE decision improves the quality and discrimination of auth-gating exploration on blocked surfaces.

## Pre-IMPROVE Baseline (Agent 66 uniform-500 pattern)
- Evidence quality threshold: NONE (0 allowed)
- Result: Uniform-500 no-ops, 0 discriminable information
- Header-differential: Not preserved (no evidence quality gates)

## Post-IMPROVE (with evidence quality threshold >0)
- Evidence quality threshold: >0 discriminable bytes required
- Gates enabled:
  - Artifact-promotion gate (Agent 66)
  - Selection rule excluding infrastructure-failure patterns (Agent 161)
  - Disk-existence verification (Agent 66)

## Hypothesis
**Null**: IMPROVE decision does NOT improve auth-gating exploration quality/discrimination
**Alternative**: IMPROVE decision DOES improve auth-gating exploration quality/discrimination

## Test Design
Run fresh independent reproduction of auth-gating exploration with evidence quality threshold enforcement >0.

### Test Protocol
1. Target blocked auth surfaces on current boot (login=401, no credential source)
2. Apply evidence quality gates and threshold enforcement
3. Compare against pre-IMPROVE uniform-500 baseline
4. Assess discriminable evidence preservation

### Auth Surfaces to Test
- GET /rest/user/security-question (401, no Accept header)
- GET /rest/user/security-question (401, Accept: application/json)
- GET /api/BasketItems (401)
- POST /api/SecurityAnswers/ (201 write-open, null ownership)
- GET /api/SecurityAnswers/ (401 read-gated)
- GET /api/Coupons (500, routes mutated away)
- GET /api/ChangePassword (401)

### Expected Results
If IMPROVE decision EFFECTIVE:
- Evidence quality: >0 discriminable bytes (vs 0 baseline)
- Discriminability: Header-differential preserved as byte-anchored evidence
- Selection: Auth-gating surface properly selected with evidence quality >0

If IMPROVE decision INEFFECTIVE:
- Evidence quality: Still 0 discriminable bytes (no improvement)
- Discriminability: No header-differential preservation
- Selection: Still uniform-500 pattern

## Deliverable
One reproducible research result demonstrating whether the preceding IMPROVE decision improves the quality or discrimination of auth-gating exploration.