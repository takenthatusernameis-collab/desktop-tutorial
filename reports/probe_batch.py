#!/usr/bin/env python3
import json, urllib.request

BASE = "http://lab-mutator:3000"

ROUTES = [
    "/rest/user/whoami", "/rest/user/login", "/rest/user/register", "/rest/user/change-password",
    "/rest/user/forgot-password", "/rest/user/security-question?email=test@example.com",
    "/rest/user/authentication-details", "/rest/user/address", "/rest/user/addresses",
    "/rest/user/order-history", "/rest/user/basket", "/rest/user/recovery-answer",
    "/rest/user/security-answer", "/rest/memories", "/rest/products",
    "/rest/products/search?q=test", "/rest/products/1", "/rest/orders", "/rest/coupons",
    "/rest/coupon", "/rest/reviews", "/rest/feedbacks", "/rest/security-answers",
    "/rest/addresses", "/rest/cards", "/rest/cart", "/rest/basket", "/rest/web3/nftUnlocked",
    "/rest/web3/nftMint", "/rest/web3/nftClaim", "/rest/web3/collect", "/rest/web3/deposit",
    "/rest/web3/transfer", "/rest/web3/address", "/rest/web3/verifySignature",
    "/rest/web3/addressBalance", "/rest/continue-code", "/rest/continue-code/apply?code=123456",
    "/rest/continue-code/list", "/rest/leaderboard", "/rest/redirect?continue=http://example.com",
    "/rest/chat", "/rest/admin", "/rest/score-board", "/rest/photo-wall", "/rest/recycle",
    "/rest/reset-password", "/rest/file-upload", "/rest/captcha",
    "/api/Challenges/", "/api/Memories/", "/api/RecoveryAnswers/", "/api/Questions/",
    "/api/Addresses/", "/api/Reviews/", "/api/Cards/", "/api/Orders/", "/api/Feedbacks/",
    "/api/Coupons/", "/api/Carts/", "/api/Baskets/", "/api/SecurityAnswers/", "/api/Uploads/",
    "/api/Exports/", "/api/Jwt", "/api/Jwt/", "/api/User", "/api/User/",
    "/api/CaptchaRiddle/0", "/api/CaptchaRiddle/3", "/api/Captcha/", "/api/SecurityAnswer/",
    "/api/Complaints/", "/api/SecurityAnswers/",
]

METHODS = ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH", "POST"]

def req(path, method, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = body.encode()
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return (resp.status, (resp.getheader("Content-Type") or ""),
                (resp.getheader("Access-Control-Allow-Origin") or ""),
                resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return (e.code, (e.headers.get("Content-Type") or ""),
                (e.headers.get("Access-Control-Allow-Origin") or ""),
                e.read().decode("utf-8", "replace"))
    except Exception as e:
        return ("ERR", "", "", str(e))

out = []
for path in ROUTES:
    for m in METHODS:
        st, ct, cors, b = req(path, m)
        out.append({"path": path, "method": m, "status": st,
                    "content_type": ct, "cors": cors,
                    "body": b[:80].replace("\n", " ")})
json.dump(out, open("/workspace/reports/probe_results.json", "w"), ensure_ascii=False, indent=1)
summary = {r["path"] + "|" + r["method"]: (r["status"], r["body"]) for r in out}
print(json.dumps(summary, indent=1))
print("total:", len(out))
