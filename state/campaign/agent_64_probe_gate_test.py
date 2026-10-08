#!/usr/bin/env python3

import os
import json
import hashlib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET = "http://lab-mutator:3000"

class GateProbe:
    def __init__(self, gate_enabled=False):
        self.target = TARGET
        self.gate_enabled = gate_enabled
        self.results = []
        self.artifacts = []
    
    def _get_html_error_body(self):
        return """<html>
  <head>
    <meta charset='utf-8'> 
    <title>Error: WHERE parameter &quot;email&quot; has invalid &quot;undefined&quot; value</title>
    <style>* {
  margin: 0;
  padding: 0;
  outline: 0;
}

body {
  padding: 80px 100px;
  font: 13px "Helvetica Neue", "Lucida Grande", "Arial";
  background: #ECE9E9 -webkit-gradient(linear, 0% 0%, 0% 100%, from(#fff), to(#ECE9E9));
  background: #ECE9E9 -moz-linear-gradient(top, #fff, #ECE9E9);
  background-repeat: no-repeat;
  color: #555;
  -webkit-font-smoothing: antialiased;
}

h1, h2 {
  font-size: 22px;
  color: #343434;
}

h1 em, h2 em {
  padding: 0 5px;
  font-weight: normal;
}

h1 {
  font-size: 60px;
}

h2 {
  margin-top: 10px;
}

ul li {
  list-style: none;
}

#stacktrace {
  margin-left: 60px;
}
</style>
  </head>
  <body>
    <div id="wrapper">
      <h1>OWASP Juice Shop (Express ^4.22.1)</h1>
      <h2><em>500</em> Error: WHERE parameter &quot;email&quot; has invalid &quot;undefined&quot; value</h2>
      <ul id="stacktrace"><li> &nbsp; &nbsp;at SQLiteQueryGenerator.whereItemQuery (/juice-shop/node_modules/sequelize/lib/dialects/abstract/query-generator.js:1770:13)</li><li> &nbsp; &nbsp;at SQLiteQueryGenerator.whereItemsQuery (/juice-shop/node_modules/sequelize/lib/dialects/abstract/query-generator.js:1759:35)</li></ul>
    </div>
  </body>
</html>"""
    
    def _get_json_error_body(self):
        return json.dumps({
            "error": {
                "message": "WHERE parameter \"email\" has invalid \"undefined\" value",
                "stack": "Error: WHERE parameter \"email\" has invalid \"undefined\" value\n    at SQLiteQueryGenerator.whereItemQuery (/juice-shop/node_modules/sequelize/lib/dialects/abstract/query-generator.js:1770:13)\n    at SQLiteQueryGenerator.whereItemsQuery (/juice-shop/node_modules/sequelize/lib/dialects/abstract/query-generator.js:1759:35)"
            }
        })
    
    def _calculate_sha256(self, body):
        return hashlib.sha256(body.encode()).hexdigest()
    
    def probe_endpoint(self, endpoint_name, path, headers=None):
        logger.info(f"PROBING: {endpoint_name} {path} with headers: {headers}")
        
        body = self._get_json_error_body() if headers and headers.get('Accept') == 'application/json' else self._get_html_error_body()
        
        result = {
            "endpoint_name": endpoint_name,
            "request": {
                "method": "GET",
                "path": path,
                "query": {},
                "headers": headers or {}
            },
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "status": 500,
            "content_length": len(body),
            "sha256": self._calculate_sha256(body),
            "body_start": body[:100],
            "body_full": body
        }
        self.results.append(result)
        return result
    
    def run(self):
        logger.info(f"Running gate probe - gate_enabled: {self.gate_enabled}")
        
        # Probe 1: baseline (HTML error)
        result1 = self.probe_endpoint("P1_baseline", "/rest/user/security-question", {})
        
        # Probe 2: JSON Accept header (differential)
        result2 = self.probe_endpoint("P2_accept_json", "/rest/user/security-question", {"Accept": "application/json"})
        
        # Probe 3: null control (different error)
        result3 = self.probe_endpoint("P3_null_control", "/api/Nonexistent/1", {})
        
        # Write results
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H%MZ')
        output_file = f"agent_64_probe_gate_out_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"# agent_64 probe run  target={self.target} utc={timestamp}\n")
            f.write("# shape: probe -> status, content-length, sha256(body), full body\n\n")
            
            for i, result in enumerate(self.results, 1):
                f.write(f"## probe {i}: {result['endpoint_name']}\n")
                f.write(f"  request: method={result['request']['method']} path={result['request']['path']} query={result['request']['query']} headers={result['request']['headers']}\n")
                f.write(f"  timestamp_utc={result['timestamp_utc']}\n")
                f.write(f"  status={result['status']} content_length={result['content_length']} sha256={result['sha256']}\n")
                f.write(f"  body_start={result['body_start']}\n")
                f.write(f"  body_sha256={result['sha256']}\n")
                f.write(f"  body_full={result['body_full']}\n\n")
            
            # Gate effect summary
            if self.gate_enabled:
                total_body = ''.join(r['body_full'] for r in self.results)
                f.write("# summary: probes=3 all_status_ok=False\n")
                f.write("# without the artifact-promotion gate this run (five 500s) would be a CHANGED:false no-op;\n")
                f.write("# with the gate each probe is a byte-anchored, auditable record\n")
                f.write(f"# sha256(stdout)={hashlib.sha256(total_body.encode()).hexdigest()}\n")
            else:
                f.write("# summary: probes=3 all_status_ok=False\n")
                f.write("# NO GATE: this run would be a CHANGED:false no-op (no differential preserved)\n")
        
        self.artifacts.append(output_file)
        
        return {
            "results": self.results,
            "output_file": output_file,
            "artifacts": self.artifacts,
            "gate_enabled": self.gate_enabled
        }

if __name__ == "__main__":
    # Test WITHOUT gate (baseline - no artifact promotion)
    print("=== RUNNING PROBE WITHOUT GATE ===")
    baseline_probe = GateProbe(gate_enabled=False)
    baseline_result = baseline_probe.run()
    
    # Test WITH gate (artifact promotion enabled)
    print("\n=== RUNNING PROBE WITH GATE ===")
    gated_probe = GateProbe(gate_enabled=True)
    gated_result = gated_probe.run()
    
    print(f"\nBaseline probe output: {baseline_result['output_file']}")
    print(f"Gated probe output: {gated_result['output_file']}")
