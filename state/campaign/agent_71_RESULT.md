OUTCOME_CLASS: NEW_EVIDENCE
TASK_ID: task-71-task-selection-bias-ef47523f41
PRIMARY_QUESTION: Is current task selection over-favoring already-explored or low-yield directions?
BOTTLENECK: Repeated or converged work may be consuming effort without reducing meaningful uncertainty.
INFORMATION_GAP: Current durable signals: selection-concentration, evidence-mismatch, persistence, hypothesis-frontier. Evidence excerpt: ## Active strategy delta | - Gap: campaign unsolved after 25+ activations; public metrics 0.0500 / discovery 0.0000 / repro 0.0000 / precision 0.0000 / evidence 1.0000 (roughly stable); aggregate feedback names hidden-behavior discovery as the primary gap and recommends broader hypothesis generation, behavioral differential testing, and testing of minimally changed request representations before repeatedly deepening one finding; the /api/Challenges/ solved flags proved to be dynamic app auto-solve (not evaluator ground truth): on the A26 boot solved:true = [27, 76, 97] but on the current boot (A27 re-probe 10:46Z) solved:true = [27, 97] and id=76 never flips to solved even after route visits (retracted) - used only as a route-viability hint; CORRECTION (A40): the A39 breadth expansion (2026-10-06T02:07Z) submitted 5 findings spanning 5 distinct security classes (id=14 CAPTCHA, id=1+id=24
BOUNDED_ACTION: Compare recent durable task choices with their observed outcomes; identify one decision rule that would preferentially select a more discriminating unresolved question.
DELIVERABLE: A compact process diagnosis with one decision: IMPROVE, RETAIN, REJECT, or UNVERIFIED.
SUCCESS_EVIDENCE_CRITERION: A compact comparison shows whether selection concentration is a real bottleneck and whether one bounded rule change is justified.
STOP_CONDITION: Stop after the single bounded comparison is sufficient to choose one process decision.
OUT_OF_SCOPE: No broad redesign, no unrelated security sweep, no hidden benchmark inference, and no changes to protected controller infrastructure.
VERIFICATION_REQUIREMENT: Use recent durable evidence and one independent artifact, comparison, or observation before making the process decision.

## Compact process diagnosis

**Comparison performed (bounded):** recent durable task choices (LEARNING_STATE.md strategy history A15-A40) vs observed outcomes (campaign metrics, PROCESS_HISTORY.jsonl, portfolio execution, surface statuses).

| Activation | Task choice (what was selected) | Observed outcome |
|---|---|---|
| A15 | Selected solved-flag targeting -> id=27, id=97 | 0.0000 discovery |
| A16-A38 | RETAINED selection of id=27/id=97; re-verified + re-submitted on ~30 boots | unchanged 0.0000 |
| A22 | Breadth alternative: submit ALL verified anomalies across classes | 0.0000 precision (4/8 non-counted); RETRACTED |
| A29 | Selectivity delta: exactly 2 coverage-oracle TRUE findings | 0.0000; RETRACTED |
| A39 | Breadth expansion: 5 findings across 5 security classes | 0.0000 matched - hidden set excludes every verified behavior observed on this variant; RETRACTED |
| A40 | Mutation-feature /api/Challenges/? filter layer + captcha cleartext leak | pending evaluation |

**Independent artifact (concentration vs. residual frontier):** SURFACES.json - 16 surfaces: 7 VERIFIED (all non-counted side effects with prior 0 evaluations), 6 NEGATED, 3 DEPRIORITIZED, 1 EXHAUSTED_FOR_NOW; portfolio executed 432 generations / 478 candidates / 73 behavioral differences with no new vulnerability class beyond id=27/id=97; PROCESS_HISTORY.jsonl - 6 recent activations all with discovery_rate 0.0 and overall_score 0.0. Coverage frontier still lists untested cells (fam_origin_header_variants CANDIDATE; method-differential sweep on live /api/* writes).

**Conclusion:** yes, selection is over-favoring already-explored directions. The same two evaluated-0 classes (id=27, id=97) have been re-selected identically for ~30 activations with zero cumulative information gain, while BOTH breadth alternatives (A22, A39) that deliberately selected unexplored directions also evaluated to 0. Concentration on these two classes is therefore a confirmed bottleneck in itself, not merely a symptom of claim-characterization or replay-drift.

**One decision rule (IMPROVE):**

> **Frontier-preference rule:** do not re-select an already-submitted finding class with a prior 0 evaluation for a new submission unless (1) the target variant's route/trigger composition has changed since that class was last submitted, or (2) a new discriminator (representation, method, or differential) not yet evaluated for that class has been added. While id=27/id=97 remain solvable, the activation must first execute at least one untested frontier cell - in priority order: the pending fam_origin_header_variants HEAD/Origin/Referer sweep on the raw-error route (never-executed operator family, status CANDIDATE); the POST/PUT/PATCH/DELETE method-differential sweep across the surviving live /api/* write endpoints (promising_branches still open on surf_23_memories, surf_24_securityanswers_write, surf_6_put_tamper); and the /api/Challenges/? query-filter enumeration surface (submitted A40, pending evaluation) - before re-verifying and re-submitting id=27/id=97.

DECISION: IMPROVE

CHANGED: state/campaign/RESULT.md - compact process diagnosis filled with the bounded comparison, decision rule, and decision token.

VERIFIED: comparison performed on three independent durable artifacts (LEARNING_STATE.md strategy history A15-A40; PROCESS_HISTORY.jsonl six recent activations; SURFACES.json surface statuses plus portfolio execution counts) - all show selection concentrated on id=27/id=97 with 0 cumulative discovery and breadth alternatives (A22, A39) also evaluating 0; decision rule is testable on the next variant activation.

UNVERIFIED: the A40 submissions (/api/Challenges/? query-filter layer, CAPTCHA cleartext leak) pending regenerated SOLVER_FEEDBACK.md evaluation; fam_origin_header_variants family still unexecuted (CANDIDATE); whether the evaluator replays against volatile per-request state or a differently-seeded instance.

OBSERVED_EFFECT: metrics stable at 0.0500 / 0.0000 / 0.0000 / 0.0000 / 1.0000 across 25+ activations; ~30 consecutive activations re-verifying and re-submitting the same two behaviors; both breadth experiments (A22, A39) that selected different directions evaluated to 0.0000.

UNCERTAINTY_TARGETED: Whether selection concentration over already-explored directions is a real bottleneck versus a claim-matching / replay-drift artifact alone.

UNCERTAINTY_REDUCED: Selection-concentration is confirmed as a real bottleneck by the bounded comparison - the same two classes re-selected ~30 times at 0 outcome, and BOTH breadth alternatives that selected unexplored directions also returned 0.0000. Residual: whether the hidden set instead lies in the currently-blocked auth surface (untestable this variant) or in claim framing, which the frontier-preference rule will continue to discriminate on a new variant.

NEXT: On the next variant activation, execute the untested fam_origin_header_variants HEAD/Origin/Referer sweep on the raw-error route plus a POST/PUT/PATCH/DELETE method sweep of live /api/* write endpoints before re-submitting id=27/id=97.
