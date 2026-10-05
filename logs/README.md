# Activation Logs

Keep concise human-readable activation records for substantive work, important failures, and durable handoffs.

**Timestamped logging is the default operational standard for new activation records.** When timestamps are observable, include UTC timestamps for activation start and finish and for consequential work/checkpoints that make progress easier to reconstruct. Prefer ISO 8601 format such as `2026-10-03T15:43:00Z`. A timestamp records the UTC time at which the logged event or action actually occurred; never backfill or infer a precise time that was not observed. When only a date or coarser time is known, record only that known precision rather than inventing a precise time.

The date-based activation filename is the canonical container for that day's records. Do not create a separate file per activation minute. Append each substantive activation to `logs/ACTIVATION-YYYY-MM-DD.md` under a section such as `## Activation — 21:56 UTC`, while keeping observed ISO 8601 UTC timestamps inside the section authoritative.

Use the following handoff structure for every substantive record:

**CHANGED**
actual files/code or durable state changed

**VERIFIED**
exact commands, workflow stages, tests, evaluations, or evidence that actually succeeded after final relevant changes

**UNVERIFIED**
anything execution-dependent, unavailable, denied, or not independently checked

**NEXT**
the smallest useful bounded action for a fresh activation

Do not invent timestamps, metrics, findings, or verification. Do not store credentials or confidential information here.
