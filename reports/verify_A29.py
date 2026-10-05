import hashlib, json, subprocess, os

os.makedirs("reports", exist_ok=True)

def probe(headers=None, query=None):
    cmd = ["curl", "-s"]
    if query:
        cmd.append("http://lab-mutator:3000" + headers["path"] + "?" + query)
    else:
        cmd.append("http://lab-mutator:3000" + headers["path"])
    if headers:
        for k, v in headers.items():
            if k not in ("path", "query"):
                cmd += ["-H", f"{k}: {v}"]
    meta = {}
    with open("/tmp/probe_body", "wb") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        r.stderr.strip()
    # Re-run with -w for status/size/content-type (body already written to file)
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}\n%{http_code}\n%{http_size}\n%{content_type}\n"]
    if query:
        cmd.append("http://lab-mutator:3000" + headers["path"] + "?" + query)
    else:
        cmd.append("http://lab-mutator:3000" + headers["path"])
    if headers:
        for k, v in headers.items():
            if k not in ("path", "query"):
                cmd += ["-H", f"{k}: {v}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip().splitlines()
    meta = {
        "HTTP": out[0] if len(out) > 0 else "0",
        "HTTPSIZE": out[2] if len(out) > 2 else "0",
        "HTTPCT": out[3] if len(out) > 3 else "",
    }
    with open("/tmp/probe_body", "rb") as f:
        body = f.read().decode("utf-8", errors="replace")
    size = meta.get("HTTPSIZE", str(len(body.encode())))
    ct = meta.get("HTTPCT", "")
    return int(meta.get("HTTP", 0)), size, ct, hashlib.sha256(body.encode()).hexdigest(), hashlib.md5(body.encode()).hexdigest(), body

probes_list = [
    ("27_primary", {"path": "/rest/user/security-question"}),
    ("27_accept_json", {"path": "/rest/user/security-question", "Accept": "application/json"}),
    ("27_redirect", {"path": "/redirect", "query": "continue="}),
    ("27_control", {"path": "/api/Nonexistent/1"}),
    ("97_metrics", {"path": "/metrics"}),
    ("oracle", {"path": "/api/Challenges/"}),
]

results = []
for name, req in probes_list:
    status, size, ct, sha256, md5, body = probe(headers=req, query=req.get("query"))
    results.append((name, status, size, ct, sha256, md5, body))

with open("reports/verify_A29_out.json", "w") as f:
    for name, status, size, ct, sha256, md5, body in results:
        f.write(f"=== {name} ===\n")
        f.write(f"status={status} size={size} ct={ct} sha256={sha256} md5={md5}\n")
        f.write(body + "\n\n")

for name, status, size, ct, sha256, md5, body in results:
    print(f"{name}: {status} {size} sha256={sha256[:20]}... ct={ct}")
