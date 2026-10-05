import subprocess, json

base = "http://lab-mutator:3000"
token = json.loads(subprocess.run(["curl", "-s", "-X", "POST", base + "/rest/user/login",
    "-H", "Content-Type:application/json",
    "-d", json.dumps({"email": "adminhacker@x.com", "password": "AdminPass123!", "rememberMe": False})],
    capture_output=True, text=True).stdout)["authentication"]["token"]


def req(method, path, data=None, auth=False):
    cmd = ["curl", "-s"] + (["-X", method] if method != "GET" else [])
    if auth:
        cmd += ["-H", "Authorization:Bearer " + token]
    if data:
        cmd += ["-H", "Content-Type:application/json", "-d", data]
    r = subprocess.run(cmd + [base + path], capture_output=True, text=True)
    body = r.stdout[:200].replace("\n", " ")
    return r.returncode, body


paths = [
    ("/api/SecurityQuestions", "GET", None, False),
    ("/api/Quantitys", "GET", None, False),
    ("/api/Recycles", "GET", None, False),
    ("/api/Hints", "GET", None, False),
    ("/dataerasure", "POST", '{"userId":1}', False),
    ("/dataerasure", "POST", '{"email":"bjoern@owasp.org"}', False),
    ("/file-upload", "GET", None, False),
    ("/file-upload", "POST", '{"name":"x.png"}', False),
    ("/rest/chat", "GET", None, False),
    ("/rest/chat", "POST", '{"message":"hi"}', False),
    ("/rest/continue-code-findIt", "GET", None, False),
    ("/rest/continue-code-findIt/apply/", "GET", None, False),
    ("/rest/continue-code-findIt/apply/123", "GET", None, False),
    ("/rest/continue-code-fixIt", "GET", None, False),
    ("/rest/continue-code-fixIt/apply/", "GET", None, False),
    ("/rest/continue-code-fixIt/apply/123", "GET", None, False),
    ("/rest/order-history", "GET", None, True),
    ("/rest/wallet/balance", "GET", None, True),
    ("/rest/web3", "GET", None, False),
    ("/rest/image-captcha/", "GET", None, False),
    ("/rest/user/authentication-details/", "GET", None, True),
    ("/rest/user/change-password?current=", "GET", None, True),
    ("/rest/user/change-password?current=abc&new=", "PUT", None, True),
    ("/rest/products", "GET", None, False),
    ("/api/Deliverys", "GET", None, False),
    ("/api/Addresss", "GET", None, False),
    ("/rest/track-order", "GET", None, False),
    ("/rest/continue-code", "GET", None, False),
]

for p, m, d, a in paths:
    rc, body = req(m, p, d, a)
    print("%s %-35s rc=%d  %s" % (m, p, rc, body))
