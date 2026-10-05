import subprocess, re, json

base = "http://lab-mutator:3000"
js = open('/tmp/main.js').read()

# Extract API endpoint patterns from the JS
patterns = set()
# patterns like hostServer+"/path" or hostServer+"/path"+
for m in re.finditer(r'hostServer\s*\+\s*`([^`]+)`', js):
    patterns.add(m.group(1))
for m in re.finditer(r'hostServer/`([^`]+)`', js):
    patterns.add(m.group(1))
for m in re.finditer(r'`\$\{hostServer\}/([^"`]+)', js):
    patterns.add(m.group(1))
# /rest/* and /api/* literals in http calls
for m in re.finditer(r'["/\'](/(?:rest|api)/[A-Za-z0-9_./{}?=&@:;$%\-\[\]])', js):
    patterns.add(m.group(1))

paths = sorted(set(p for p in patterns if p.startswith('/')))
print("Found %d candidate paths" % len(paths))
for p in paths[:120]:
    print(repr(p))