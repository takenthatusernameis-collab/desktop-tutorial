#!/usr/bin/env python3
"""Dependency-free deterministic tests for the benchmark generator/mutator."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import generate_benchmark as generator
import mutator


def make_request(ch: dict) -> tuple[str, str, dict, dict]:
    family = ch["family"]
    route = ch["route"]

    if family == "idor":
        return "GET", route + "/" + ch["record_ids"][0], {ch["user_header"]: ch["owner_b"]}, {}

    if family == "mass_assignment":
        return "POST", route, {}, {
            ch["forbidden_field"]: ch["privileged_value"],
            ch["display_field"]: "tester",
        }

    if family == "ssrf":
        url = "http://" + ch["internal_host"] + ch["internal_path"]
        return "POST", route, {}, {ch["url_field"]: url}

    if family == "path_traversal":
        query = urlencode({ch["path_field"]: "../../" + ch["secret_file"]})
        return "GET", route + "?" + query, {}, {}

    if family == "open_redirect":
        query = urlencode({ch["redirect_field"]: "https://attacker.example/callback"})
        return "GET", route + "?" + query, {}, {}

    if family == "cors":
        return "GET", route, {"Origin": ch["probe_origin"]}, {}

    if family == "business_logic":
        return "POST", route, {}, {ch["amount_field"]: -1}

    if family == "method_override":
        return "POST", route, {"X-HTTP-Method-Override": "DELETE"}, {}

    raise AssertionError(f"unsupported family: {family}")


def main() -> int:
    history = []
    seen = set()

    for offset, seed in enumerate(("test-seed-a", "test-seed-b", "test-seed-c", "test-seed-d")):
        spec = generator.build_spec(seed, history)
        commitment = generator.sha256_text(generator.canonical_json(spec))
        assert commitment not in seen
        seen.add(commitment)

        mutator.SPEC = spec
        for ch in spec["challenges"]:
            if ch.get("mode") == "secure_decoy":
                method, path, headers, body = make_request(ch)
                vulnerable = mutator.local_handle(method, path, headers, body, [ch], True)
                secure = mutator.local_handle(method, path, headers, body, [ch], False)
                assert vulnerable == secure, ("decoy changed behavior", ch["id"])
                continue

            method, path, headers, body = make_request(ch)
            vulnerable = mutator.local_handle(method, path, headers, body, [ch], True)
            secure = mutator.local_handle(method, path, headers, body, [ch], False)
            assert vulnerable is not None
            assert secure is not None

            if ch["family"] == "cors":
                assert vulnerable[1].get("Access-Control-Allow-Origin") == ch["probe_origin"]
                assert secure[1].get("Access-Control-Allow-Origin") != ch["probe_origin"]
                assert vulnerable[1].get("Access-Control-Allow-Credentials") == "true"
                assert secure[1].get("Access-Control-Allow-Credentials") == "false"

            assert mutator.semantic_diff(vulnerable, secure), (
                "mutation did not create a behavioral difference",
                ch["family"],
            )

        history.append(
            {
                "commitment": commitment,
                "shape_signature": generator.shape_signature(spec["families"], spec["difficulty"]),
            }
        )

    assert len({row["shape_signature"] for row in history}) >= 2
    print("benchmark harness self-test: PASS")
    print(json.dumps({"variants": len(history), "unique_commitments": len(seen)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
