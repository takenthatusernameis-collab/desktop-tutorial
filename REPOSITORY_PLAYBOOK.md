# Repository Interaction Playbook

## Purpose

This file is the repository's **procedural generational memory**.

It records verified, reusable knowledge about how to operate this security-research enterprise efficiently and safely. It is deliberately separate from research findings, benchmark state, and controller-owned evaluation artifacts.

The objective is to help each fresh Kilo generation inherit the repository's best-known operating methods instead of rediscovering them.

## How to use this playbook

Read this file early in every activation.

Treat entries as **operational guidance**, not target or benchmark evidence. A lesson can explain how to inspect state, select methods, reproduce an observation, preserve an artifact, or recover from a tooling problem without proving that any security hypothesis is true.

Prefer:
- controller-owned state and durable research records over conversational memory;
- existing deterministic harnesses over ad-hoc replacements;
- breadth and discriminating tests before repetitive deepening;
- targeted verification before broad execution;
- durable evidence and compact handoffs over raw logs.

When a verified lesson supersedes an older rule, strengthen the existing entry instead of creating a duplicate.

## Fast path for a fresh activation

1. Read `LEARNING_EFFICIENCY.md`, `SOLVER_FEEDBACK.md`, durable campaign/research state, and the latest relevant activation record when present.
2. Read this playbook for verified repository-operating shortcuts and recurring failure modes.
3. Inspect the controller-selected task and trusted program handoff before target interaction.
4. Reuse existing deterministic research/program infrastructure.
5. Establish a small representative path before broadening.
6. Independently reproduce consequential observations and check false-positive explanations.
7. Persist research findings in the authorized result artifacts and reusable operating lessons here.

## Efficient interaction patterns

### State-first navigation

**Rule:** Recover the durable campaign state and controller-owned handoff before broad target exploration.

### Portfolio and program interaction

**Rule:** Treat controller-owned `state/research/` artifacts as read-only evidence and make worker proposals only through the authorized handoff mechanism.

### Research execution

**Rule:** Prefer the existing research-program runner, deterministic validators, and safe local reproduction paths before writing bespoke execution infrastructure.

### Differential evidence

**Rule:** Pair interesting observations with a nearby null/control or alternate representation before deepening them.

### Failure handling

**Rule:** First classify whether the failure belongs to the target, worker/container, gateway, controller, persistence, or evaluator layer.

### Persistence

**Rule:** Leave a compact handoff containing what changed, what was independently verified, what remains uncertain, and exactly one useful next action.

## Verified interaction lessons

Add only lessons that generalize beyond one transient activation.

| Lesson | Status | Evidence / context | Reusable rule |
|---|---|---|---|
| Durable campaign state must be checked before new exploration | VERIFIED | Repeated activation continuity and bootstrap records | Inspect persistent research state before recreating a search frontier. |
| Worker-visible benchmark state is not authoritative | VERIFIED | Blind benchmark architecture | Treat worker-visible challenge context as evidence to inspect, not ground truth. |
| Controller-owned `state/research/` must remain read-only during worker sessions | VERIFIED | Blind workspace and program-handoff contract | Propose changes through the authorized handoff artifact; do not mutate controller state directly. |
| Differential/null controls improve evidence efficiency | VERIFIED | Repeated reproduced findings with control comparisons | Add a nearby control before spending effort on deeper reproduction. |
| Environment-layer observations are separate from target evidence | VERIFIED | Environment-awareness repair on 2026-10-06 | Classify runner, gateway, permission, and evaluator behavior as infrastructure evidence unless independently connected to the research question. |

## Environment and tool constraints

Record stable constraints only when they materially affect the efficient execution path.

Examples:
- command/tool allowlists;
- isolated-network behavior;
- blind-workspace boundaries;
- persistence or evaluator gates;
- known Kilo gateway limitations.

Do not record secrets, hidden evaluator details, private reasoning, or raw sensitive target data.

## Failed approaches worth avoiding

| Approach | Status | Why it is inefficient or unsafe | Better path |
|---|---|---|---|
| Treating controller/evaluator output as target evidence | VERIFIED_NEGATIVE | It collapses infrastructure and target layers | Establish the observation directly against the authorized target and validate independently. |
| Repeating a broad scan without changing the information objective | VERIFIED_NEGATIVE | It consumes activations without increasing discovery probability | Change hypothesis class, representation, surface coverage, or differential control. |
| Mutating controller-owned research state from the worker | VERIFIED_NEGATIVE | It breaks the trusted state boundary | Use the authorized worker-to-controller handoff artifact. |

## Update contract for future generations

Add or revise a playbook entry only when all are true:

1. The lesson is generalizable.
2. It was directly observed or independently verified.
3. It can save future research effort, reduce errors, or improve evidence quality.
4. It does not duplicate an existing entry.

Use this compact format:

```
Lesson: <generalizable operational lesson>
Status: VERIFIED | UNVERIFIED | VERIFIED_NEGATIVE
Evidence: <where it was established>
Reusable rule: <one concrete instruction>
```

Do not turn this file into an activation diary. Detailed chronology belongs in activation logs; research conclusions belong in durable research state; this file stores reusable **how-to-operate knowledge**.
