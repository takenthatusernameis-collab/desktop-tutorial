#!/bin/bash
# Fresh independent reproduction of the id=27 trigger class (target http://lab-mutator:3000)
# Captures status, size, sha256, and content-type for the three representations + null control.
BASE="http://lab-mutator:3000"
OUT="agent26_fresh_probes_$(date -u +%Y-%m-%dT%H%M%SZ).txt"
echo "Fresh id=27 trigger-class reproduction — $OUT" > "$OUT"
echo "Target: $BASE ; session started UTC: $(date -u +%Y-%m-%dT%H%M%SZ)" >> "$OUT"
echo "================================================================" >> "$OUT"

# Representation 1: GET /rest/user/security-question (no Accept -> text/html)
for i in 1 2; do
  t=$(date -u +%Y-%m-%dT%H%M%SZ)
  b=$(curl -s -w "\n%{http_code}\n%{size_download}\n%{content_type}" "$BASE/rest/user/security-question")
  sc=$(echo "$b" | sed -n '2p'); sz=$(echo "$b" | sed -n '3p'); ct=$(echo "$b" | sed -n '4p')
  body=$(echo "$b" | sed -n '1p')
  sh=$(printf '%s' "$body" | sha256sum | cut -d' ' -f1)
  head=$(printf '%s' "$body" | head -c 160 | tr -d '\n')
  echo "REPR1 ($t, probe $i): status=$sc size=$sz content-type=$ct sha256=$sh" >> "$OUT"
  echo "  body head: $head" >> "$OUT"
done
echo "" >> "$OUT"

# Representation 2: Accept: application/json
for i in 1 2; do
  t=$(date -u +%Y-%m-%dT%H%M%SZ)
  b=$(curl -s -H "Accept: application/json" -w "\n%{http_code}\n%{size_download}\n%{content_type}" "$BASE/rest/user/security-question")
  sc=$(echo "$b" | sed -n '2p'); sz=$(echo "$b" | sed -n '3p'); ct=$(echo "$b" | sed -n '4p')
  body=$(echo "$b" | sed -n '1p')
  sh=$(printf '%s' "$body" | sha256sum | cut -d' ' -f1)
  head=$(printf '%s' "$body" | head -c 160 | tr -d '\n')
  echo "REPR2 ($t, probe $i): status=$sc size=$sz content-type=$ct sha256=$sh" >> "$OUT"
  echo "  body head: $head" >> "$OUT"
done
echo "" >> "$OUT"

# Representation 3: GET /redirect?continue=http://example.com
for i in 1 2; do
  t=$(date -u +%Y-%m-%dT%H%M%SZ)
  b=$(curl -s -w "\n%{http_code}\n%{size_download}\n%{content_type}" "$BASE/redirect?continue=http://example.com")
  sc=$(echo "$b" | sed -n '2p'); sz=$(echo "$b" | sed -n '3p'); ct=$(echo "$b" | sed -n '4p')
  body=$(echo "$b" | sed -n '1p')
  sh=$(printf '%s' "$body" | sha256sum | cut -d' ' -f1)
  head=$(printf '%s' "$body" | head -c 160 | tr -d '\n')
  echo "REPR3 ($t, probe $i): status=$sc size=$sz content-type=$ct sha256=$sh" >> "$OUT"
  echo "  body head: $head" >> "$OUT"
done
echo "" >> "$OUT"

# Null control: graceful-wrapped 500 (proves the trigger route is not following the app's normal wrapper)
for i in 1 2; do
  t=$(date -u +%Y-%m-%dT%H%M%SZ)
  b=$(curl -s -w "\n%{http_code}\n%{size_download}\n%{content_type}" "$BASE/api/Nonexistent/1")
  sc=$(echo "$b" | sed -n '2p'); sz=$(echo "$b" | sed -n '3p'); ct=$(echo "$b" | sed -n '4p')
  body=$(echo "$b" | sed -n '1p')
  sh=$(printf '%s' "$body" | sha256sum | cut -d' ' -f1)
  head=$(printf '%s' "$body" | head -c 160 | tr -d '\n')
  echo "CONTROL ($t, probe $i): status=$sc size=$sz content-type=$ct sha256=$sh" >> "$OUT"
  echo "  body head: $head" >> "$OUT"
done
echo "" >> "$OUT"

echo "DONE: $OUT"
