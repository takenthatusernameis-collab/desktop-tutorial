---
task_id: "ILLUSTRATIVE-SCORING-EXAMPLE"
version: "1.0.0"
authorized_target: "local-fake-sandbox-v2"
scope_boundary: "http://sandbox.internal:8080/*"
auth_verified_by: "researcher-illustration (fictional lab record for triage testing only)"
source_reference: "sample-candidates/authorized-scoring-example.md"
source_system: "illustrative example only"
hypothesis: "Illustrative only: XSS reflected from an unparameterized search string at /search?q= on sandbox.internal."
why_this_target: "Illustrative only: search endpoints are common XSS surface in internal sandboxes."
success_criteria: "Illustrative only: payload <script>alert(1)</script> appears in HTML response body without encoding."
scope_size: "large"
hypothesis_specificity: "specific"
novelty: "potentially novel"
evidence_available: "substantial"
---

# Illustrative Scoring Example — fictional sandbox only

> **NOT A REAL TARGET.** This file exists to exercise the scoring path of
> `scripts/triage_tasks.py`. Do not treat anything in this file as an actual
> research target, scope, or authorization.

This example sets `auth_verified_by` to a non-empty value so that the
authorization gate passes and the candidate is scored. A genuine intake record
must have the authorization verified against a real, authorized target.
