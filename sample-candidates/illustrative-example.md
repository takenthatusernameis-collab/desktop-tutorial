---
task_id: "ILLUSTRATIVE-EXAMPLE"
version: "1.0.0"
authorized_target: "example-local-fake-lab"
scope_boundary: "http://example.local/*"
auth_verified_by: ""
source_reference: "sample-candidates/illustrative-example.md"
source_system: "illustrative example only"
hypothesis: "Illustrative only: a debug endpoint at /debug/vars leaks internal configuration on example.local."
why_this_target: "Illustrative only: the host name suggests an internal lab environment."
success_criteria: "Illustrative only: HTTP 200 with JSON containing PASSWORD or SECRET_KEY keys."
scope_size: "small"
hypothesis_specificity: "moderate"
novelty: "common"
evidence_available: "none"
---

# Illustrative Example — fictional local lab only

> **NOT A REAL TARGET.** This file exists to demonstrate the intake format and to
> make `scripts/triage_tasks.py` testable in isolation. Do not treat anything in
> this file as an actual research target, scope, or authorization.

This example intentionally sets `auth_verified_by` to a placeholder so that the
authorization gate rejects it. A genuine intake record must have `auth_verified_by`
populated (and verification status set to "verified") before any scoring is
performed — see D4 in research_state.md.
