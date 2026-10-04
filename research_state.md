---
enterprise: desktop-tutorial-bug-bounty-research-enterprise
state_schema_version: "1.0.0"
last_updated: "2026-10-04T15:44:00Z"
state:
  primary_objective: "Confirm the research-state format (H1), instantiate a durable task-selection mechanism (intake template, prioritization rubric, decision-quality checklist), and hand off for a future authorized target."
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
    status: testing
    created: "2026-10-04T15:44:00Z"
    linked_evidence: [E5]
  - id: H3
    statement: "If research tasks are prioritized against an explicit rubric and checked against a false-positive checklist before research begins, selection and validation quality improves, measurable by consistent application to each candidate record."
    success_criteria: "A prioritization rubric and a false-positive checklist exist and are applied to each candidate record in the research-state document."
    status: pending
    created: "2026-10-04T15:44:00Z"
    linked_evidence: []
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
unresolved_questions:
  - "Should hypotheses and task records be keyed by program/target (target_key) once a scope boundary exists, rather than only by id?"
  - "Do we want a separate evidence/ directory with raw outputs (tool runs) and let RESEARCH_STATE.md reference them?"
  - "What is the cadence and trigger for promoting a hypothesis from pending to confirmed or rejected?"
  - "Should the prioritization rubric's 'evidence available' criterion be rephrased to favor hypotheses with a clear local-reproduction path?"
next_actions:
  - "Define an authorized task source (bug-bounty program scope page / task queue) and fill task-intake-template.md with the first authorized target."
  - "Apply the prioritization rubric and false-positive checklist (Sections 10-11) to each candidate record before research begins."
  - "If evidence quality becomes a repeated manual burden, promote scripts/validate_research_state.py into a recurring pre-commit gate."
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
  - `research_state.md` — confirmed H1; added H2 (task intake) and H3 (decision quality); populated structured frontmatter arrays (hypotheses, evidence, findings, activation records, decisions); added Section 10 (task intake + prioritization rubric) and Section 11 (false-positive checklist).
  - `task-intake-template.md` — new gated intake template for authorized research tasks.
- **VERIFIED:**
  - `scripts/validate_research_state.py` run against `research_state.md` after append: **valid** (schema passes; required frontmatter fields present; required hand-off labels present).
  - `task-intake-template.md` contents reviewed against the authorization gate and D3/D4 decisions.
  - Scope determination (F2) re-checked against the workspace contents.
- **UNVERIFIED:**
  - H2's long-term claim (tasks will be choosable once authorized) — awaiting first real target.
  - H3's claim (prioritization + checklist improve decision quality) — not yet applied to an external candidate.
  - Whether the validator will need extension for nested lineage/evaluation sections as the format matures.
  - Whether the prioritization rubric's criteria survive independent review when applied to a real target.
- **NEXT:**
  - Next activation: define an authorized task source and fill `task-intake-template.md` with the first authorized target; apply the prioritization rubric and checklist before any research.
  - Do not perform external target interaction until a scope boundary is explicitly documented in `task-intake-template.md`.

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
