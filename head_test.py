import subprocess

base = "http://lab-mutator:3000"


def head(path):
    r = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w",
         "%{http_code}:%{http_size}:%{http_content_type}", base + path],
        capture_output=True, text=True,
    )
    return r.stdout.strip()


paths = [
    "/admin",
    "/api/Products/",
    "/assets/i18n/en.json",
    "/assets/public/.env",
    "/.env",
    "/.git/config",
    "/swagger.json",
    "/assets/public/backup.sql",
    "/backup.sql",
    "/assets/public/README.md",
    "/assets/public/legal.md",
    "/ftp/legal.md",
]
for p in paths:
    print(repr(p), "->", repr(head(p)))
