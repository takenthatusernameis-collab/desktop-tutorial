# Kilo Worker Learning Efficiency

## Current diagnosis

The infrastructure has a strong external learning loop:

**worker -> hidden evaluation -> aggregate history -> SOLVER_FEEDBACK.md -> next worker**

Current public benchmark evidence shows high evidence quality but repeatedly near-zero discovery, reproduction, precision, and overall score. The important implication is:

**the worker is better at validating discovered anomalies than at discovering the benchmark's hidden behavioral differences.**

The bottleneck is therefore search efficiency and breadth, not more evidence-reporting instructions.

## Highest-value learning improvement

Convert aggregate solver feedback into one explicit, durable **strategy delta** per activation:

- **Gap:** the public capability gap indicated by aggregate feedback.
- **Strategy Delta:** exactly one change in search behavior.
- **Expected Effect:** which public metric should improve.
- **Anti-gaming constraint:** what must not be weakened to obtain that improvement.
- **Observed Effect:** what actually happened.
- **Decision:** RETAIN / REVERT / UNVERIFIED.

Do not infer or reconstruct hidden challenge identities, mutation families, or evaluator internals.

## Discovery-efficiency changes

### 1. Search breadth before depth

Because discovery is the persistent weak signal, require a coverage-oriented early phase before repeatedly deepening one promising anomaly.

Prioritize:
- distinct reachable surfaces;
- distinct hypothesis classes;
- minimally changed request representations;
- differential request pairs;
- nearby null cases.

Only deepen a finding after the current search frontier has enough coverage to justify it.

### 2. Track an explicit coverage frontier

Maintain a compact list of:
- tested surface;
- hypothesis class;
- representation/method combination;
- outcome;
- unresolved follow-up.

The next activation should preferentially select a high-value untested cell rather than rediscovering prior work.

### 3. Learn from benchmark feedback at the process level

The current feedback says discovery is weak while evidence quality is strong. Therefore the worker should change search policy, not relax evidence thresholds.

A feedback update should change one of:
- hypothesis-generation breadth;
- differential-test selection;
- surface prioritization;
- negative-space search order;
- representation diversity.

### 4. Preserve held-out validity

Benchmark score is a search signal, not proof of real-world security capability.

Never alter:
- authorization scope;
- safety constraints;
- evidence standards;
- null/falsification requirements;
- hidden-evaluation boundaries.

### 5. Prefer mechanism diversity

When several activations plateau, change search mechanism rather than merely increasing repetition.

Useful mechanism changes include switching from:
- route-by-route probing -> hypothesis-family sweeps;
- single-parameter mutation -> representation/verb comparisons;
- anomaly deepening -> systematic null-case matrix;
- repeated exploitation -> differential behavior discovery.

## Implementation priority

The best first implementation is not a larger prompt. It is a compact **strategy-delta + coverage-frontier memory** that connects benchmark feedback to the next activation's search policy.

Only add more sophisticated evolutionary selection if this lightweight feedback loop fails to improve discovery over several genuinely different activations.
