# Persistence Policy

## Purpose

The runner is disposable, but useful authorized-security research work should become durable repository state.

The persistence boundary is safety-based, not cleanliness-based.

## Allowed

Relevant ordinary repository content may persist, including research notes, safe test harnesses, tests, deterministic tooling, diagnostics, evidence summaries, activation records, state, negative/inconclusive results, methodology, and process improvements.

## Always protected

The autonomous worker must not modify or persist changes to:
- .github/workflows/**
- .kilo/**
- AGENTS.md
- ENTERPRISE.md
- MANUAL_SETUP.md
- PERSISTENCE_POLICY.md
- AUTHORIZED_TARGET.md
- HARDCORE_BENCHMARK.md
- lab/generate_benchmark.py
- lab/generate_solver_feedback.py
- lab/mutator.py
- lab/evaluate_benchmark.py
- lab/test_benchmark.py
- lab/benchmark_campaign.py
- lab/kilo-worker.Dockerfile
- lab/kilo_gateway_proxy.py
- lab/README.md

 `SOLVER_FEEDBACK.md` is a trusted workflow-generated aggregate learning packet. The worker may read it but must not modify it; after a successful independent evaluation the trusted workflow may regenerate and persist it. If feedback generation fails, the previous trusted version must be restored before persistence.

The trusted workflow restores protected control-plane paths before persistence. The benchmark history file and evaluator-generated aggregate reports are durable evidence and may persist.

## Never persist

Reject high-confidence unsafe material such as private keys, API tokens or credentials, secret-bearing .env/credential files, secret-bearing .pem or .key files, symbolic links, generated Python bytecode/build artifacts, or copied target secrets/personal data.

Do not silently weaken the persistence gate.

## On violation

Report the blocked category, affected path(s), whether useful work remains only in the disposable runner, and the smallest safe recovery step.

## Promotion rule

A helper may become durable infrastructure when there is evidence that future activations benefit from it.

Objective:

maximum useful authorized-security research continuity subject to a small, explicit safety boundary.

## Campaign workspace boundary

Each numbered agent receives a disposable, intentionally curated workspace. Historical scratch scripts, controller-only benchmark artifacts, and worker-visible challenge-state extracts are not part of the active agent workspace.

The controller exchanges only a controller-selected task contract and compact per-agent result memo between sessions. Agent 10 may create candidate findings/program-handoff artifacts, but only the controller-owned final synthesis may promote canonical artifacts.

The campaign state is durable at the repository persistence boundary, but private Kilo context is never a handoff mechanism.

The absence of controller-excluded files inside an agent workspace is therefore an intentional blindness boundary, not evidence of repository data loss.

## Controller-only benchmark state

The trusted workflow may persist the active hidden benchmark in controller-only workflow artifacts so an unsolved research campaign can survive multiple activations. This state is not worker-visible repository content and must not be copied into the worker workspace.

