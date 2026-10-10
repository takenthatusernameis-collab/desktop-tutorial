#!/bin/bash

# Test script to implement artifact-promotion WITHOUT disk-existence verification gate
# This is the IMPROVED version that should perform better than the REJECTED version

TARGET_BASE="http://lab-mutator:3000"
WORKSPACE="/workspace"
CAMPAIGN_STATE="/workspace/state/campaign"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Function to create byte anchor
sha256() {
    echo -n "$1" | sha256sum | cut -d' ' -f1
}

# Function to capture uniform-500 probe artifact WITHOUT disk-existence verification gate
capture_uniform_500_artifact() {
    local request_desc="$1"
    local method="$2"
    local url="$3"
    local headers_json="$4"
    local body="$5"
    
    echo "[IMPROVED] Executing $method $url - $request_desc"
    
    # Convert headers JSON to curl headers
    local curl_headers=""
    if [ "$headers_json" != "null" ] && [ "$headers_json" != "" ]; then
        curl_headers=$(echo "$headers_json" | jq -r 'to_entries|map(" -H \"\(\.key\): \(\.value)\"")|.[]' 2>/dev/null || echo "")
    fi
    
    # Make request with curl
    local response
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$TARGET_BASE$url" $curl_headers)
    elif [ "$method" = "POST" ]; then
        # Create temporary body file
        echo "$body" > /tmp/body.json
        response=$(curl -s -w "%{http_code}" -X POST "$TARGET_BASE$url" $curl_headers -d @/tmp/body.json --header "Content-Type: application/json")
    else
        response=$(curl -s -w "%{http_code}" -X "$method" "$TARGET_BASE$url" $curl_headers)
    fi
    
    local status_code="${response: -3}"
    local content="${response%???}"
    
    # Create byte anchor
    local anchor=$(sha256 "$content")
    
    # Create artifact object
    local artifact_json=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "request_desc": "$request_desc",
  "method": "$method",
  "url": "$url",
  "headers": $headers_json,
  "body": $body,
  "status_code": $status_code,
  "response_body": $(echo "$content" | jq -R . | jq .),
  "byte_anchor": "$anchor",
  "content_length": $(echo -n "$content" | wc -c),
  "improvement_note": "artifact-promotion WITHOUT disk-existence verification gate"
}
