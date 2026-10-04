# Bug Bounty Research Enterprise

A research-only autonomous enterprise for improving the process of progressing lawful, authorized bug-bounty and ethical-security research tasks.

The architecture is inspired by the enterprise/control-plane separation used by X, but its highest-order objective is:

> Continuously improve the enterprise's ability to choose, investigate, validate, document, and learn from authorized security-research opportunities while preserving scope, safety, evidence integrity, and truthful reporting.

## Architecture

- GitHub Actions: deterministic 5-minute worker heartbeat with single-run concurrency.
- Kilo Code worker: bounded autonomous research execution in a disposable runner.
- Repository: durable institutional memory, evidence, state, and handoffs.
- Git history: audit trail.
- ChatGPT supervisor: independent daily supervisory layer for process quality, bottlenecks, integrity, and higher-order improvement.

This repository is not a live offensive-security environment. Research must remain inside explicitly authorized bug-bounty programs, owned labs, CTF/sandbox environments, or other clearly permitted targets.

See ENTERPRISE.md, AGENTS.md, PERSISTENCE_POLICY.md, MANUAL_SETUP.md, and .kilo/wakeup-prompt.md.
