# Optional Evolutionary Research Protocol

This document defines the lightweight protocol for controlled-mutation research. It is optional and should be activated only when a bounded candidate space and meaningful evaluator exist.

## Selection gate

Use evolutionary search when:

1. the candidate can be represented explicitly;
2. a candidate can be changed through bounded mutations;
3. evaluation is repeatable enough to compare candidates;
4. the objective is sufficiently measurable;
5. repeated search has higher expected information gain than simpler experiments.

Otherwise, use ordinary hypothesis-driven research.

## Candidate lifecycle

A candidate should move through:

PROPOSE -> MUTATE -> EVALUATE -> REVIEW -> PROMOTE / REJECT -> ARCHIVE

The repository should preserve enough information to reconstruct each meaningful transition.

## Minimum lineage record

For each promoted or materially evaluated candidate, record when practical:

- candidate identifier;
- parent identifier or baseline;
- mutation/change description;
- hypothesis or intended improvement;
- evaluator name/version/configuration;
- observed score or qualitative result;
- independent/held-out validation status;
- promotion/rejection decision;
- limitations or unresolved risks.

Never fabricate missing fields. Mark them unavailable.

## Evaluation hierarchy

Prefer evaluation signals in this order:

1. hard safety/authorization constraints;
2. correctness or validity checks;
3. independent or held-out verification;
4. primary evaluator score;
5. efficiency/cost measures;
6. secondary convenience metrics.

A candidate that improves a lower-level metric while violating a higher-level constraint is rejected.

## Diversity and stopping

Preserve useful diversity when it increases the chance of discovering different mechanisms.

Stop or change strategy when:
- candidates converge without useful new information;
- mutations become repetitive;
- the evaluator is demonstrably gameable or too noisy;
- improvements disappear under independent validation;
- resource consumption exceeds expected information gain;
- the mutation space has been adequately explored.

## Security-research boundary

Evolution may alter safe research artifacts such as hypotheses, analysis rules, test harnesses, prioritization heuristics, evidence workflows, and reporting transformations.

Evolution may not alter authorization scope, safety policy, credential rules, least-privilege boundaries, trusted scheduler/control-plane rules, or requirements for truthful reporting.

## Inspiration

The protocol is conceptually inspired by AlphaEvolve's combination of LLM-generated candidates, automated evaluation, and evolutionary selection, while intentionally adapting the idea to a safety-constrained security-research process.
