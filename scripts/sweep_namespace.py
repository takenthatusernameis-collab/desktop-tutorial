import urllib.request, json, sys, time
ns = sys.argv[1]  # e.g. /rest, /api, /api/v1, /api/v2, /i18n, /assets/js, /admin
base = "http://lab-mutator:3000"
seen = set()
results = []
def probe(path):
    key = path.split("?")[0].split("/")[0:5]
    k = "/".join(key)
    if k in seen:
        return
    seen.add(k)
    try:
        req = urllib.request.Request(base+path, method="GET", headers={"User-Agent":"Mozilla/5.0 (research)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read()
        ctype = r.headers.get("content-type","")
        snap = (body[:120] if len(body)>120 else body.decode("utf-8","ignore")).replace("\n"," ")
        results.append([path, r.status, len(body), ctype.split(";")[0], snap])
    except urllib.error.HTTPError as e:
        body = e.read()
        results.append([path, e.code, len(body), "text/html", str(e.read())[:80]])
    except Exception as ex:
        results.append([path, "ERR", 0, "", f"{type(ex).__name__}:{str(ex)[:60]}"])
# build candidate paths from known Juice Shop route patterns
import re
cands = []
if ns == "/rest":
    cands = ["/rest/account/create","/rest/account/login","/rest/account/me","/rest/admin/challenges","/rest/admin/config","/rest/admin/dashboard","/rest/admin/health","/rest/admin/metrics","/rest/admin/reviews","/rest/addresses","/rest/auth/csrf","/rest/basket","/rest/basket/bought","/rest/basket/cleanup","/rest/basket/items","/rest/basket/status","/rest/cards","/rest/captcha","/rest/checkout","/rest/complaints","/rest/coupons","/rest/custom","/rest/continue-code","/rest/coupon","/rest/errors/forbidden","/rest/errors/generic","/rest/errors/timeout","/rest/errors/unexpected","/rest/feedback","/rest/flags","/rest/forgot-password","/rest/i18n","/rest/i18n/resources","/rest/addresses","/rest/i18n/resources/en","/rest/i18n/resources/de","/rest/legal","/rest/locations","/rest/memories","/rest/memberships","/rest/addresses","/rest/nft","/rest/nftUnlocked","/rest/nftUnlock","/rest/nftUnlock","/rest/notes","/rest/orders","/rest/orders/active","/rest/orders/history","/rest/orders/checkout","/rest/password-change","/rest/payment","/rest/products","/rest/products/search","/rest/products/lowstock","/rest/products/categories","/rest/products/top10","/rest/privacy","/rest/privacy-policy","/rest/profile","/rest/questions","/rest/quotes","/rest/redirect","/rest/reviews","/rest/scoreboards","/rest/security-question","/rest/user/authentication-details","/rest/user/continue-code","/rest/user/email","/rest/user/feedback","/rest/user/login","/rest/user/login/check","/rest/user/logout","/rest/user/me","/rest/user/membership","/rest/user/password-hash","/rest/user/register","/rest/user/register/check","/rest/user/security-question","/rest/user/security-answer","/rest/user/tos","/rest/user/tos/accepted","/rest/wallet","/rest/web3"]
    # add numeric IDs
    for p in ["/rest/admin/reviews","/rest/basket/items","/rest/cards","/rest/complaints","/rest/coupons","/rest/memories","/rest/orders","/rest/products","/rest/questions","/rest/reviews","/rest/users","/rest/addresses","/rest/notes","/rest/nft","/rest/wallet","/rest/payment","/rest/feedback","/rest/quotes","/rest/legal","/rest/locations","/rest/flags","/rest/security-question","/rest/custom","/rest/profile","/rest/scoreboards","/rest/privacy","/rest/privacy-policy","/rest/payment","/rest/checkout","/rest/bought"]:
        cands.append(p)
    for i in range(1,61):
        for suf in ["/orders/history","/orders/active","/orders/items","/products","/products/lowstock","/questions","/reviews","/addresses","/cards","/complaints","/coupons","/memberships","/notes","/wallet","/cards/items","/orders"]:
            cands.append(f"/rest/{i}{suf}" if i==1 else f"/rest/users/{i}")
elif ns == "/api":
    cands = ["/api/Addresses","/api/Addresses/","/api/Cards","/api/Complaints","/api/Coupons","/api/Memberships","/api/Notes","/api/Orders","/api/Products","/api/Products/","/api/Questions","/api/Reviews","/api/UserAccounts","/api/UserAccounts/","/api/Challenges","/api/Captcha","/api/Captcha/verify","/api/Feedbacks","/api/Feedbacks/","/api/RecoveryAnswers","/api/RecoveryAnswers/","/api/SecurityAnswers","/api/SecurityAnswers/","/api/ProductLabels","/api/NFT","/api/Wallet","/api/PrivacyPolicy","/api/SecurityPolicy","/api/ContinueCode","/api/ContinueCode/apply","/api/ContinueCode/apply/","/api/PasswordChange","/api/ResetPassword","/api/Scoreboard","/api/Scoreboard/","/api/Customer","/api/Restock","/api/Restock/apply","/api/Memories","/api/Memories/","/api/Questions","/api/Questions/","/api/Reviews","/api/Reviews/","/api/Complaints/","/api/Cards/","/api/Addresses/","/api/Memberships/","/api/Notes/","/api/Coupons/"]
elif ns == "/api/v1":
    cands = ["/api/v1/users","/api/v1/products","/api/v1/orders","/api/v1/customers","/api/v1/addresses","/api/v1/cards","/api/v1/memberships","/api/v1/notes","/api/v1/reviews","/api/v1/questions","/api/v1/complaints","/api/v1/coupons"]
elif ns == "/i18n":
    cands = ["/i18n/en","/i18n/de","/i18n/fr","/i18n/es","/i18n/pt","/i18n/nl","/i18n/zh","/i18n/ja","/i18n/ko","/i18n/ru","/i18n/ar","/i18n/it","/i18n/tr","/i18n/pl","/i18n/cs","/i18n/hu","/i18n/ro","/i18n/uk","/i18n/vi","/i18n/th","/i18n/unknown","/i18n/missing","/i18n/extra","/i18n/resources","/i18n/resources/en.json","/i18n/resources/de.json"]
elif ns == "/assets/js":
    cands = ["/assets/js/main.js","/assets/js/runtime.js","/assets/js/polyfills.js","/assets/js/vendor.js","/assets/js/main.js.map","/assets/js/en.json","/i18n/en.json"]
elif ns == "/admin":
    cands = ["/admin","/admin/","/admin/users","/admin/challenges","/admin/dashboard"]
elif ns == "/graphql":
    cands = ["/graphql","/graphql/","/graphql/playground"]
cands = list(dict.fromkeys(cands))
for c in cands:
    probe(c)
    time.sleep(0.03)
with open(f"/workspace/reports/sweep_{ns.replace('/','_')}_live.json","w") as f:
    json.dump(results, f)
print(f"wrote {len(results)} probes for {ns}")
