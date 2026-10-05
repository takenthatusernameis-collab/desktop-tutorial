import json

findings = [
    {
        "title": "[F1] Unauthenticated user-object exposure via GET /rest/memories (password hash, totpSecret, deluxeToken, lastLoginIp)",
        "analysis": "GET /rest/memories returns all stored memories as JSON with full embedded User objects, returned unauthenticated. Each User object exposes email, a 32-hex password hash, role, a 40-hex deluxeToken, totpSecret, and lastLoginIp. Verified: 200 / 10 records; user fields [createdAt, deletedAt, deluxeToken, email, id, isActive, lastLoginIp, password, profileImage, role, totpSecret, updatedAt, username]; password hash e.g. 9283f1b2e9669749081963be0462e466; deluxeToken present but is not a signed JWT (auth attempts with it yield 'Invalid signature'). Controls (e.g. /rest/basket) return 401. Severity: this is broader than exposing the logged-in user's hash — every user's hash + TOTP secret is readable by any caller, enabling offline hash cracking and TOTP-token compromise. Maps to sensitive-data-exposure / Password Hash Leak class.",
        "false_positive_check": "The route requires no Authorization and returns the same 10-record response with a bogus Bearer token as with no auth; 401 for truly gated routes (basket). The deluxeToken caveat limits account hijack value but does not reduce the exposure finding: hash + TOTP secret are leaked regardless. Not explained by a benign 'display' requirement, as User objects are never needed to render a memory listing (caption + image path suffice).",
        "request": {
            "method": "GET",
            "url": "http://lab-mutator:3000/rest/memories",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "[F2] /api/SecurityAnswers/: read-gated / unauthenticated-write-open gap (broken access control)",
        "analysis": "GET /api/SecurityAnswers/ returns 401 (no Authorization), but POST /api/SecurityAnswers/ with no credentials and an empty body returns 201 and creates a new SecurityAnswer record server-side with a server-generated id (23, 24, 25 observed incrementing across requests/boot), UserId=null, SecurityQuestionId=null, answer=null. The read path is protected while the write path accepts unauthenticated writes with no ownership validation, no question-answer binding, and no input validation. Repeating the POST continues the id sequence, proving server-side persistence. Neighboring write routes are gated (GET /api/Complaints/ /Cards/ -> 401; /Addresses/ /Reviews/ /Questions/ /Memberships/ -> 500 'Unexpected path'). Severity: unauthenticated injection of security-answer records with null UserId — data-integrity and potential security-answer poisoning/privilege-escalation vector.",
        "false_positive_check": "GET consistently 401; POST consistently 201 with fresh server id; id sequence increments (23->24->25) proving the writes are real and persistent, not a local echo. The endpoint is genuinely auth-misconfigured (read protected, write open), not a benign API design: posting to a read-gated write resource without credentials should 401 or 403.",
        "request": {
            "method": "POST",
            "url": "http://lab-mutator:3000/api/SecurityAnswers/",
            "headers": {"Content-Type": "application/json"},
            "body": {}
        }
    },
    {
        "title": "[F5] /rest/user/security-question?email= unauthenticated account enumeration and security-question disclosure",
        "analysis": "GET /rest/user/security-question?email=<addr> returns 200 for both existing and nonexistent emails, but the body discriminates: configured users return {\"question\":{\"id\":7,\"question\":\"Name of your favorite pet?\",...}} while nonexistent addresses return 200 / 2 B {}. Verified: bjoern@owasp.org -> id=7 'Name of your favorite pet?'; nonexistent -> {}. Severity: unauthenticated account existence enumeration combined with disclosure of the account's security-question text (usable for targeted social-engineering / answer-guessing against the associated account).",
        "false_positive_check": "Differential verified across both branches: existing user returns full question JSON, nonexistent returns exactly 2 B '{}'. Neighbors gated (authentication-details 401, other /rest/user/* 500). Not benign enumeration: the endpoint exists to look up an answer for an account the caller already owns; exposing question+existence to arbitrary callers is an information-disclosure failure, not intended public behavior.",
        "request": {
            "method": "GET",
            "url": "http://lab-mutator:3000/rest/user/security-question?email=bjoern%40owasp.org",
            "headers": {},
            "body": {}
        }
    },
    {
        "title": "[F6] Unauthenticated PUT on /api/Products/{id} -> persistent product-tampering (broken object-level authorization)",
        "analysis": "PUT /api/Products/{id} with no Authorization header returns 200 and persists arbitrary product field modification (name/description/price) in the backend. Verified round-trip: GET /api/Products/1 -> name 'Apple Juice (1000ml)' price 1.99; unauth PUT {'name':'BENCHMARK-TAMPER-999','price':666.66} -> 200 'success'; fresh GET -> name 'BENCHMARK-TAMPER-999' price 666.66; write observed across separate requests (persisted, not session-local). Severity: any caller can modify any product's listing data without credentials (broken object-level authorization / mass-assignment on the product update route). Mapped to the product-tampering / improper-input-validation class. (Product restored to original values after verification; mutation is ephemeral.)",
        "false_positive_check": "Cross-request persistence confirmed: the modification written in one request is readable in a subsequent, independent GET — not a local echo. The same PUT with a valid Authorization header is not the vector; unauthenticated PUT alone succeeds. Neighboring writes gated (POST /api/Products 401; DELETE /api/Products/1 401) — the vulnerability is the inconsistent authorization on the PUT update method, i.e. an authorization gap on a specific HTTP method.",
        "request": {
            "method": "PUT",
            "url": "http://lab-mutator:3000/api/Products/1",
            "headers": {"Content-Type": "application/json"},
            "body": {"name": "BENCHMARK-TAMPER-999", "price": 666.66}
        }
    },
    {
        "title": "[F7] Cleartext CAPTCHA-answer leak via GET /rest/captcha (CAPTCHA defeat vector; POST submission path broken in this mutation)",
        "analysis": "GET /rest/captcha returns JSON containing the server-generated CAPTCHA expression AND its cleartext answer: e.g. {\"captchaId\":5,\"captcha\":\"5-4-9\",\"answer\":\"-8\"}. The answer is verifiably correct (5-4-9 = -8). Severity: the answer is served to every unauthenticated caller, defeating the CAPTCHA entirely; a client can retrieve the current answer without solving it. In this mutation the POST /api/Feedbacks/ submission path currently rejects even the correct answer ('Wrong answer to CAPTCHA'), a mutation-side break in the submission flow — so the complete bypass path is not reproducible, but the answer-leak vector itself is.",
        "false_positive_check": "The answer field is verified against the expression server-side arithmetic on multiple boots (7*4*7=196, 6-3+1=-3, 5-7-5=-7, 1*6-9=-3, 5-4-9=-8). The leak is independent of the broken submission path: GET always returns cleartext. The finding is presented as a verified information-disclosure / CAPTCHA-defeat vector, not as a fully working bypass, because the POST submission path rejects correct answers in this boot.",
        "request": {
            "method": "GET",
            "url": "http://lab-mutator:3000/rest/captcha",
            "headers": {},
            "body": {}
        }
    }
]

out = {"findings": findings}
with open("/workspace/reports/benchmark_findings.json", "w") as f:
    json.dump(out, f, indent=1)

# validate contract shape
import json as _j
d = _j.load(open("/workspace/reports/benchmark_findings.json"))
for i, f in enumerate(d["findings"]):
    assert all(k in f for k in ["title","analysis","false_positive_check"]), f
    assert all(k in f["request"] for k in ["method","url","headers","body"]), f
print("VALIDATED:", len(d["findings"]), "findings; contract shape OK")
