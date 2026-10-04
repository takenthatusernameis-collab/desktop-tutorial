# Authorized Training Target

## Purpose

This file defines the sole security-testing target for autonomous research activations in the disposable benchmark environment.

## Target

- **Application:** Juice Shop-derived blind benchmark variant.
- **Base image:** `bkimminich/juice-shop:20.2.0`
- **Worker endpoint:** `http://lab-mutator:3000/*`
- **Authorization basis:** Repository-controlled GitHub Actions job that provisions the intentionally vulnerable base application plus a per-activation mutation overlay inside isolated Docker networks.
- **Lifecycle:** Ephemeral. The target and hidden evaluator exist only for the workflow activation and are destroyed during cleanup.
- **Ground truth:** Generated per activation and kept outside the worker-visible workspace.

## Scope

Permitted interaction is limited to the worker-facing benchmark endpoint above. The worker must not interact with the underlying Juice Shop container directly, the evaluator-only network, public Juice Shop infrastructure, third-party systems, or unrelated external targets.

## Research posture

Treat this as a clean-room authorized security laboratory. Perform black-box discovery without challenge hints or answer keys, validate findings against false positives, preserve negative results, and record enough evidence for independent replay.

## Hard boundary

This authorization does not grant permission to expand scope, scan arbitrary Internet hosts, seek credentials, exfiltrate data, establish persistence, or perform destructive/disruptive actions.