# Security Research Learning State

This is the compact durable learning layer connecting benchmark feedback to the next worker activation.

## Active strategy delta

- Gap: hidden-behavior discovery is persistently 0 while evidence quality is 1.0 and overall score is 0.05.
- Strategy Delta: Run a coverage-first discovery pass across reachable surfaces and hypothesis families, using minimally changed request representations and differential pairs before deepening any single anomaly.
- Expected Effect: Increase unique hidden-behavior discovery and reproduction without reducing evidence quality.
- Anti-gaming Constraint: preserve authorization, scope, evidence, null-case testing, independent reproduction, and hidden-evaluator isolation; never target hidden evaluator details.
- Observed Effect: UNVERIFIED — no post-delta benchmark evaluation yet.
- Decision: UNVERIFIED
- Next: Execute the next campaign with the coverage frontier recorded before deep investigation, then compare the resulting public discovery/reproduction metrics.

## Coverage frontier

| Surface / hypothesis family | Representation / method | Status | Evidence / reason | Next bounded action |
|---|---|---|---|---|
| | | UNEXPLORED | | |

Prefer an untested, high-information frontier cell over repeating an equivalent experiment.

## Recent strategy history

| Activation | Gap | Strategy Delta | Expected Effect | Observed Effect | Public metric effect | Decision |
|---|---|---|---|---|---|---|
| | | | | | | |

## Learning rules

1. Use aggregate `SOLVER_FEEDBACK.md` as a process-level search signal only; never infer hidden challenge identities or evaluator internals.
2. Normally choose one substantive strategy delta per activation.
3. Prefer breadth, mechanism diversity, differential testing, and minimally changed representations while discovery is weak.
4. Repeat an experiment only for a new hypothesis, diagnostic purpose, materially new condition, independent verification need, or different information objective.
5. A higher benchmark score is evidence about the search process, not proof of real-world security capability.
6. Never weaken safety, authorization, falsification, evidence, or held-out evaluation boundaries to improve score.
7. Do not claim a delta worked until its expected effect is observed; use UNVERIFIED when evidence is insufficient.
