# Authorized Training Target

## Purpose

This file defines the sole security-testing target for autonomous research activations until a different target is explicitly authorized.

## Target

- **Application:** OWASP Juice Shop
- **Image:** `bkimminich/juice-shop:20.2.0`
- **Endpoint:** `http://127.0.0.1:3000/*`
- **Authorization basis:** Repository-controlled GitHub Actions service container provisioned by the workflow for this job only.
- **Lifecycle:** Ephemeral. The target exists only for the workflow activation and is destroyed with the runner/job.

## Scope

Permitted interaction is limited to the Juice Shop instance exposed on the loopback address above. Do not interact with unrelated hosts, public Juice Shop demo infrastructure, third-party systems, or external targets from this training activation.

## Research posture

Treat this as a clean-room authorized security laboratory. Prefer discovery without challenge hints, validate findings against false positives, preserve negative results, and record enough evidence for independent review.

## Hard boundary

This authorization does not grant permission to expand scope, scan arbitrary Internet hosts, seek credentials, exfiltrate data, establish persistence, or perform destructive/disruptive actions.
