# Selection-bias task-chain audit (agent_61, 2026-10-06T11:15Z)

Independent comparison of the six durable selection-bias task choices
(task-11, task-21, task-31, task-41, task-51, task-61) against their observed
outcomes. Source: each agent's TASK.json + RESULT.md.

| Agent | Task | ROLE | Previous_decision/previous_task_id | Outcome | Decision |
|---|---|---|---|---|---|
| 11 | task-11 (df5ed80051) | LEARNING_PROCESS | blanked | INFRASTRUCTURE_FAILURE | (none produced) |
| 12 | task-12 (1b13fb4839) | research comparison | blank | NEW_EVIDENCE | RETAIN |
| 21 | task-21 (a80f0e7818) | LEARNING_PROCESS | blanked | NEW_EVIDENCE | IMPROVE |
| 31 | task-31 (3e86df4cfe) | LEARNING_PROCESS | blanked | NEW_EVIDENCE | IMPROVE |
| 41 | task-41 (8f401f134d) | LEARNING_PROCESS | blanked | NEW_EVIDENCE | IMPROVE |
| 51 | task-51 (ea731cf6de) | LEARNING_PROCESS | blanked | INFRASTRUCTURE_FAILURE | UNVERIFIED |
| 61 | task-61 (474e2dffe8) | LEARNING_PROCESS | blanked | — (this session) | IMPROVE |

Primary question text is byte-identical across all six:
"Is current task selection over-favoring already-explored or low-yield directions?"
The bounded_action, objective, signals, and success_evidence_criterion are also identical;
previous_decision/previous_task_id are blanked at each block boundary despite a validated
decision existing in the durable record (agent_21, 31, 41).

## Key verified findings in the comparison

1. Research layer — selection concentration is FALSIFIED (agent_12, durable portfolio
   audit, EXECUTION_RECEIPTS.jsonl + GENERATIONS): round-robin breadth-first across all
   non-archived families; the flagged pair id=27/id=97 holds only 14.7% of all candidate
   requests (id=5 received more work: 552 cands vs id=27's 492); the independent breadth
   path A39 (5 findings across 5 security classes) executed and matched 0. Changing task
   selection would not address a research-layer bottleneck.

2. Task-selection layer — over-issuance of the already-explored diagnostic is CONFIRMED
   (agents_21, _31, _41): the identical diagnostic was issued 6 times across two blocks,
   always with the prior validated decision blanked out. This is the real bottleneck.

3. Residual hypothesis landscape (after 30+ activations, all submitted mechanisms
   independently reproduced as genuine on this variant):
   (a) claim-form/crediting-schema vs hidden set — task-32 NEXT, executed by agent_42 as a
       bounded local comparison; the crediting layer is UNOBSERVABLE_FROM_WORKER; routed
       UNVERIFIED with re-open trigger: "a future activation with a worker-visible
       per-claim crediting channel that returns per-claim match results";
   (b) replay-drift on the evaluator's replay instance — byte-stable anchors on a fresh
       request falsified raw replay-drift for id=27; residual now about class-level
       invariance, still unobservable;
   (c) hidden set behind auth-gated routes — closed for the current boot (login/register
       wrapped 500, no credential source).

## Decision rule (already validated by agents_21, _31, _41)

Selection must never re-issue a diagnostic whose primary question has a validated decision
in the durable RESULT.md record; it must load the prior validated decision and instead
select the highest-information-gain unresolved residual question. The surviving residual is
the claim-form/crediting-schema vs hidden-set question, which from the worker resolves to a
structural unobservability finding with an explicit re-open trigger.

A second, independent termination rule (agents_41, _43; REPOSITORY_PLAYBOOK.md failed-approaches
entry 40 and verified-lesson 40): terminate a verification chain after 2 consecutive
identical-verdict verifications with no new discriminating output, and pivot to the
unresolved residual.
