import subprocess, json, time

base = "http://lab-mutator:3000"
token = None

def get_admin():
    global token
    if token:
        return token
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", base + "/rest/user/login",
         "-H", "Content-Type:application/json",
         "-d", json.dumps({"email": "adminhacker@x.com", "password": "AdminPass123!", "rememberMe": False})],
        capture_output=True, text=True).stdout
    token = json.loads(out)["authentication"]["token"]
    return token

def req(method, path, hdrs=None):
    cmd = ["curl", "-s"] + (["-X", method] if method != "GET" else [])
    hdrs = hdrs or {}
    hdrs["Authorization"] = "Bearer " + get_admin()
    for k, v in hdrs.items():
        cmd += ["-H", k + ":" + v]
    cmd += ["-o", "/tmp/gp_out", "-w", "%{http_code}:%{http_size}", base + path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    body = open("/tmp/gp_out", errors="ignore").read()
    return r.stdout.strip(), body

paths = [
    ("GET", "/api/UserAccounts/26"),
    ("GET", "/api/UserAccounts/1"),
    ("GET", "/api/Feedbacks/1"),
    ("GET", "/api/Reviews"),
    ("GET", "/api/Coupons"),
    ("GET", "/api/Orders"),
    ("GET", "/api/Memberships"),
    ("GET", "/api/Questions"),
    ("GET", "/api/Addresses"),
    ("GET", "/api/Cards"),
    ("GET", "/api/Complaints"),
    ("GET", "/api/Wallet"),
    ("GET", "/api/NFT"),
    ("GET", "/api/SecurityAnswers"),
    ("GET", "/rest/basket"),
    ("GET", "/rest/basket/1"),
    ("GET", "/rest/user/whoami"),
    ("GET", "/rest/user/profile"),
    ("POST", "/api/Reviews"),
    ("DELETE", "/api/Feedbacks/1"),
    ("GET", "/rest/user/security-question?email=bjoern@owasp.org"),
    ("GET", "/api/Export"),
    ("GET", "/api/data-export"),
    ("GET", "/rest/user/export"),
    ("GET", "/admin"),
    ("GET", "/admin/"),
    ("GET", "/api/admin"),
    ("GET", "/admin/dashboard"),
]

for m, p in paths:
    code, body = req(m, p)
    code = int(code.split(":")[0])
    preview = body[:60].replace("\n", " ")
    print(f"{m:6} {p:35} {code:4} {preview}")
