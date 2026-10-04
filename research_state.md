---
enterprise: desktop-tutorial-bug-bounty-research-enterprise
state_schema_version: "1.1.0"
last_updated: "2026-10-04T19:30:24Z"
state:
  primary_objective: "Operationalize the false-positive decision-quality checklist as a triage-time evaluator (H3), add deterministic self-tests for the triage contract, promote H2, and hand off for a future authorized target."
  phase: hand-off
hypotheses:
  - id: H1
    statement: "If research state is recorded in a validated structured format (YAML frontmatter + documented sections) rather than unstructured notes, subsequent activations will produce more consistent, auditable, and reusable records, measurable by successful schema validation and presence of required hand-off labels."
    success_criteria: "At least one research state document validates against research_state_schema.json, contains required frontmatter fields, and carries CHANGED / VERIFIED / UNVERIFIED / NEXT hand-off labels."
    status: confirmed
    created: "2026-10-04T15:29:28Z"
    evaluated_at: "2026-10-04T15:44:00Z"
    conclusion: "H1 accepted and confirmed: the format validated on creation (A1) and validates again after a second activation appended records and artifacts (A2), demonstrating repeatable append + validate across activations. The long-term quality benefit versus unstructured notes is still untested with external targets."
    linked_evidence: [E1, E2, E3, E4]
  - id: H2
    statement: "If the enterprise records authorized research tasks through a documented intake mechanism (template with required authorization and scope fields), it will be able to choose and track research tasks immediately once a target is authorized."
    success_criteria: "A task-intake template exists at a documented path, a minimal example record demonstrates the required fields, and both are referenced from the research-state document."
    status: confirmed
    created: "2026-10-04T15:44:00Z"
    evaluated_at: "2026-10-04T19:30:24Z"
    conclusion: "H2 confirmed: task-intake-template.md exists at a documented path; sample-candidates/authorized-scoring-example.md follows the template's required fields and is consumed by scripts/triage_tasks.py --standalone; both are referenced from research_state.md Sections 10-12."
    linked_evidence: [E5, E7]
  - id: H3
    statement: "If the false-positive checklist (research_state.md Section 11) is implemented as a triage-time content evaluator that scores candidate records on required decision-quality fields, decision-quality checks become an independently testable part of triage rather than remaining an emitted template, measurable by per-item checklist results plus a total score for every triaged candidate and by H3's success criteria."
    success_criteria: "scripts/triage_tasks.py evaluates each awaiting_triage candidate against the Section 11 checklist, reports per-item done/partial/missing results and a total score, and makes the final decision sensitive to checklist completeness; the outcome is recorded as evidence."
    status: testing
    created: "2026-10-04T15:44:00Z"
    evaluated_at: "2026-10-04T19:30:24Z"
    conclusion: "H3 initiated into testing: evaluate_checklist() and finalize_decision() are implemented in scripts/triage_tasks.py v0.2.0, the self-test suite passes (E9), and the override path (rubric research -> defer) is verified against a fictional verified-style record (E10); the decision logic has not yet been applied to a real target."
    linked_evidence: [E8, E9, E10]
  - id: H4
    statement: "If the enterprise records candidate tasks in a machine-readable format (research_state.md `candidate_tasks` array) and applies the prioritization rubric and false-positive checklist via a deterministic triage tool, task-selection capability becomes independently testable and reusable across activations rather than remaining documentation-only."
    success_criteria: "scripts/triage_tasks.py runs without error against research_state.md, produces a ranked triage report in reports/, every candidate_task record validates against research_state_schema.json, and the triage output is recorded as evidence."
    status: testing
    created: "2026-10-04T18:48:42Z"
    linked_evidence: [E6]
evidence:
  - id: E1
    type: observation
    description: "Repository state inspection: repo contains only architecture documentation and GitHub Actions workflow; zero research artifacts exist."
    path: "git log / directory listing"
    quality: high
  - id: E2
    type: scope finding
    description: "No bug-bounty program scope, owned lab, or CTF target is present in the workspace; workspace name is generic (desktop-tutorial). Concrete external target interaction is therefore not authorized."
    path: "workspace inspection"
    quality: high
  - id: E3
    type: tooling
    description: "Workflow kilo-wakeup.yml implements model discovery, trusted config, and a credential/protected-path persistence gate; only the research-state substrate was missing."
    path: "workflow review"
    quality: high
  - id: E4
    type: verification
    description: "scripts/validate_research_state.py ran against research_state.md after a second activation appended records: valid. Schema passed; required frontmatter fields present; required hand-off labels present."
    path: "scripts/validate_research_state.py"
    quality: high
  - id: E5
    type: artifact
    description: "Created task-intake-template.md: an authorized-target gated intake template that requires scope reference, authorization verification, hypothesis, and prioritization rubric application before research begins."
    path: "task-intake-template.md"
    quality: high
  - id: E7
    type: tooling
    description: "H2 confirmed: task-intake-template.md exists at a documented path; sample-candidates/authorized-scoring-example.md demonstrates the template's required fields and is consumed by scripts/triage_tasks.py --standalone; both are referenced from research_state.md Sections 10-12."
    path: "task-intake-template.md, sample-candidates/authorized-scoring-example.md"
    quality: high
  - id: E6
    type: tooling
    description: "Created scripts/triage_tasks.py: a deterministic, dependency-light triage tool that applies the prioritization rubric (research_state.md Section 10) and false-positive checklist (Section 11) to candidate_task records, enforces the authorization gate (D4), and emits a ranked auditable report to reports/."
    path: "scripts/triage_tasks.py"
    quality: high
  - id: E8
    type: tooling
    description: "Implemented scripts/triage_tasks.py v0.2.0 checklist evaluator: CHECKLIST_EVIDENCE maps the 9 Section 11 checklist items to candidate-record fields, evaluate_checklist() scores each candidate (done/partial/missing with reasons), and finalize_decision() overrides 'research' to 'defer' when the checklist is below CHECKLIST_THRESHOLD=5 of 9."
    path: "scripts/triage_tasks.py"
    quality: high
  - id: E9
    type: verification
    description: "scripts/test_triage.py self-test suite (30 assertions) runs with 0 failures; it regression-tests the authorization gate, all four rubric scales, the accept/defer/reject thresholds, the checklist evaluator, the research->defer override, and deterministic ranking."
    path: "scripts/test_triage.py"
    quality: high
  - id: E10
    type: verification
    description: "Demo full-pipeline triage of a verified-style record: authorization gate passed, rubric 12/12 ('research'), checklist 3.0/9; final decision overridden to 'defer', confirming that checklist completeness gates research readiness."
    path: "reports/triage_20261004T193008Z.md"
    quality: high
findings:
  - id: F1
    title: "Repo has process policy but no execution-state medium"
    target: "desktop-tutorial"
    status: verified
    observation: "AGENTS.md, ENTERPRISE.md, EVOLUTION.md, PERSISTENCE_POLICY.md, MANUAL_SETUP.md define the enterprise; kilo-wakeup.yml wakes and persists."
    inference: "A durable record is the missing substrate for longitudinal research continuity."
    conclusion: "The architecture and automated wake+persist workflow are in place, but no activation record, hypothesis log, or evidence artifact has ever been persisted. This is a process-infrastructure gap, not a target-security gap."
    evidence_refs: [E1, E3]
    decided_at: "2026-10-04T15:29:28Z"
  - id: F2
    title: "No authorized target boundary defined"
    target: "desktop-tutorial"
    status: verified
    observation: "No program scope / owned lab / CTF present in the workspace."
    conclusion: "Authorization scope is ambiguous; per the authorization and safety gate, no external target interaction is performed; work is confined to safe, local repository-state improvement."
    evidence_refs: [E2]
    decided_at: "2026-10-04T15:29:28Z"
  - id: F3
    title: "Task-selection capability is the current bottleneck"
    target: "desktop-tutorial"
    status: verified
    observation: "The enterprise has a wake/persist loop and a validated state format, but no task source, no task intake, and no prioritization mechanism — it can record and persist, but has nothing to choose."
    inference: "Improving the choose step (intake + prioritization + decision quality) has higher expected durable value than adding more process documentation."
    conclusion: "The next most consequential improvement is durable task-selection capability (intake + prioritization + decision-quality checks), not more process documentation."
    evidence_refs: [E2]
    decided_at: "2026-10-04T15:44:00Z"
  - id: F4
    title: "Prioritization rubric and false-positive checklist are documented but not executable"
    target: "desktop-tutorial"
    status: verified
    observation: "research_state.md Sections 10-11 define the prioritization rubric and the decision-quality checklist, but there is no executable mechanism to apply them; H2 and H3 therefore remain untested on any candidate record."
    inference: "The task-selection bottleneck (F3) is not a lack of rubric content but a lack of an executable triage step that turns the rubric/checklist into runnable, auditable output."
    conclusion: "Implemented scripts/triage_tasks.py, which renders the rubric and checklist as deterministic, testable tooling and emits ranked triage reports; validated against the illustrative sample candidates. No external target interaction performed (F2)."
    evidence_refs: [E2, E6]
    decided_at: "2026-10-04T18:48:42Z"
  - id: F5
    title: "False-positive checklist was documentation only, never evaluated"
    target: "desktop-tutorial"
    status: verified
    observation: "research_state.md Section 11 and the false-positive checklist existed in scripts/triage_tasks.py, but triage_task() only emitted an empty checklist template; no automated decision-quality check was applied to any candidate."
    inference: "The validate capability was incomplete: the rubric was executable (F4 remediation) but the decision-quality checklist was not."
    conclusion: "Remediated in activation A4: scripts/triage_tasks.py v0.2.0 evaluates every candidate against the 9 Section 11 items and overrides 'research' decisions to 'defer' when the checklist is below 5/9; H3 moved pending -> testing. Self-tests (E9) regression-test this logic."
    evidence_refs: [E8, E9, E10]
    decided_at: "2026-10-04T19:30:24Z"
activation_records:
  - id: A1
    timestamp: "2026-10-04T15:29:28Z"
    objective: "Establish the minimal durable research-state format and instantiate it for the first time."
    scope_determination: "Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace."
    hypothesis: "H1"
    actions:
      - "Inspected repository state, git history, workflow, and config."
      - "Identified the missing durable research-state substrate as the primary bottleneck."
      - "Created research_state.md (first research-state document)."
      - "Created research_state_schema.json (frontmatter + section JSON Schema)."
      - "Created scripts/validate_research_state.py (dependency-light validator)."
      - "Validated the document against the schema."
    result: "Document validates; all required labels present. H1 accepted as proceeding."
    artifacts_created: ["research_state.md", "research_state_schema.json", "scripts/validate_research_state.py"]
    decisions:
      - "D1: Chose a single markdown document with YAML frontmatter over a pure JSON log, because the mission requires a human-readable activation record; the frontmatter supplies machine-readability and validation."
      - "D2: Did not initialize a task queue or target repository, because doing so would imply an authorization boundary that does not exist."
    next:
      - "Awaiting the next activation to test that a second activation can append records to RESEARCH_STATE.md while it still validates (tests H1 with a second data point)."
      - "Define the authorized task source and a minimal scope boundary before any target-side work."
      - "If evidence quality becomes a repeated manual burden, promote scripts/validate_research_state.py into a recurring pre-commit gate."
  - id: A2
    timestamp: "2026-10-04T15:44:00Z"
    objective: "Confirm H1, instantiate a durable task-selection mechanism (intake + prioritization + decision-quality checks), and hand off."
    scope_determination: "Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace."
    hypothesis: "H1 (confirm), H2 (test), H3 (initiate)"
    actions:
      - "Re-read the trusted instructions (AGENTS.md, ENTERPRISE.md, PERSISTENCE_POLICY.md), the workflow, config, and durable state."
      - "Confirmed the current primary objective is task-selection capability (F3), which is the most consequential lever given a validated state format and no authorized target."
      - "Marked H1 as confirmed (H1) after the state document validated across two activations; added H2 (task intake) and H3 (decision quality)."
      - "Created task-intake-template.md: a gated intake template requiring authorization verification, scope reference, and prioritization application."
      - "Extended research_state.md: structured frontmatter arrays (hypotheses, evidence, findings, activation records, decisions), Section 10 (task intake + prioritization rubric), Section 11 (false-positive checklist)."
      - "Re-ran the validator to verify append + validate still passes."
    result: "H1 confirmed. H2 in testing. H3 initiated. Validator passes after append. No external target interaction performed (F2)."
    artifacts_created: ["task-intake-template.md"]
    decisions:
      - "D3: The authoritative task source is, until a target is authorized, this intake mechanism itself; when a target exists, the single authoritative source will be the bug-bounty platform's program scope page / task queue, and tasks will be recorded in task-intake-template.md."
      - "D4: Authorization clarity is a hard gate, not a scoreable dimension: research begins only after 'Authorization verified by' is populated in the intake template."
    next:
      - "Define an authorized task source (bug-bounty program scope page / task queue) and fill task-intake-template.md with the first authorized target."
      - "Apply the prioritization rubric and false-positive checklist to each candidate record before research begins."
      - "If evidence quality becomes a repeated manual burden, promote scripts/validate_research_state.py into a recurring pre-commit gate."
  - id: A3
    timestamp: "2026-10-04T18:48:42Z"
    objective: "Make the task-selection capability executable by implementing scripts/triage_tasks.py, which renders the prioritization rubric and false-positive checklist as deterministic, testable tooling."
    scope_determination: "Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace. The sample candidates in sample-candidates/ are explicitly fictional labs and are never treated as real targets."
    hypothesis: "H4"
    actions:
      - "Re-read the trusted instructions (AGENTS.md, ENTERPRISE.md, PERSISTENCE_POLICY.md), the workflow, config, and durable state."
      - "Confirmed F3 and F4: the prioritization rubric and false-positive checklist are documented but not executable, so H2 and H3 remain untested."
      - "Extended research_state_schema.json (v1.1.0) with the candidate_tasks array to hold machine-readable task records."
      - "Created scripts/triage_tasks.py: a deterministic, dependency-light triage tool that applies the authorization gate (D4), scores the rubric, applies the false-positive checklist template, and emits a ranked, auditable report to reports/."
      - "Created sample-candidates/illustrative-example.md and sample-candidates/authorized-scoring-example.md as clearly fictional lab records to exercise the auth gate and the scoring path."
      - "Added the illustrative example to research_state.md frontmatter candidate_tasks (intake_status: not_verified) and re-ran the validator."
    result: "H4 in testing. scripts/triage_tasks.py runs against research_state.md and sample candidates without error; the auth gate rejects unverified records before scoring, and scoring produces ranked decisions. Validator passes against v1.1.0 schema."
    artifacts_created: ["research_state_schema.json (v1.1.0)", "scripts/triage_tasks.py", "sample-candidates/illustrative-example.md", "sample-candidates/authorized-scoring-example.md", "reports/triage_*.md"]
    decisions:
      - "D6: Using deterministic triage tooling rather than evolutionary mode; no bounded evaluator problem exists yet, so simpler executable tooling has higher expected information gain than a controlled-mutation search."
    next:
      - "Apply the prioritization rubric and false-positive checklist (Sections 10-11) to each candidate record before research begins."
      - "Define an authorized task source and fill task-intake-template.md with the first authorized target; then promote the illustrative example to awaiting_triage and re-triage."
      - "If evidence quality becomes a repeated manual burden, promote scripts/validate_research_state.py into a recurring pre-commit gate."
  - id: A4
    timestamp: "2026-10-04T19:30:24Z"
    objective: "Operationalize the false-positive decision-quality checklist as a triage-time evaluator (H3), add deterministic self-tests for the triage contract, and promote H2."
    scope_determination: "Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace. Sample candidates remain fictional and are never treated as real targets."
    hypothesis: "H2 (confirm), H3 (into testing), H4 (remain testing)"
    actions:
      - "Re-read the trusted instructions (AGENTS.md, ENTERPRISE.md, PERSISTENCE_POLICY.md), the workflow, config, and durable state."
      - "Confirmed F4/F5: the prioritization rubric was executable but the false-positive checklist was an emitted template only; the next bottleneck was decision-quality automation (the central 'validate' capability)."
      - "Extended scripts/triage_tasks.py to v0.2.0: added CHECKLIST_EVIDENCE, evaluate_checklist() (per-item done/partial/missing with reasons), finalize_decision() (overrides 'research' to 'defer' when the checklist is below CHECKLIST_THRESHOLD=5 of 9), and per-item checklist reporting in triage reports."
      - "Fixed a tuple-unpacking bug in triage_task() where an unrecognised rubric criterion assigned a tuple to result['decision']."
      - "Added scripts/test_triage.py: a deterministic self-test suite (30 assertions on the gate, rubric scales, thresholds, checklist evaluator, override, and ranking stability)."
      - "Reran the validator and the triage tool (research_state.md gate demo + standalone full-pipeline demo); both reports written to reports/."
    result: "H2 confirmed; H3 into testing; self-tests 30/30 pass; validator valid; triage reports generated. No external target interaction performed (F2)."
    artifacts_created: ["scripts/triage_tasks.py (v0.2.0)", "scripts/test_triage.py", "reports/triage_20261004T193008Z.md"]
    decisions:
      - "D7: A checklist score below CHECKLIST_THRESHOLD overrides an 'research' rubric decision to 'defer' with a recorded reason."
      - "D8: Deterministic self-tests added as the regression gate for the triage contract."
      - "D9: H2 promoted to confirmed; H3 moved to testing; H4 remains testing pending a real target."
    next:
      - "See Section 9 hand-off and Section 8 next actions."
decisions:
  - timestamp: "2026-10-04T15:29:28Z"
    decision: "D1 — format choice: single markdown document with YAML frontmatter rather than a JSON-only log or pure markdown notes."
    rationale: "PERSISTENCE_POLICY.md requires a concise human-readable activation record; the frontmatter supplies the structured fields that make state machine-parseable and schema-validatable."
  - timestamp: "2026-10-04T15:29:28Z"
    decision: "D2 — no task queue or target repository initialized."
    rationale: "Queue design presupposes a set of authorized targets and an intake source; neither exists. Defer until a scope boundary is defined."
  - timestamp: "2026-10-04T15:44:00Z"
    decision: "D3 — authoritative task source; intake mechanism defined."
    rationale: "No program scope / owned lab / CTF exists in the workspace (F2), so no external target can be recorded. The durable improvement is the intake mechanism itself: task-intake-template.md documents exactly how a task will be recorded once authorization exists, and research_state.md states that the single authoritative source will be the bug-bounty platform's program scope page / task queue."
  - timestamp: "2026-10-04T15:44:00Z"
    decision: "D4 — authorization clarity is a hard gate."
    rationale: "Per the authorization and safety gate, research must never begin on an unverified target. The intake template therefore requires 'Authorization verified by' populated before any work; this cannot be traded off against scope size, novelty, or expected impact."
  - timestamp: "2026-10-04T15:44:00Z"
    decision: "D5 — H1 confirmed rather than merely 'testing'."
    rationale: "H1's success criteria are met with two independent data points (creation and a second append+validate). The remaining long-term claim (superiority over unstructured notes with external targets) is still UNVERIFIED and is carried as a residual open question."
  - timestamp: "2026-10-04T18:48:42Z"
    decision: "D6 — deterministic triage tooling instead of evolutionary mode."
    rationale: "No bounded evaluator problem exists yet: the current need is a runnable, auditable triage step for the documented rubric and checklist. Simpler deterministic tooling has higher expected information gain than a controlled-mutation search, so the optional AlphaEvolve-style loop (EVOLUTION.md) is not activated this activation."
  - timestamp: "2026-10-04T19:30:24Z"
    decision: "D7 — decision-quality checklist can override a 'research' rubric decision to 'defer'."
    rationale: "scripts/triage_tasks.py v0.2.0: a research-worthy hypothesis with incomplete decision-quality prep is a deferral case (prepare the checklist), not a reject case; finalize_decision() implements this with CHECKLIST_THRESHOLD = DEFER_THRESHOLD = 5 of 9 items."
  - timestamp: "2026-10-04T19:30:24Z"
    decision: "D8 — deterministic self-tests promote the triage tooling to a testable, reproducible artifact."
    rationale: "AGENTS.md treats repeated tool failures as a signal to build deterministic tooling; test_triage.py encodes the gate, rubric scales, thresholds, checklist evaluator, override, and ranking stability as hardcoded assertions that must pass on every edit."
  - timestamp: "2026-10-04T19:30:24Z"
    decision: "D9 — H2 confirmed; H3 moved to testing; H4 remains testing."
    rationale: "H2's criteria are met (intake template, demonstrated record, references). H3's evaluator is implemented and self-tested, but the override logic has been applied only to a fictional record; a real target is needed to confirm. H4 cannot be tested without a real target."
unresolved_questions:
  - "Should hypotheses and task records be keyed by program/target (target_key) once a scope boundary exists, rather than only by id?"
  - "Do we want a separate evidence/ directory with raw outputs (tool runs) and let RESEARCH_STATE.md reference them?"
  - "What is the cadence and trigger for promoting a hypothesis from pending to confirmed or rejected?"
  - "Should the prioritization rubric's 'evidence available' criterion be rephrased to favor hypotheses with a clear local-reproduction path?"
  - "Should CHECKLIST_THRESHOLD (5 of 9) and the rubric thresholds (accept >= 8, defer 5-7) be calibrated against historical triage outcomes once real targets exist, and how should 'partial' checklist items be weighted?"
next_actions:
  - "Run scripts/test_triage.py and scripts/triage_tasks.py whenever research_state.md or the rubric/checklist changes; promote both into a pre-commit gate if evidence quality becomes a repeated manual burden."
  - "Obtain an authorized task source, fill task-intake-template.md with the first authorized target, promote that candidate to awaiting_triage, run scripts/triage_tasks.py, record the triage outcome, and move H3 to confirmed or rejected accordingly."
  - "Do not perform external target interaction until a scope boundary is explicitly documented in task-intake-template.md (D4)."
candidate_tasks:
  - task_id: "ILLUSTRATIVE-EXAMPLE"
    intake_status: "not_verified"
    authorized_target: "example-local-fake-lab (fictional; see sample-candidates/illustrative-example.md)"
    scope_boundary: "http://example.local/* (fictional)"
    auth_verified_by: null
    source_reference: "sample-candidates/illustrative-example.md"
    source_system: "illustrative example only"
    hypothesis: "Illustrative only: a debug endpoint at /debug/vars leaks internal configuration on a local lab host."
    scope_size: "small"
    hypothesis_specificity: "moderate"
    novelty: "common"
    evidence_available: "none"
---

# Research State

Durable record of hypotheses, evidence, decisions, findings, and next actions for the authorized bug-bounty research enterprise.
See `research_state_schema.json` for the frontmatter schema.

## 1. Current Primary Objective

One objective per activation, per ENTERPRISE.md and AGENTS.md:

- **Objective:** Confirm the research-state format (H1), instantiate a durable task-selection mechanism (intake template, prioritization rubric, decision-quality checklist), and hand off for a future authorized target.

## 2. Hypotheses

| id | statement (summary) | status |
|---|---|---|
| H1 | A structured research-state format (validated YAML frontmatter + sections) improves record consistency, auditability, and reuse across activations. | confirmed |
| H2 | A documented task-intake mechanism with required authorization and scope fields lets the enterprise choose and track tasks as soon as a target is authorized. | testing |
| H3 | Prioritization against an explicit rubric plus a false-positive checklist before research begins improves selection and validation quality. | pending |

## 3. Evidence

| id | type | description | path | quality |
|---|---|---|---|---|
| E1 | observation | Repo contains only architecture documentation and GitHub Actions workflow; zero research artifacts exist. | git log / directory listing | high |
| E2 | scope finding | No bug-bounty program scope, owned lab, or CTF target in the workspace; external target interaction not authorized. | workspace inspection | high |
| E3 | tooling | kilo-wakeup.yml implements model discovery, trusted config, and credential/protected-path persistence gate. | workflow review | high |
| E4 | verification | Validator passed on a second append + validate run (this activation). | scripts/validate_research_state.py | high |
| E5 | artifact | Created task-intake-template.md, a gated intake template requiring authorization verification, scope reference, and prioritization. | task-intake-template.md | high |

## 4. Findings

| id | title | status | conclusion |
|---|---|---|---|
| F1 | Repo has process policy but no execution-state medium | verified | Process and wake/persist infrastructure exist; no activation record, hypothesis log, or evidence artifact has ever been persisted. Process-infrastructure gap, not a target-security gap. |
| F2 | No authorized target boundary defined | verified | Authorization scope is ambiguous (no program scope / owned lab / CTF). No external target interaction; work confined to safe, local repository-state improvement. |
| F3 | Task-selection capability is the current bottleneck | verified | The enterprise can record, prioritize, and persist, but has nothing to choose. The most consequential improvement is durable task-selection capability, not more process documentation. |

## 5. Activation Records

### A1 — Initial state-definition activation

- **Timestamp:** 2026-10-04T15:29:28Z (observed UTC from environment; not backfilled)
- **Objective:** Establish the minimal durable research-state format and instantiate it for the first time.
- **Scope determination:** Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace.
- **Hypothesis tested:** H1.
- **Actions:**
  - Inspected repository state, git history, workflow, and config.
  - Identified the missing durable research-state substrate as the primary bottleneck.
  - Created `research_state.md` (first research-state document).
  - Created `research_state_schema.json` (frontmatter + section JSON Schema).
  - Created `scripts/validate_research_state.py` (dependency-light validator).
  - Validated the document against the schema.
- **Result:** Document validates; all required labels present. H1 accepted as proceeding.
- **Artifacts created:**
  - `research_state.md`
  - `research_state_schema.json`
  - `scripts/validate_research_state.py`
- **Decisions:** D1, D2.
- **Next:** See Section 8.

### A2 — Confirm H1; instantiate task-selection capability

- **Timestamp:** 2026-10-04T15:44:00Z (observed UTC from environment; not backfilled)
- **Objective:** Confirm the research-state format (H1), instantiate a durable task-selection mechanism (intake + prioritization + decision-quality checks), and hand off.
- **Scope determination:** Repository-internal process improvement only; no external target interaction (F2). Safe, local work within the workspace.
- **Hypotheses tested:** H1 (confirm), H2 (test), H3 (initiate).
- **Actions:**
  - Re-read the trusted instructions (AGENTS.md, ENTERPRISE.md, PERSISTENCE_POLICY.md), the workflow, config, and durable state.
  - Confirmed the current primary objective is task-selection capability (F3), the most consequential lever given a validated state format and no authorized target.
  - Marked H1 as confirmed after the state document validated across two activations; added H2 (task intake) and H3 (decision quality).
  - Created `task-intake-template.md`: a gated intake template requiring authorization verification, scope reference, hypothesis, and prioritization rubric application.
  - Extended `research_state.md`: populated structured frontmatter arrays (hypotheses, evidence, findings, activation records, decisions); added Section 10 (task intake + prioritization rubric) and Section 11 (false-positive checklist).
  - Re-ran the validator to verify append + validate still passes.
- **Result:** H1 confirmed. H2 in testing. H3 initiated. Validator passes after append. No external target interaction performed (F2).
- **Artifacts created:** `task-intake-template.md`.
- **Decisions:** D3, D4, D5.
- **Next:** See Section 8.

## 6. Decisions and Rationale

- **D1 (format choice):** Single markdown document with YAML frontmatter, rather than a JSON-only log or pure markdown notes. Rationale: PERSISTENCE_POLICY.md requires a concise human-readable activation record; the frontmatter supplies the structured fields that make state machine-parseable and schema-validatable.
- **D2 (no task queue yet):** Queue design presupposes a set of authorized targets and an intake source; neither exists. Deferred to a future activation once a scope boundary is defined.
- **D3 (authoritative task source):** Until a target is authorized, the authoritative task source is the intake mechanism itself. When a target exists, the single authoritative source will be the bug-bounty platform's program scope page / task queue; tasks will be recorded in `task-intake-template.md`.
- **D4 (authorization as a hard gate):** Per the authorization and safety gate, research must never begin on an unverified target. The intake template requires "Authorization verified by" populated before any work; authorization clarity is not a scoreable rubric dimension but a pass/fail gate.
- **D5 (H1 confirmation):** H1's success criteria are met with two independent data points (creation and a second append+validate run). The residual long-term claim (superiority over unstructured notes with external targets) remains UNVERIFIED and is carried as an open question.

## 7. Unresolved Questions

- Should hypotheses and task records be keyed by program/target (`target_key`) once a scope boundary exists, rather than only by `id`?
- Do we want a separate `evidence/` directory with raw outputs (tool runs) and let `research_state.md` reference them?
- What is the cadence and trigger for promoting a hypothesis from pending to confirmed or rejected?
- Should the prioritization rubric's "evidence available" criterion be rephrased to favor hypotheses with a clear local-reproduction path?

## 8. Next Actions

1. Define an authorized task source (bug-bounty program scope page / task queue) and fill `task-intake-template.md` with the first authorized target.
2. Apply the prioritization rubric and false-positive checklist (Sections 10-11) to each candidate record before research begins.
3. If evidence quality becomes a repeated manual burden, promote `scripts/validate_research_state.py` into a recurring pre-commit gate.

## 9. Hand-Off State

- **CHANGED:**
  - `scripts/triage_tasks.py` — v0.2.0; added `CHECKLIST_EVIDENCE`, `evaluate_checklist()` (per-item done/partial/missing with reasons), `finalize_decision()` (overrides 'research' to 'defer' when the checklist is below CHECKLIST_THRESHOLD=5 of 9), and per-item checklist reporting in triage reports; fixed a tuple-unpacking bug in triage_task() (unrecognised criterion) and corrected the wording 'any real target' -> 'any unauthorized target'.
  - `scripts/test_triage.py` — new deterministic self-test suite (30 assertions on the authorization gate, all four rubric scales, the accept/defer/reject thresholds, the checklist evaluator, the research->defer override, and deterministic ranking).
  - `reports/triage_20261004T193008Z.md` — full-pipeline demo report (gate passed, rubric 12/12 'research', checklist 3.0/9, overridden to 'defer').
  - `research_state.md` — updated: H2 confirmed, H3 into testing, E7-E10 added, F5 added, activation record A4 and decisions D7-D9 added, Section 9 hand-off refreshed, Section 12 updated to v0.2.0.
- **VERIFIED:**
  - `scripts/validate_research_state.py` run against `research_state.md`: **valid** (schema passes; required frontmatter fields present; required hand-off labels present).
  - `scripts/test_triage.py`: **30/30 pass** (0 failures).
  - `scripts/triage_tasks.py` run on `research_state.md` (auth-gate demo: ILLUSTRATIVE-EXAMPLE rejected without scoring) and standalone on `sample-candidates/authorized-scoring-example.md` (full pipeline: gate passed, rubric 12/12, checklist 3.0/9, overridden to 'defer'); reports written to `reports/`.
  - Override behavior verified: a record scoring 12/12 on the rubric is deferred because the decision-quality checklist is incomplete (E10).
  - `task-intake-template.md` contents re-reviewed against the authorization gate and D3/D4 decisions.
  - Scope determination (F2) re-checked against the workspace contents.
- **UNVERIFIED:**
  - H2's long-term claim (tasks will be choosable once authorized) — confirmed for the intake mechanism itself; awaiting first real target.
  - H3's claim (checklist improves decision quality) — implemented and self-tested, but the override logic has been applied only to a fictional verified-style record; needs a real target to confirm the 5/9 threshold is appropriate.
  - H4's claim (triage tooling makes task selection independently testable) — validated only against fictional sample candidates; needs a real target to confirm.
  - Threshold calibration (CHECKLIST_THRESHOLD=5/9; rubric accept >= 8, defer 5-7) unvalidated against real programs.
  - Whether the validator will need extension for nested lineage/evaluation sections as the format matures.
- **NEXT:**
  - Next activation: obtain an authorized task source, fill `task-intake-template.md` with the first authorized target, promote that candidate to `awaiting_triage`, run `scripts/test_triage.py` and `scripts/triage_tasks.py`, record the triage outcome, and move H3 to confirmed or rejected accordingly.
  - Do not perform external target interaction until a scope boundary is explicitly documented in `task-intake-template.md` (D4).
  - Consider promoting `scripts/validate_research_state.py` and `scripts/test_triage.py` into a pre-commit gate if evidence quality becomes a repeated manual burden.


## 10. Task Intake Mechanism and Prioritization

**Authoritative task source:** Until an authorized target exists, the task source is this intake mechanism. Once a target is authorized, the single authoritative source will be the bug-bounty platform's program scope page / task queue, and each task will be recorded in `task-intake-template.md` (D3).

**Flow:**

1. Verify authorization: confirm target, scope boundary, and written/program scope basis; record "Authorization verified by".
2. Record the task in `task-intake-template.md` from the authoritative source reference.
3. Score the task against the rubric below.
4. Decide: research / defer / reject.
5. Link the task to `research_state.md` (activation record, hypothesis, evidence, findings ids).

**Prioritization rubric** (score each criterion; the rubric summarizes, never replaces, the authorization gate in D4):

| Criterion | Scale | Notes |
|---|---|---|
| Authorization clarity (gate) | not verified / partial / clear | Hard gate; research begins only when "clear". |
| Scope size / surface area | small / medium / large | Larger, well-scoped targets give more signal per unit effort; tiny targets may be trivially covered. |
| Hypothesis specificity | vague / moderate / specific | Specific, falsifiable hypotheses are preferred. |
| Novelty | common / documented pattern / potentially novel | Novel mechanisms are prioritized; documented patterns are still valuable as confirmations or negative results. |
| Evidence available | none / partial / substantial | Favor hypotheses that can be reproduced locally with the minimum interaction (reproducibility improves evidence quality). |

Scoring is documented in the intake template; the rubric is a decision aid, not a substitute for scope discipline. A target that scores high on scope size but fails the authorization gate is rejected regardless of score.

## 11. Decision-Quality Checklist (False-Positive Mitigation)

Apply this checklist to every candidate record before research begins, and record the outcome. Its purpose is to separate observation, inference, and conclusion and to avoid upgrading a plausible story into a finding.

- [ ] The hypothesis is falsifiable and scoped to an authorized target only.
- [ ] The scope boundary is explicitly stated and any out-of-scope behavior is noted.
- [ ] Expected behavior under the null hypothesis is recorded (what would refute the hypothesis).
- [ ] At least one common false-positive class matching the hypothesis is identified and ruled out.
- [ ] The minimum safe interaction to test the hypothesis is defined; no destructive, disruptive, or stealthy action is included.
- [ ] Reproduction conditions are specified so the result is independently checkable.
- [ ] Evidence quality (high / medium / low) is assigned per observation, with source references.
- [ ] A null result (hypothesis refuted) is acceptable and recorded if that is the outcome — negative results reduce uncertainty and are preserved.
- [ ] The finding status is chosen from: verified / unverified / rejected / false-positive, never "confirmed" without the above checks.

## 12. Candidate Task Triage Tooling

**Purpose:** renders the Section 10 prioritization rubric and Section 11 decision-quality checklist as executable, auditable tooling so the task-selection capability (F3/F4) can be run and reproduced instead of remaining documentation-only.

**Tool:** `scripts/triage_tasks.py` — dependency-light (yaml/json only), mirrors the rubric and checklist in this document and keeps them in sync.

**Checklist evaluation (v0.2.0):** the tool now evaluates the Section 11 checklist per candidate (`evaluate_checklist()`, 9 items scored done/partial/missing), reports the score and per-item status in each triage report, and overrides an 'research' decision to 'defer' when the checklist is below CHECKLIST_THRESHOLD (5 of 9).

**Hard gate:** the authorization gate (D4) is enforced before scoring; a candidate with an empty `auth_verified_by` is rejected without a rubric score.

**Usage:**

    # Triage candidate tasks recorded in research_state.md (default):
    python3 scripts/triage_tasks.py

    # Triage a single stand-alone intake record (isolated test):
    python3 scripts/triage_tasks.py --standalone sample-candidates/illustrative-example.md

**Output:** a ranked triage report is printed to stdout and written to `reports/triage_<timestamp>.md`, including the authorization-gate failures, the ranking table, decision summary, lifecycle status, and the per-candidate false-positive checklist evaluation (per-item status, total score, and any decision override).

**Status of this activation's candidate task:** the illustrative example in `sample-candidates/illustrative-example.md` is recorded in the `candidate_tasks` frontmatter array with `intake_status: not_verified` and fails the authorization gate when triaged, demonstrating the D4 gate; `sample-candidates/authorized-scoring-example.md` exercises the scoring path and is purely illustrative.



## 13. Authorized Training Target

The repository now provisions an ephemeral, repository-controlled OWASP Juice Shop service for autonomous security research activations. The authoritative scope record is `AUTHORIZED_TARGET.md`. The workflow pins `bkimminich/juice-shop@sha256:8739101ade29358abb5469ee66ae78e582c97ed0a5543a4ad102e5fa5193526b (v20.2.0)` and exposes only `http://127.0.0.1:3000/*` for the duration of the job. The worker must not substitute public demo infrastructure or any unrelated external target.


## 13. Endless Hardcore Benchmark

The repository now provisions a blind, disposable security-research benchmark on every activation.

**Architecture:** a pinned OWASP Juice Shop 20.2.0 base is wrapped by a per-activation mutation gateway. A hidden cryptographic seed/spec selects randomized vulnerability families, routes, parameters, state, and secure decoys. The worker receives only the worker-facing target and a blind workspace. The exact mutation spec and benchmark harness are excluded from that workspace.

**Isolation:** target and worker use internal Docker networks. The worker has no Docker socket and no direct Internet/GitHub route. Kilo API access passes through a fixed-destination raw TLS gateway to `api.kilo.ai:443`. The evaluator is completely offline on `--network none`.

**Evaluation:** worker submissions are replayed against hidden ground truth. The evaluator verifies the hidden-spec cryptographic commitment before scoring. Aggregate metrics include discovery rate, reproduction rate, precision, evidence quality, and an overall score. Scheduled runs persist public commitment + aggregate history; manual dispatch retains short-lived forensic artifacts.

**Evolution:** recent benchmark performance influences difficulty and recent-shape avoidance. Exact target instances remain fresh and hidden rather than becoming a static challenge list.

**Current bottleneck:** runtime validation and calibration. The architecture is implemented in repository control-plane state, but a live GitHub Actions activation still needs to execute successfully before runtime claims are verified.

**CHANGED:** endless benchmark generator, mutation gateway, offline evaluator, deterministic harness self-test, isolated Kilo worker image, fixed Kilo egress gateway, workflow orchestration, worker prompt, authorization boundary, enterprise/evolution documentation.

**VERIFIED:** source-level control-plane inspection confirms the benchmark components exist, worker/evaluator separation is encoded, protected paths include the benchmark harness, and the evaluator performs commitment verification.

**UNVERIFIED:** first end-to-end GitHub Actions activation; empirical difficulty calibration; whether generated variants remain sufficiently diverse under long-run history.

**NEXT:** execute a manual workflow activation and inspect benchmark self-test, target readiness, Kilo execution, evidence replay, aggregate report, cleanup, and persistence outcomes.


## 2026-10-04T22:53:39Z — Endless Benchmark Repair Activation

### CHANGED
- Repaired the mutation comparator so security-relevant CORS response headers participate in behavioral-difference detection.
- Added explicit CORS vulnerable-versus-secure assertions to the deterministic benchmark self-test.
- Hardened workflow path handling so cleanup, merge, evaluation, and artifacts do not depend on skipped-step `GITHUB_ENV` writes.
- Removed invalid `runner.*` references from job-level `env`; only contexts permitted at that workflow key are used there.

### VERIFIED
- The previous live failure was independently inspected from GitHub Actions logs and reproduced as a CORS mutation-contract failure.
- The previous cascading `LAB_SECRET_DIR` / `EHB_WORKER_DIR` failures were confirmed from the same run.

### UNVERIFIED
- Post-repair benchmark self-test and end-to-end workflow execution remain unverified until a new GitHub Actions activation runs from this repaired commit.

### NEXT
- Use the post-repair GitHub Actions activation as the runtime verification gate; inspect self-test, target startup, worker, hidden evaluation, cleanup, and persistence before declaring the benchmark operational.


## 2026-10-04T22:58:08Z — Hardcore benchmark runtime inspection

### CHANGED
- Identified the concrete runtime blocker in workflow run 23: the repository referenced the nonexistent Docker tag `bkimminich/juice-shop:20.2.0`. The published v20.2.0 image is now referenced by its immutable multi-platform index digest.
- Strengthened target startup with explicit readiness polling for the pinned Juice Shop instance and mutation gateway.
- Prevented benchmark evaluation/history updates when target startup failed or the Kilo worker was never launched.
- Tightened evaluator target validation so out-of-scope hostnames cannot receive hidden-ground-truth credit.
- Removed the empty-submission precision floor that previously produced a positive 0.1 score for a run with no worker execution.
- Expanded the worker into a multi-pass deep-grinding campaign with mapping, hypothesis generation, differential testing, independent reproduction, negative-space search, and final falsification.

### VERIFIED
- Run 23 reached benchmark self-test, model discovery, Kilo configuration, worker-image build, and hidden benchmark generation successfully.
- Run 23 failed at target startup because Docker reported `manifest for bkimminich/juice-shop:20.2.0 not found`; its resulting empty evaluation was identified as invalid runtime data and removed from adaptive benchmark history.
- Current Docker Hub evidence confirms v20.2.0 and identifies immutable index digest `sha256:8739101ade29358abb5469ee66ae78e582c97ed0a5543a4ad102e5fa5193526b`.

### UNVERIFIED
- The repaired target startup, blind Kilo research campaign, hidden evaluation, and end-to-end persistence remain unverified until a subsequent activation completes them.

### NEXT
- Execute the repaired benchmark activation and inspect the complete ladder: target readiness, blind worker execution, evidence quality, independent replay, aggregate history, cleanup, and persistence.
