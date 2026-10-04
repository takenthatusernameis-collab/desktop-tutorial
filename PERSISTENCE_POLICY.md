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
- lab/mutator.py
- lab/evaluate_benchmark.py
- lab/README.md

The trusted workflow restores these paths before persistence. The benchmark history file and evaluator-generated aggregate reports are durable evidence and may persist.

## Never persist

Reject high-confidence unsafe material such as private keys, API tokens or credentials, secret-bearing .env/credential files, secret-bearing .pem or .key files, symbolic links, generated Python bytecode/build artifacts, or copied target secrets/personal data.

Do not silently weaken the persistence gate.

## On violation

Report the blocked category, affected path(s), whether useful work remains only in the disposable runner, and the smallest safe recovery step.

## Promotion rule

A helper may become durable infrastructure when there is evidence that future activations benefit from it.

Objective:

maximum useful authorized-security research continuity subject to a small, explicit safety boundary.
