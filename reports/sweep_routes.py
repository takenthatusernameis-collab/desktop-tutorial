import json, subprocess, sys
routes = []
import re
# Build candidate routes: enumerate from known JS route tables + brute force common namespaces
namespaces = []
def add(prefix, items):
    for it in items:
        routes.append(prefix + it)
# Known static + brute-forced common patterns
brute = [f"/{i}" for i in range(1,10)]
brute += ["/me","/whoami","/profile","/settings","/account","/dashboard","/admin","/console","/debug","/health","/status","/ping","/version"]
brute += ["/export","/import","/upload","/download","/delete","/rename","/move","/copy","/clone"]
brute += ["/ai","/chat","/chatbot","/assistant","/llm","/inference","/embed","/vector","/rag"]
brute += ["/feedback","/survey","/vote","/like","/bookmark","/flag","/report"]
brute += ["/nft","/web3","/wallet","/token","/airdrop","/mint","/stake","/farm"]
brute += ["/coupon","/redeem","/voucher","/giftcard","/loyalty","/points","/referral"]
brute += ["/support","/ticket","/"+"help","/faq","/contact"]
add("/rest/user/", ["settings","preferences","preferences2","tokens","sessions","change-password","reset-password","email","phone","avatar","photo","images","media","cards","addresses","addresses2","memberships","subscriptions","orders","order-history","cart","basket","history","activity","audit","notifications","messages","chats","friends","following","followers","connections","groups","teams"])
add("/rest/", ["users","admins","roles","permissions","permissions2","groups","teams","sessions","tokens","logs","audit","activity","debug","config","settings","secrets","keys","certificates","backups","snapshots","recovery","recoveryanswers","security-answers","captcha","continue-code","continue-codes","web3","nft","nfts","nftUnlocked","ai","chatbot","assistant","llm","inference"])
add("/api/", ["Users","user","users2","Accounts","account","accounts","Sessions","tokens","Roles","permissions","Logs","audit","Activity","debug","Config","settings","Challenges","challenges","Feedbacks","feedback","Reviews","review","Complaints","complaints","Products","product","Carts","cart","Baskets","basket","Orders","order","Memberships","membership","Coupons","coupon","RecoveryAnswers","recovery-answers","SecurityAnswers","security-answers","Web3","web3","NFT","nfts","AI","chatbot","Metrics","metrics"])
add("/assets/public/", ["uploads","data","keys","secrets","config","backup","dump",".git",".env","backup.sql","database.sql"])
json.dump(routes, open("/workspace/reports/routes_candidates.json","w"), indent=0)
print(len(routes), "routes")
