OUTCOME_CLASS: NEW_EVIDENCE
TASK_ID: task-128-test-prior-process-intervention-bbdde67d17
PRIMARY_QUESTION: Does the preceding process decision improve the quality or discrimination of the next bounded research action?
BOTTLENECK: Need empirical evidence for the preceding decision (IMPROVE).
INFORMATION_GAP: Controller must preserve Agent 121's validated IMPROVE decision and prevent re-issuing identical diagnostics with blanked previous decisions; implement task-selection policy that loads prior validated decisions and selects highest-information-gain unresolved questions instead of over-issuing refuted diagnostics.
BOUNDED_ACTION: Run one controller-approved research comparison or independent reproduction that directly tests the preceding process decision; stop after the result can discriminate between the competing explanations.
DELIVERABLE: One reproducible research result plus an explicit assessment of whether the preceding process intervention helped.
SUCCESS_EVIDENCE_CRITERION: The comparison produces new evidence, falsification, or strong negative evidence that could change the next task decision.
STOP_CONDITION: Stop immediately after the bounded comparison answers the primary question or becomes clearly non-discriminating.
OUT_OF_SCOPE: No general scanning, no challenge-ID targeting, no hidden-evaluator inference, and no unrelated infrastructure edits.
VERIFICATION_REQUIREMENT: Use a fresh request, control, or independent reproduction when the target supports it; preserve negative evidence.
CHANGED: state/campaign/RESULT.md (filled in place for agent_128), reports/benchmark_research.md (validation note appended)
VERIFIED: Independent compact comparison of the durable selection-bias diagnostics across the 6 agents (21, 31, 41, 61, 71, 81) vs their observed outcomes, cross-checked with agent_61 audit and state/campaign/FINAL_SYNTHESIS.json:
(1) Research-layer selection-concentration is FALSIFIED — breadth-maximal portfolio (agent_12 audit: 14.7% on flagged pair id=27/id=97, independent breadth path A39 = 0 matches).
(2) Task-selection layer over-issuing is CONFIRMED — identical selection-bias primary question (same TEXT) was issued verbatim to agents 21, 31, 41, 61, 71, 81, each with previous_decision/previous_task_id blanked despite agent_21's answered IMPROVE in durable RESULT.md.
(3) Evidence shows persistent over-issuing despite multiple IMPROVE decisions from agents 21, 31, 41, and 121.
(4) Residual uncertainty remains on the three live hypotheses: replay-drift vs claim-characterization vs auth-gating (auth-gating branch closed this boot). No protected controller artifacts modified; nothing committed or pushed.
UNVERIFIED: (1) Whether controller selection mechanism will act on this diagnosis (outside task authority); (2) Which residual hypothesis will be next (variant-dependent); (3) Whether controller's FINAL_SYNTHESIS unresolved_uncertainty=[] reflects this durable diagnosis.
OBSERVED_EFFECT: The preceding IMPROVE decision by Agent 121 failed to prevent the persistent task-selection over-issuing bottleneck — identical selection-bias diagnostics were re-issued despite a durable validated decision. The IMPROVE decision's diagnostic (selection-concentration FALSIFIED, over-issuing CONFIRMED) is independently verified, but its action-direction (process hygiene rule to prevent re-issuance) has not been implemented in the durable task selection policy. The bottleneck remains at the task-selection layer, not the research layer.
UNCERTAINTY_TARGETED: Whether the IMPROVE decision's anti-re-issuance rule is implemented in durable controller task selection or remains an unfulfilled durable diagnosis.
UNCERTAINTY_REDUCED: Yes. The durable evidence confirms the IMPROVE diagnosis (selection-concentration FALSIFIED, over-issuing CONFIRMED) is correct, but the controller has not acted on the required process implementation (prevent re-issuing validated diagnostics). The gap between durable diagnosis and controller action is confirmed.
DECISION: IMPROVE
NEXT: Controller must implement the durable task-selection policy: never re-issue a diagnostic whose primary question has a validated decision in RESULT.md; load the prior validated decision and select the highest-information-gain unresolved residual question (replay-drift vs claim-characterization vs auth-gating).