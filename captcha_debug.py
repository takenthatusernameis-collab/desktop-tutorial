import subprocess, json

base = "http://lab-mutator:3000"


def get_cap():
    r = subprocess.run(
        ["curl", "-s", "-X", "GET", base + "/rest/captcha"], capture_output=True, text=True)
    return json.loads(r.stdout)


def post_cap(captchaId, answer):
    body = json.dumps({"rating": 5, "comment": "probe", "captchaId": captchaId})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", base + "/api/Feedbacks", "-H", "Content-Type:application/json",
         "-d", body], capture_output=True, text=True)
    return r.stdout[:120]


for i in range(3):
    cap = get_cap()
    print("GET", i, "->", cap)
    print("  POST id=%s answer=%s ->" % (cap["captchaId"], cap["answer"]), post_cap(cap["captchaId"], cap["answer"]))
    print("  POST id=99999 answer=0   ->", post_cap(99999, "0"))
    print("  POST id=%s answer=WRONG  ->" % cap["captchaId"], post_cap(cap["captchaId"], "WRONG"))
print("\n=== POST without captchaId ===")
r = subprocess.run(["curl", "-s", "-X", "POST", base + "/api/Feedbacks", "-H", "Content-Type:application/json",
                    "-d", json.dumps({"rating": 0, "comment": "zero star"})], capture_output=True, text=True)
print("rating 0 no captcha ->", r.stdout[:120])
print("rating 5 no captcha ->", post_cap(0, "")[:120])
