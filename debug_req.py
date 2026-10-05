import subprocess, json
base = "http://lab-mutator:3000"
token = json.loads(subprocess.run(["curl","-s","-X","POST",base+"/rest/user/login",
    "-H","Content-Type:application/json","-d",json.dumps({"email":"adminhacker@x.com","password":"AdminPass123!","rememberMe":False})],
    capture_output=True,text=True).stdout)["authentication"]["token"]
cmd = ["curl","-s","-X","POST",base+"/rest/basket/1/products/1/quantity",
    "-H","Authorization:Bearer "+token,"-H","Content-Type:application/json","-d",'{"quantity":5}']
r = subprocess.run(cmd,capture_output=True,text=True)
print('cmd:', ' '.join(cmd))
print('rc:', r.returncode)
print('stdout:', repr(r.stdout[:200]))
print('stderr:', repr(r.stderr[:200]))
