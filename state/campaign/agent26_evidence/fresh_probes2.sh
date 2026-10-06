#!/bin/bash
BASE="http://lab-mutator:3000"
OUT="agent26_fresh_probes2_$(date -u +%Y-%m-%dT%H%M%SZ).txt"
echo "Fresh id=27 trigger-class reproduction — $OUT" > "$OUT"
echo "Target: $BASE ; session started UTC: $(date -u +%Y-%m-%dT%H%M%SZ)" >> "$OUT"
echo "================================================================" >> "$OUT"

run() {
  local label="$1" shift
  local headers="$1" shift
  for i in 1 2; do
    t=$(date -u +%Y-%m-%dT%H%M%SZ)
    curl -s -o req.body -w "%{http_code}|%{size_download}|%{content_type}\n" $headers "$BASE/$1"
    > /dev/null
    sc=$(head -1 req.status) ; sz=$(sed -n '2p' req.status) ; ct=$(sed -n '3p' req.status)
    sh=$(sha256sum req.body | cut -d' ' -f1)
    head=$(head -c 200 req.body | tr '\n' ' ' | cut -c1-220)
    echo "$label ($t probe $i): $sc $sz B $ct | sha256=$sh | head=[$head]" >> "$OUT"
    rm -f req.body req.status
  done
}
run "REPR1 no-accept" "" "rest/user/security-question"
run "REPR2 accept-json" "-H 'Accept: application/json'" "rest/user/security-question"
run "REPR3 redirect" "" "redirect?continue=http://example.com"
run "CONTROL" "" "api/Nonexistent/1"
echo "DONE: $OUT"
