#!/usr/bin/env python3
"""
Blind benchmark campaign harness for lab-mutator:3000.
Black-box only: mapping, request variation, differential testing,
independent reproduction, falsification. No harness internals.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "http://lab-mutator:3000"
OUT = "reports/campaign.json"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def req(path, method="GET", headers=None, data=None):
    """Single request; returns (status, headers_dict, body_bytes, body_text, raw_exception)."""
    url = BASE + path
    hdrs = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    body_bytes = None
    if data is not None:
        if isinstance(data, str):
            body_bytes = data.encode()
            hdrs["Content-Type"] = "application/json; charset=utf-8"
        else:
            body_bytes = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json; charset=utf-8"
    req_obj = urllib.request.Request(url, data=body_bytes, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=30) as resp:
            status = resp.status
            hdrs_d = dict(resp.headers)
            raw = resp.read()
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = raw.hex()
            return status, hdrs_d, raw, text, None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = raw.hex()
        return e.code, dict(e.headers), raw, text, None
    except Exception as e:
        return None, {}, b"", "", repr(e)

def probe(path, methods=None):
    if methods is None:
        methods = ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH", "POST"]
    results = {}
    for m in methods:
        s, h, raw, text, exc = req(path, method=m)
        results[m] = {"status": s, "length": len(raw),
                      "cors": h.get("Access-Control-Allow-Origin", ""),
                      "allow": h.get("Allow", ""),
                      "exc": exc,
                      "body": text[:500]}
    return results

def probe_list(paths, method="GET"):
    """Probes a list of paths with a single method; records baseline behavior."""
    out = {"probe_at": now(), "method": method, "paths": {}}
    for p in paths:
        out["paths"][p] = probe(p, methods=[method])
    return out

def differential(label, cases):
    """cases: list of (name, method, path, headers, body). Returns structured result."""
    res = {"label": label, "at": now(), "cases": []}
    for name, method, path, headers, body in cases:
        s, h, raw, text, exc = req(path, method=method, headers=headers, data=body)
        res["cases"].append({
            "name": name,
            "status": s,
            "length": len(raw),
            "cors": h.get("Access-Control-Allow-Origin", ""),
            "allow": h.get("Allow", ""),
            "body": text[:700],
            "exc": exc
        })
    return res

def main():
    start = now()
    raw = {"campaign_started": start, "target": BASE}

    # Pass 0: baseline + key endpoints (fast)
    baseline = probe_list([
        "/", "/robots.txt", "/sitemap.xml", "/rest/memories", "/rest/captcha",
        "/rest/user/whoami", "/rest/wallet/balance", "/rest/basket",
        "/rest/products/search", "/api/Challenges/", "/api/SecurityAnswers/",
        "/api/Feedbacks/", "/rest/web3/nftUnlocked", "/rest/user/security-question?email=test@example.com",
        "/rest/user/login", "/rest/chat", "/rest/order-history", "/rest/deluxe-membership",
        "/redirect", "/redirect?continue=http://example.com", "/rest/languages",
        "/rest/repeat-notification", "/rest/country-mapping", "/api/Complaints/",
        "/api/Cards/", "/api/Addresss/", "/rest/continue-code-findIt",
        "/rest/continue-code-findIt?continueCode=123", "/rest/2fa/status",
        "/rest/2fa/setup", "/rest/2fa/verify", "/rest/2fa/disable",
    ], method="GET")

    # Pass 1: multi-method sweep of the critical REST surface
    critical = [
        "/rest/memories", "/rest/captcha", "/rest/products/search", "/rest/products/search?q=Apple",
        "/rest/user/whoami", "/rest/user/authentication-details", "/rest/user/basket",
        "/rest/user/addresses", "/rest/user/security-question?email=admin@owasp.org",
        "/rest/user/security-question?email=", "/rest/user/change-password",
        "/rest/admin", "/rest/order-history", "/rest/web3/nftUnlocked",
        "/rest/web3/submitKey", "/rest/deluxe-membership",
        "/rest/continue-code-findIt", "/rest/continue-code-findIt?apply",
        "/rest/continue-code-fixIt", "/rest/continue-code-fixIt?apply",
        "/rest/continue-code/apply/abc123", "/rest/chat", "/rest/2fa/status",
        "/rest/2fa/setup", "/rest/2fa/verify", "/rest/2fa/disable",
        "/rest/languages", "/rest/repeat-notification", "/rest/country-mapping",
        "/api/Feedbacks/", "/api/Challenges/", "/api/SecurityAnswers/",
        "/api/Complaints/", "/api/Cards/", "/api/Addresss/", "/api/Memories/",
        "/rest/nft/1", "/rest/nft/collect", "/redirect", "/redirect?continue=http://127.0.0.1:22",
    ]
    methodsweep = probe_list(critical)

    # Pass 2: differential testing (hypothesis-driven pairs)
    diffs = []

    # D1: captcha answer leak vs submission
    capt = req("/rest/captcha")[3]  # body text
    captcha_json = json.loads(capt)
    captcha_id = captcha_json.get("captchaId")
    leaked_answer = captcha_json.get("answer")
    diff_captcha = differential("D1_captcha_leak_vs_submission", [
        ("captcha_leaked_answer", "GET", "/rest/captcha", None, None),
        ("feedback_wrong_answer", "POST", "/api/Feedbacks/",
         {"Content-Type": "application/json"},
         {"feedback": "Test feedback", "captchaId": captcha_id, "answer": "000000"}),
        ("feedback_correct_answer", "POST", "/api/Feedbacks/",
         {"Content-Type": "application/json"},
         {"feedback": "Test feedback", "captchaId": captcha_id, "answer": leaked_answer}),
        ("feedback_no_captcha", "POST", "/api/Feedbacks/",
         {"Content-Type": "application/json"},
         {"feedback": "Test feedback"}),
    ])
    diffs.append(diff_captcha)

    # D2: memories public vs auth-gated controls (read the data first)
    mem = req("/rest/memories")
    diff_memories = differential("D2_memories_public_vs_controls", [
        ("GET_memories", "GET", "/rest/memories", None, None),
        ("GET_memories_with_fake_auth", "GET", "/rest/memories",
         {"Authorization": "Bearer fake-token-12345"}, None),
        ("GET_wallet_balance", "GET", "/rest/wallet/balance", None, None),
        ("GET_user_authentication_details", "GET", "/rest/user/authentication-details", None, None),
        ("GET_basket", "GET", "/rest/basket", None, None),
        ("GET_user_security_question", "GET", "/rest/user/security-question?email=test@example.com", None, None),
    ])
    diffs.append(diff_memories)

    # D3: SecurityAnswers read(401) vs write(POST unauth)
    diff_securityanswers = differential("D3_securityAnswers_write_gap", [
        ("GET_401", "GET", "/api/SecurityAnswers/", None, None),
        ("POST_no_auth", "POST", "/api/SecurityAnswers/",
         {"Content-Type": "application/json"},
         {"questionId": 7, "answer": "A test answer", "email": "probe@example.com"}),
        ("POST_no_auth_v2", "POST", "/api/SecurityAnswers/",
         {"Content-Type": "application/json"},
         {"questionId": 7, "answer": "A test answer v2", "email": "probe2@example.com"}),
        ("POST_empty_object", "POST", "/api/SecurityAnswers/",
         {"Content-Type": "application/json"}, {}),
        ("POST_very_empty", "POST", "/api/SecurityAnswers/",
         {"Content-Type": "application/json"}, []),
        ("POST_missing_fields", "POST", "/api/SecurityAnswers/",
         {"Content-Type": "application/json"}, {"answer": "only answer"}),
    ])
    diffs.append(diff_securityanswers)

    # D4: products search param mutation + SQLi
    diff_products = differential("D4_products_search_param_mutation", [
        ("GET_no_param", "GET", "/rest/products/search", None, None),
        ("GET_q=Apple", "GET", "/rest/products/search?q=Apple", None, None),
        ("GET_q=", "GET", "/rest/products/search?q=", None, None),
        ("GET_q=test", "GET", "/rest/products/search?q=test", None, None),
        ("GET_q_unsafe_singlequote", "GET", "/rest/products/search?q=%27", None, None),
        ("GET_q_or_tautology", "GET", "/rest/products/search?q=%27%20OR%20%271%27=%271", None, None),
        ("GET_q_union", "GET", "/rest/products/search?q=%27%20UNION%20SELECT%201,2,3--", None, None),
        ("GET_q_drop", "GET", "/rest/products/search?q=%3B%20DROP%20TABLE%20products--", None, None),
        ("GET_q_nullbyte", "GET", "/rest/products/search?q=apple%00", None, None),
        ("GET_q_xss", "GET", "/rest/products/search?q=%3Cscript%3E", None, None),
        ("GET_q_xss_html", "GET", "/rest/products/search?q=<script>", None, None),
    ])
    diffs.append(diff_products)

    # D5: web3 / rest/web3/* multi-method
    web3_routes = ["/rest/web3/nftUnlocked", "/rest/web3/nft", "/rest/web3/mint",
                   "/rest/web3/submitKey", "/rest/web3/wallet"]
    web3_results = probe_list(web3_routes, method="GET")
    web3_post = {"paths": {p: probe(p, methods=["POST", "PUT", "DELETE", "PATCH"]) for p in ["/rest/web3/submitKey"]}}

    # D6: /redirect SSRF-ish variants (no outbound; just behavior)
    diff_redirect = differential("D6_redirect_variants", [
        ("GET_redirect", "GET", "/redirect", None, None),
        ("GET_redirect_continue_example", "GET", "/redirect?continue=http://example.com", None, None),
        ("GET_redirect_continue_local", "GET", "/redirect?continue=http://127.0.0.1:22", None, None),
        ("GET_redirect_continue_blank", "GET", "/redirect?continue=", None, None),
    ])
    diffs.append(diff_redirect)

    # D7: order-history variants
    diff_order = differential("D7_order_history_variants", [
        ("GET_order_history", "GET", "/rest/order-history", None, None),
        ("GET_order_history_empty", "GET", "/rest/order-history?orderId=", None, None),
    ])
    diffs.append(diff_order)

    # D8: deluxe membership
    diff_deluxe = differential("D8_deluxe_membership", [
        ("GET_deluxe", "GET", "/rest/deluxe-membership", None, None),
        ("POST_deluxe_noauth", "POST", "/rest/deluxe-membership", None, None),
        ("POST_deluxe_credit", "POST", "/rest/deluxe-membership",
         {"Content-Type": "application/json"}, {"paymentMode": "credit"}),
    ])
    diffs.append(diff_deluxe)

    # D9: continue-code variants
    diff_continue = differential("D9_continue_code_variants", [
        ("GET_continue_findIt", "GET", "/rest/continue-code-findIt", None, None),
        ("GET_continue_fixIt", "GET", "/rest/continue-code-fixIt", None, None),
        ("GET_continue_findIt_apply", "GET", "/rest/continue-code-findIt?apply", None, None),
        ("GET_continue_fixIt_apply", "GET", "/rest/continue-code-fixIt?apply", None, None),
        ("GET_continue_findIt_code", "GET", "/rest/continue-code-findIt?continueCode=123", None, None),
        ("GET_continue_fixIt_code", "GET", "/rest/continue-code-fixIt?continueCode=123", None, None),
        ("GET_continue_apply_path", "GET", "/rest/continue-code/apply/abc123", None, None),
    ])
    diffs.append(diff_continue)

    # D10: captchaId increment / re-use across two fresh ids (bypass attempt recheck)
    c1 = req("/rest/captcha")[3]
    c1j = json.loads(c1)
    c2 = req("/rest/captcha")[3]
    c2j = json.loads(c2)
    fb = req("/api/Feedbacks/", method="POST", headers={"Content-Type": "application/json"},
             data={"feedback": "check", "captchaId": c1j["captchaId"], "answer": c1j["answer"]})
    diff_captcha_reuse = differential("D10_captchaId_fresh_vs_fresh", [
        ("captcha_first", "GET", "/rest/captcha", None, None),
        ("captcha_second", "GET", "/rest/captcha", None, None),
        ("feedback_first_correct", "POST", "/api/Feedbacks/",
         {"Content-Type": "application/json"},
         {"feedback": "check", "captchaId": c1j["captchaId"], "answer": c1j["answer"]}),
    ])
    diffs.append(diff_captcha_reuse)

    # Challenge inventory
    chal = req("/api/Challenges/")[3]
    chal_data = json.loads(chal)
    challenge_count = len(chal_data.get("data", []))

    raw["baseline"] = baseline
    raw["methodsweep"] = methodsweep
    raw["differentials"] = diffs
    raw["web3_get"] = web3_results
    raw["web3_methods"] = web3_post
    raw["challenge_inventory"] = {"count": challenge_count}
    raw["campaign_finished"] = now()

    with open(OUT, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"Campaign complete. Output: {OUT}")
    print(json.dumps({"baseline": baseline, "methodsweep": methodsweep}, indent=0))
    print("differentials written:", [d["label"] for d in diffs])
    print("challenges:", challenge_count)

if __name__ == "__main__":
    main()
