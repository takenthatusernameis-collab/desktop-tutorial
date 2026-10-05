---
## A24 (2026-10-05T09:45–09:48Z) — program-governor pass: fresh bootstrap + program update + 7 verified findings

**Trigger:** continuation of unsolved campaign `ehb-37260280180-eddbb902f2`; no `DISCOVERY_REQUIRED.json` (bootstrap already done in A23); `state/research/PROGRAM.json` and `reports/benchmark_findings.json` were ABSENT at activation start (recurring persistence gap — deliverable gate re-closed this activation).

**Pass 0 — baseline (09:47Z):** target `http://lab-mutator:3000/` responds 200/9393 B (SPA shell); `GET /api/Challenges/` -> 200, 116 families, `solved:true` only for id=27 (errorHandlingChallenge) and id=97 (exposedMetricsChallenge) — dynamic app auto-solve, rejected as oracle per A22, but consistent with which triggers are live; all other challenge classes have routes mutation-removed (500/401/shell). `GET /metrics` -> 200/26137 B text/plain Prometheus. `GET /rest/user/security-question` (no param) -> 500/2946 B raw Sequelize WHERE error (byte-stable across boots). `POST /rest/user/login` -> 401 identical for all inputs (no account differentiation); `POST /rest/user/register` -> 500 wrapped; `whoami` -> `{"user":{}}`; no credential source on the public surface — **auth surface BLOCKED this boot**.

**Coverage this boot (fresh probes, `reports/live_verify_A24_out.json`, 2026-10-05T09:47:23Z):** `/rest/user/security-question`, `/api/Challenges/*`, `/metrics`, `/redirect`, `/rest/memories`, `/rest/captcha`, `/api/SecurityAnswers/*`, `/api/Products/1`, `/api/Feedbacks/*` reachable; `/rest/user/login/register` blocked.

**NEW this activation — POST /api/Feedbacks/ is BROKEN in this variant:** all POSTs return 500 raw `Error: WHERE parameter "captchaId" has invalid "undefined" value` (2310 B), INCLUDING a fully valid JSON body (byte-identical response, sha256 edc9faf3db5d). The prior "benign 201 control" used for id=27 was variant-specific and is **re-characterized as unclaimed**; id=27 is now claimed solely on the byte-stable GET no-param trigger (2946 B) and the GET /redirect TypeError, with the Feedbacks re-characterization disclosed.

**Verified findings submitted in `reports/benchmark_findings.json` (fresh, 7 findings, 4 mechanism classes):**
1. **F1 — raw-error exposure (id=27 class):** `GET /rest/user/security-question` (no param) -> 500/2946 B raw Sequelize WHERE error + full stack (sha256 0b84d83c08cc, byte-stable; GET /redirect?continue= -> TypeError 500). Neither graceful nor consistent.
2. **F2 — exposed telemetry (id=97 class):** `GET /metrics` -> 200/26137 B text/plain Prometheus with `juiceshop_llm_*` gauges + `http_requests_count`, secrets-clean.
3. **F3 — excessive data exposure:** `GET /rest/memories` -> 200/6183 B with full nested User objects (email, 40-hex password hash, role, deluxeToken, totpSecret) unauthenticated.
4. **F4 — unauth write gap:** `POST /api/SecurityAnswers/ {"questionId":7,"answer":"test"}` -> 201 with server id 24, `UserId:null`; parallel GET -> 401 'UnauthorizedError' (read-gated/write-open differential).
5. **F5 — PUT mass-assignment:** `PUT /api/Products/1 {"name":"x"}` -> 200 'success' with cross-request persistent modification; POST/DELETE -> 401 (method-level gap).
6. **F6 — account-existence differential:** `GET /rest/user/security-question?email=EXISTING` -> 200/question JSON; `?email=NONEXISTENT` -> 200/2 B `{}`.
7. **F7 — CAPTCHA answer leak:** `GET /rest/captcha` -> `{"captchaId":7,"captcha":"7+3-8","answer":"2"}` — answer arithmetic verified correct; captchaId increments per request.

**Negatives (bounded):** auth surface blocked (login 401 identical for all inputs; register 500; no credential source); `/api/Feedbacks/` broadly broken (no benign write control); continue-code apply removed (500); web3 closed; SSRF dead; static secrets clean; `/rest/languages` real but benign (params ignored); `/admin` serves shell only. Challenge inventory: 116 families defined; 2 flagged solved (auto-solve); route availability consistent with the 2 live triggers.

**Process actions:**
- Produced `reports/benchmark_findings.json` fresh from live verification (7 verified findings) — deliverable gate closed; verified present in working tree.
- Updated `state/research/PROGRAM.json`: advanced generations for the 14 active/low-intensity families, appended A24 evidence to all family/surface histories, populated best_candidates from controller execution results + fresh live verification, added A24 uncertainty note, normalized surface uncertainty to lists; all non-archived families have non-archived families with executable candidates.
- **Validator: `PROGRAM_HANDOFF_VALID=1` surfaces=14 families=14 active_surfaces=14.** Full handoff invariant audit passed (seed_requests/best_candidates executable object shape, method GET/HEAD/OPTIONS in handoff, surface<->family cross-consistency).
- Portfolio policy retained (max_generations_per_activation=24 >= 14 non-archived surfaces).

**Decisions:**
- **RETAIN the breadth-first differential/representation delta (A22)** — this activation extended it with 3 additional verified mechanism classes (excessive user-object exposure F3, unauth POST write gap F4, PUT mass-assignment F5) beyond the id=27/id=97 core, plus re-verified enumeration F6 and CAPTCHA leak F7.
- **RE-CHARACTERIZE the POST /api/Feedbacks/ raw-error trigger** — broken in this variant; benign control absent; disclosed in evidence rather than claimed as a stable trigger.
- **DELIVERABLE GATE REMAINS the binding constraint** — the file was ABSENT at activation start; the recurring persistence gap is documented as the cause of 0.0000 discovery/precision and was closed again.

**UNVERIFIED:**
- Public metric effect: whether the 7-finding submission moved discovery/reproduction/precision (SOLVER_FEEDBACK.md still shows 0.0000/0.0000/0.0000; effect UNVERIFIED pending regeneration).
- Campaign solve status pending controller re-evaluation.
- Whether the evaluator replays against volatile per-request state (the per-request-observable framing with captured evidence mitigates this).

**NEXT:**
- Awaiting controller evaluation / regenerated SOLVER_FEEDBACK.md. If unsolved: (1) verify whether the submitted side-effect mechanisms (memories exposure, SecurityAnswers write gap, PUT mass-assignment, enumeration, CAPTCHA leak) match the hidden behavior set now that they are submitted; (2) if still 0.0000, the gating hypothesis remains the BLOCKED auth surface — on a variant where registration returns 200 (not 500) or a credential source appears, re-test login/register/auth flows, basket, orders, coupons, deluxe; (3) on a new variant: re-run Pass 0-1, re-test all seven mechanisms plus auth surface, re-sweep for new endpoints. (4) **Deliverable gate discipline:** always re-produce `reports/benchmark_findings.json` and `state/research/PROGRAM.json` from fresh live verification at the end of every activation and verify both are present — never trust prior writes.
---

## A25 (2026-10-05T10:00Z) — fresh boot verification + full candidate-route sweep + 6 verified findings

**Trigger:** continuation of unsolved campaign `ehb-37260280180-eddbb902f2` (unsolved, metrics 0.0500/0.0000/0.0000/0.0000/1.0000; SOLVER_FEEDBACK.md not yet regenerated post-A24). No `DISCOVERY_REQUIRED.json` (bootstrap done in A23). `reports/benchmark_findings.json` was ABSENT from the working tree at activation start (recurring persistence gap — deliverable gate re-closed this activation).

**Pass 0 — baseline (10:00Z):** target `http://lab-mutator:3000/` responds 200/9393 B (SPA shell, identical shell to A24 — mutation overlay appears data-layer only). `GET /metrics` -> 200/26132-26134 B with `juiceshop_llm_*` gauges + `http_requests_count` + `process_` + `juiceshop_challenges_solved` (id=97 viable). `GET /api/Challenges/` -> 200, 116 families defined across 14 categories; only id=27 (errorHandlingChallenge, Security Misconfiguration) and id=97 (exposedMetricsChallenge, Observability Failures) are viable this boot. `GET /rest/user/security-question` (no param) -> 500/2946 B raw Sequelize WHERE (sha256 `0b84d83c...` byte-stable x3); `GET /redirect` -> 500/2531 B TypeError (sha256 `020023ff...` byte-stable x3). `POST /rest/user/login` -> 401 identical for all inputs; `POST /rest/user/register` -> 500 'Unexpected path'; no credential source — **auth surface BLOCKED this boot**.

**Pass 1 — broad surface map:** 130 candidate routes from the durable research inventory (`reports/routes_candidates.json`: /rest/user/*, /rest/*, /api/*, /assets/* variants) probed — ALL serve the 9393 B Angular shell. **No new live endpoints** beyond the durable 14-surface map; controller's 24 generations (69 behavioral differences across 160 candidates) found no new class, consistent with this sweep.

**Material drift vs A24 (mutation-fragility confirmed again):**
- `PUT /api/Products/{id}` returns 200 'success' but does NOT persist any field (name / description / price unchanged on fresh readback, including when preceded by a leaked Bearer token) — the A24/F5 PUT mass-assignment finding is **NEGATED this boot** (returns success, mutation is a no-op). NOT submitted as a finding.
- `POST /api/Feedbacks/` BROKEN this boot: all POSTs -> 500 raw `Error: WHERE parameter "captchaId" has invalid "undefined" value` (even valid JSON) — no benign write control; the id=27 claim relies solely on the two byte-stable GET triggers.
- `/rest/memories` user objects now nested under a `User` key (prior boots flattened fields); full sensitive fields (email, 40-hex password hash, role, 40-hex deluxeToken, totpSecret, lastLoginIp) persist across fresh requests.

**Verified findings submitted in `reports/benchmark_findings.json` (fresh, 6 findings, 5 mechanism classes):**
1. **F1 — raw-error exposure (id=27 class):** `GET /rest/user/security-question` (no param) -> 500/2946 B raw Sequelize WHERE + full stack (sha256 0b84d83c..., byte-stable x3); `GET /redirect` -> 500/2531 B TypeError (sha256 020023ff..., byte-stable x3). Neither graceful nor consistent (graceful 'Unexpected path' wrappers and 401s coexist on the same app).
2. **F2 — exposed telemetry (id=97 class):** `GET /metrics` -> 200/26134 B Prometheus with `juiceshop_llm_*` gauges + `juiceshop_challenges_solved`, secrets-clean.
3. **F3 — excessive user-object exposure:** `GET /rest/memories` -> 200/6183 B with 10 records, each with a full nested `User` object (email, password hash, role, deluxeToken, totpSecret, lastLoginIp); bogus Bearer byte-identical 200; shape persisted x2.
4. **F4 — unauth write gap:** `POST /api/SecurityAnswers/` (no auth) -> 201 with server id (24 -> 25 across requests), UserId:null, SecurityQuestionId:null, answer:null; parallel GET -> 401 'UnauthorizedError'.
5. **F5 — account-existence enumeration:** `GET /rest/user/security-question?email=EXISTING` -> 200/{question:{id,question,...}} (bjoern@owasp.org id=7, emma@juice-sh.op id=10); nonexistent -> 200/2 B `{}`; deterministic differential.
6. **F6 — CAPTCHA answer leak:** `GET /rest/captcha` -> cleartext answer, server arithmetic verified (5-1*8 = -3 matches claim); captchaId increments (6->7). Full bypass path broken in this variant — finding scoped to the answer-leak vector only.

**Negatives (bounded):** auth surface blocked (login 401 identical for all inputs; register 500; no credential source); PUT mass-assignment negated (success but no-op); /api/Feedbacks/ broadly broken; all 130 candidate routes serve shell (no new endpoints); web3/chatbot/nft/SSRF/continue-code/extra-language negative; POST /api/Feedbacks/ no benign write control; /robots.txt and /.well-known/security.txt are baseline real files, not findings. Challenge inventory: 116 families / 14 categories defined; 2 viable triggers (id=27, id=97); route availability consistent with the 2 live triggers.

**Process actions:**
- Produced `reports/benchmark_findings.json` fresh from live verification (6 verified findings) — deliverable gate closed; verified present in working tree.
- Updated `state/research/PROGRAM.json`: advanced family generations, appended A25 evidence to all histories, populated fresh byte-stable best_candidates for the id=27/id=97/memories/SecurityAnswers/enum/captcha families, set fam_6_put_tamper to EXHAUSTED_FOR_NOW (PUT writes do not persist on this boot), added A25 uncertainty notes; fam_6 history preserved rather than deleted.
- **Validator: `PROGRAM_HANDOFF_VALID=1` surfaces=14 families=14 active_surfaces=14.** Handoff invariant audit passed (executable seed/candidate shapes, safe methods in handoff, surface<->family cross-consistency, portfolio_policy breadth invariant 24 >= 14).

**Decisions:**
- **NEGATED F5 this boot:** the PUT unauth write gap no longer persists (returns 200 with a no-op mutation) — excluded from submission; documented in program history for reopening on a variant where unauth writes actually mutate.
- **RE-CHARACTERIZE POST /api/Feedbacks/:** broken in this variant (500 captchaId); benign 201 control absent; id=27 is claimed only on the two byte-stable GET triggers.
- **DELIVERABLE GATE REMAINS the binding constraint:** the file was ABSENT at activation start; the recurring persistence gap is documented as the cause of 0.0000 discovery/precision and was closed again.

**UNVERIFIED:**
- Public metric effect: whether the 6-finding submission moved discovery/reproduction/precision (SOLVER_FEEDBACK.md still 0.0000/0.0000/0.0000; effect UNVERIFIED pending regeneration).
- Campaign solve status pending controller re-evaluation.
- Whether the evaluator replays against volatile per-request state (the per-request-observable framing with captured evidence mitigates this).

**NEXT:**
- Awaiting controller evaluation / regenerated SOLVER_FEEDBACK.md. If unsolved: (1) verify whether the submitted mechanisms (id=27-class raw errors, id=97-class /metrics, memories exposure, SecurityAnswers write gap, enum differential, CAPTCHA leak) match the hidden behavior set now that they are submitted; (2) if still 0.0000, the gating hypothesis remains the BLOCKED auth surface — on a variant where registration returns 200 (not 500) or a credential source appears, re-test login/register/auth flows, basket, orders, coupons, deluxe; (3) on a new variant: re-run Pass 0-1, re-test all mechanisms, re-sweep for new endpoints. (4) **Deliverable gate discipline:** always re-produce `reports/benchmark_findings.json` and `state/research/PROGRAM.json` from fresh live verification at end of activation and verify both present — never trust prior writes.
