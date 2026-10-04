---
task_id: "INTAKE-TEMPLATE"
version: "1.0.0"
---

# Research Task Intake Template

Record an authorized bug-bounty research task only when the target and scope are explicitly authorized.
This template is the enterprise's authoritative intake point once a task source exists.

## 1. Authorization gate

- **Authorized target:** (program name and URL, or owned lab / CTF)
- **Authorization source:** (program program page, bounty policy page, or written authorization)
- **Scope boundary:** (explicit allowed targets / paths / endpoints; anything not listed is out of scope)
- **Authorization verified by:** (person / mechanism)
- **Verification status:** [ ] not verified [ ] verified
- Do not record or research a task until "Authorization verified by" is populated and verification status is "verified".

## 2. Task source

- **Source system:** (bug-bounty platform, program docs, internal backlog — state the single authoritative source)
- **Source reference:** (URL or local path to the source record)
- **Intake timestamp:** (UTC ISO 8601 when recorded)

## 3. Research hypothesis

- **Hypothesis:** (falsifiable statement of the suspected issue)
- **Why this target:** (specific property of this target that motivates the hypothesis)
- **Success criteria:** (observable conditions that confirm or refute the hypothesis)
- **Rejected false positives to check first:** (common non-issues that match this pattern)

## 4. Prioritization

Apply the prioritization rubric from research_state.md (Section 10) and record:

- **Authorization clarity (gate):** (not verified / partial / clear) — blocks research if not verified
- **Scope size / surface area:** (small / medium / large)
- **Hypothesis specificity:** (vague / moderate / specific)
- **Novelty:** (common / documented pattern / potentially novel)
- **Evidence available:** (none / partial / substantial)
- **Total score / decision:** (accept / defer / reject)

## 5. State record

Link this task to the enterprise research state:

- **research_state.md entry:** (activation record id, hypothesis id, evidence ids, findings id)

## 6. Decision

- **Decision:** (research / defer / reject)
- **Decision rationale:** (one or two sentences)
- **Decided at:** (UTC ISO 8601)
