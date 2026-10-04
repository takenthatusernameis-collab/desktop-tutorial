# Bug Bounty Research Enterprise

A research-only autonomous enterprise for improving the process of progressing lawful, authorized bug-bounty and ethical-security research tasks.

The architecture is inspired by the enterprise/control-plane separation used by X, but its highest-order objective is:

> Continuously improve the enterprise's ability to choose, investigate, validate, document, and learn from authorized security-research opportunities while preserving scope, safety, evidence integrity, and truthful reporting.

## Architecture

- GitHub Actions: deterministic 5-minute worker heartbeat with single-run concurrency.
- Kilo Code worker: bounded autonomous research execution in a disposable runner.
- Repository: durable institutional memory, evidence, state, lineage, and handoffs.
- Git history: audit trail.
- ChatGPT supervisor: independent daily supervisory layer for process quality, bottlenecks, integrity, and higher-order improvement.
- Endless blind benchmark: each activation gets a fresh Juice Shop-derived mutation variant with hidden ground truth and independent evidence replay.
- Evolutionary research mode: controlled mutation and evaluator-driven progression are now used for benchmark difficulty/shape selection.

The evolutionary mode is inspired abstractly by AlphaEvolve-style research loops: generated candidates are evaluated, promising candidates are retained, and later candidates can inherit or mutate useful structure. It is optional and never allowed to mutate authorization, safety, scope, credential, or trusted-control invariants.

This repository is not a live offensive-security environment. Research must remain inside explicitly authorized bug-bounty programs, owned labs, CTF/sandbox environments, or other clearly permitted targets.

See ENTERPRISE.md, AGENTS.md, EVOLUTION.md, PERSISTENCE_POLICY.md, MANUAL_SETUP.md, and .kilo/wakeup-prompt.md.

## Endless benchmark flow

```
Generate hidden variant -> isolate target -> blind Kilo research -> submit reproducible evidence -> hidden replay evaluation -> persist aggregate result -> adapt difficulty/shape
```

The target is ephemeral and repository-controlled. No VPS, Replit deployment, public target authorization, or persistent external service is required.
