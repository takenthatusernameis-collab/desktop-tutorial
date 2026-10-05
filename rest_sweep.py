import subprocess, json

base = "http://lab-mutator:3000"


def is_shell(body):
    return body.startswith("<!--") or body.strip().startswith("<!doctype") or body.strip().startswith("<html")


def req(path, auth=False):
    cmd = ["curl", "-s"]
    if auth:
        token = json.loads(subprocess.run(["curl", "-s", "-X", "POST", base + "/rest/user/login",
            "-H", "Content-Type:application/json",
            "-d", json.dumps({"email": "adminhacker@x.com", "password": "AdminPass123!", "rememberMe": False})],
            capture_output=True, text=True).stdout)["authentication"]["token"]
        cmd += ["-H", "Authorization:Bearer " + token]
    r = subprocess.run(cmd + [base + path], capture_output=True, text=True)
    return r.returncode, r.stdout[:120].replace("\n", " ")


# enumerate /rest/* patterns
patterns = [
    "/rest/", "/rest/user/", "/rest/api/", "/rest/admin/", "/rest/auth/", "/rest/metrics", "/rest/feedback",
    "/rest/feedbacks", "/rest/review", "/rest/reviews", "/rest/photo", "/rest/photos", "/rest/upload", "/rest/uploads",
    "/rest/basket", "/rest/orders", "/rest/order", "/rest/cart", "/rest/wallet", "/rest/web3", "/rest/nft", "/rest/token",
    "/rest/security", "/rest/captcha", "/rest/2fa", "/rest/two-factor", "/rest/coupons", "/rest/coupon",
    "/rest/products", "/rest/product", "/rest/users", "/rest/useraccounts", "/rest/notifications",
    "/rest/continue-code", "/rest/notifications", "/rest/jobs", "/rest/jobs/", "/rest/jobs/apply",
    "/rest/qr", "/rest/qr-codes", "/rest/deluxe", "/rest/deluxe-membership", "/rest/memories", "/rest/memory",
    "/rest/security-answers", "/rest/questions", "/rest/addresses", "/rest/cards", "/rest/complaints",
    "/rest/memberships", "/rest/membership", "/rest/metrics", "/rest/system", "/rest/config", "/rest/health",
    "/rest/version", "/rest/info", "/rest/status", "/rest/whoami", "/rest/profile", "/rest/account",
    "/rest/accounting", "/rest/accounting/", "/rest/jobs", "/rest/recycling", "/rest/photo-wall",
    "/rest/privacy-security", "/rest/data-export", "/rest/change-password", "/rest/two-factor-authentication",
    "/rest/last-login-ip",
]

print("=== /rest/* sweep (unauth first, then auth) ===")
for p in patterns:
    rc, out = req(p)
    marker = "REAL " if (rc == 0 and not is_shell(out)) else "shll"
    print("%s %s  ->  %s" % (marker, p, out))
