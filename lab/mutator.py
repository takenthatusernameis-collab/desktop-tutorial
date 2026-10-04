#!/usr/bin/env python3
"""Blind mutation gateway for the disposable Juice Shop benchmark.

Worker-facing port 3000 exposes a normal Juice Shop upstream plus a small
generated overlay. Evaluator-facing port 9000 exposes ground truth only on a
separate Docker network.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlsplit


SPEC: dict[str, Any] = {}
STATE: dict[str, Any] = {"business_used": set(), "method_deleted": set()}
STATE_LOCK = threading.Lock()
UPSTREAM = "juice-shop"
UPSTREAM_PORT = 3000


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")


def response(status: int, body: Any, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    final_headers = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
    if headers:
        final_headers.update(headers)
    return status, final_headers, json_bytes(body)


def request_body(handler: BaseHTTPRequestHandler) -> bytes:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        length = 0
    return handler.rfile.read(max(0, min(length, 1_000_000)))


def parse_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw = request_body(handler)
    if not raw:
        return {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def query_value(path: str, name: str) -> str:
    query = parse_qs(urlsplit(path).query, keep_blank_values=True)
    values = query.get(name)
    return values[-1] if values else ""


def header_value(headers: dict[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def challenge_for_request(method: str, path: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for challenge in SPEC.get("challenges", []):
        route = str(challenge["route"])
        family = challenge["family"]
        if family == "idor":
            if method == "GET" and path.startswith(route + "/"):
                matches.append(challenge)
        elif family == "cors":
            if path == route and method in {"GET", "OPTIONS"}:
                matches.append(challenge)
        elif family in {"mass_assignment", "ssrf", "business_logic", "method_override"}:
            if path == route and method in {"POST", "PUT", "PATCH", "DELETE"}:
                matches.append(challenge)
        elif family in {"path_traversal", "open_redirect"}:
            if path == route and method == "GET":
                matches.append(challenge)
    return matches


def semantic_diff(vuln: tuple[int, dict[str, str], bytes], secure: tuple[int, dict[str, str], bytes]) -> bool:
    return vuln[0] != secure[0] or vuln[1].get("Location") != secure[1].get("Location") or vuln[2] != secure[2]


def apply_idor(ch: dict[str, Any], method: str, path: str, headers: dict[str, str], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    record_id = path.rsplit("/", 1)[-1]
    if record_id not in set(ch["record_ids"]):
        return response(404, {"error": "not-found"})
    actor = header_value(headers, ch["user_header"])
    owner = ch["owner_a"] if record_id == ch["record_ids"][0] else ch["owner_b"]
    foreign = not actor or actor != owner
    if foreign and not mutate:
        return response(403 if actor else 401, {"error": "ownership-check-failed"})
    body = {
        "id": record_id,
        "owner": owner,
        "status": "private",
        "note": ch["secret_value"],
        "access": "owner" if actor == owner else "cross-owner",
    }
    return response(200, body)


def apply_mass_assignment(ch: dict[str, Any], body: dict[str, Any], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    forbidden = ch["forbidden_field"]
    display = ch["display_field"]
    changed = [display] if display in body else []
    privileged = None
    if forbidden in body and mutate:
        privileged = body.get(forbidden)
        changed.append(forbidden)
    elif forbidden in body and not mutate:
        privileged = "unchanged"
    return response(200, {"changed": changed, "privileged_field": forbidden, "privileged_value": privileged})


def apply_ssrf(ch: dict[str, Any], body: dict[str, Any], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    url = str(body.get(ch["url_field"], ""))
    parsed = urlsplit(url)
    internal = parsed.hostname == ch["internal_host"] and parsed.path == ch["internal_path"]
    if internal and mutate:
        return response(200, {"fetched": url, "upstream": "internal", "body": ch["secret_value"]})
    if internal and not mutate:
        return response(403, {"error": "internal-host-blocked"})
    return response(400, {"error": "unsupported-preview-target"})


def apply_path_traversal(ch: dict[str, Any], path: str, mutate: bool) -> tuple[int, dict[str, str], bytes]:
    candidate = query_value(path, ch["path_field"])
    decoded = unquote(unquote(candidate))
    traversal = ".." in decoded or decoded.startswith("/")
    if traversal and mutate:
        return response(200, {"file": decoded, "contents": ch["secret_value"]})
    if traversal and not mutate:
        return response(403, {"error": "path-outside-download-root"})
    if decoded == ch["public_file"]:
        return response(200, {"file": decoded, "contents": "public-training-file"})
    return response(404, {"error": "file-not-found"})


def apply_redirect(ch: dict[str, Any], path: str, mutate: bool) -> tuple[int, dict[str, str], bytes]:
    destination = query_value(path, ch["redirect_field"])
    external = bool(urlsplit(destination).scheme or destination.startswith("//"))
    if external and mutate:
        return response(302, {"redirect": destination}, {"Location": destination})
    if external and not mutate:
        return response(400, {"error": "external-redirect-blocked"})
    if destination.startswith("/"):
        return response(302, {"redirect": destination}, {"Location": destination})
    return response(400, {"error": "invalid-destination"})


def apply_cors(ch: dict[str, Any], method: str, headers: dict[str, str], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    origin = header_value(headers, "Origin")
    if not origin:
        origin = "https://no-origin.example"
    out_headers = {"Vary": "Origin"}
    if mutate:
        out_headers["Access-Control-Allow-Origin"] = origin
        out_headers["Access-Control-Allow-Credentials"] = "true"
    elif origin == ch["allowed_origin"]:
        out_headers["Access-Control-Allow-Origin"] = origin
        out_headers["Access-Control-Allow-Credentials"] = "true"
    else:
        out_headers["Access-Control-Allow-Origin"] = "null"
        out_headers["Access-Control-Allow-Credentials"] = "false"
    if method == "OPTIONS":
        out_headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        out_headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response(204, {}, out_headers)
    return response(200, {"account": "redacted-training-account"}, out_headers)


def apply_business_logic(ch: dict[str, Any], body: dict[str, Any], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    raw = body.get(ch["amount_field"])
    try:
        amount = float(raw)
    except (TypeError, ValueError):
        return response(400, {"error": "invalid-amount"})
    abusive = amount <= 0
    if abusive and not mutate:
        return response(400, {"error": "amount-must-be-positive"})
    charged = max(0.0, amount) if abusive else amount
    return response(200, {"accepted": True, "requested": amount, "charged": charged})


def apply_method_override(ch: dict[str, Any], method: str, path: str, headers: dict[str, str], body: dict[str, Any], mutate: bool) -> tuple[int, dict[str, str], bytes]:
    override = body.get(ch["override_field"], "") or header_value(headers, "X-HTTP-Method-Override")
    if method == "POST" and str(override).upper() == "DELETE":
        resource_id = ch["resource_id"]
        if mutate:
            with STATE_LOCK:
                STATE["method_deleted"].add(resource_id)
            return response(200, {"deleted": resource_id, "method": "DELETE"})
        return response(405, {"error": "method-override-not-permitted"})
    return response(200, {"status": "unchanged"})


def local_handle(
    method: str,
    path: str,
    headers: dict[str, str],
    body: dict[str, Any],
    challenges: list[dict[str, Any]],
    mutate: bool,
) -> tuple[int, dict[str, str], bytes] | None:
    for ch in challenges:
        family = ch["family"]
        if family == "idor":
            return apply_idor(ch, method, path, headers, mutate)
        if family == "mass_assignment":
            return apply_mass_assignment(ch, body, mutate)
        if family == "ssrf":
            return apply_ssrf(ch, body, mutate)
        if family == "path_traversal":
            return apply_path_traversal(ch, path, mutate)
        if family == "open_redirect":
            return apply_redirect(ch, path, mutate)
        if family == "cors":
            return apply_cors(ch, method, headers, mutate)
        if family == "business_logic":
            return apply_business_logic(ch, body, mutate)
        if family == "method_override":
            return apply_method_override(ch, method, path, headers, body, mutate)
    return None


def proxy_to_upstream(handler: BaseHTTPRequestHandler, path: str, body: bytes) -> tuple[int, dict[str, str], bytes]:
    headers: dict[str, str] = {}
    for key, value in handler.headers.items():
        if key.lower() in {"host", "connection", "content-length"}:
            continue
        headers[key] = value
    headers["Host"] = f"{UPSTREAM}:{UPSTREAM_PORT}"
    connection = http.client.HTTPConnection(UPSTREAM, UPSTREAM_PORT, timeout=15)
    try:
        connection.request(handler.command, path, body=body, headers=headers)
        upstream = connection.getresponse()
        payload = upstream.read()
        out_headers: dict[str, str] = {}
        for key, value in upstream.getheaders():
            if key.lower() in {"connection", "keep-alive", "transfer-encoding"}:
                continue
            out_headers[key] = value
        return upstream.status, out_headers, payload
    except Exception as exc:
        return response(502, {"error": "upstream-unavailable", "detail": str(exc)})
    finally:
        connection.close()


class WorkerHandler(BaseHTTPRequestHandler):
    server_version = "EHBMutationGateway/1.0"

    def _serve(self) -> None:
        path = self.path
        body_raw = b""
        if self.command in {"POST", "PUT", "PATCH", "DELETE"}:
            body_raw = request_body(self)
        try:
            body_json = (
                json.loads(body_raw.decode("utf-8"))
                if body_raw else {}
            )
            if not isinstance(body_json, dict):
                body_json = {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            body_json = {}

        headers = {key: value for key, value in self.headers.items()}
        parsed_path = urlsplit(path).path
        if parsed_path == "/__lab__/health":
            status, out_headers, payload = response(200, {"status": "ready"})
        else:
            challenges = challenge_for_request(self.command, parsed_path)
            local = local_handle(
                self.command,
                path,
                headers,
                body_json,
                challenges,
                mutate=True,
            )
            if local is not None:
                status, out_headers, payload = local
            else:
                status, out_headers, payload = proxy_to_upstream(self, path, body_raw)

        self.send_response(status)
        for key, value in out_headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    do_GET = _serve
    do_POST = _serve
    do_PUT = _serve
    do_PATCH = _serve
    do_DELETE = _serve
    do_OPTIONS = _serve

    def log_message(self, format: str, *args: Any) -> None:
        return


class EvaluatorHandler(BaseHTTPRequestHandler):
    server_version = "EHBHiddenEvaluator/1.0"

    def _json_response(self, status: int, payload: Any) -> None:
        raw = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/__lab__/health":
            self._json_response(200, {"status": "evaluator-ready"})
        else:
            self._json_response(404, {"error": "not-found"})

    def do_POST(self) -> None:
        if self.path != "/__evaluator__/verify":
            self._json_response(404, {"error": "not-found"})
            return
        raw = request_body(self)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json_response(400, {"error": "invalid-json"})
            return
        if not isinstance(payload, dict):
            self._json_response(400, {"error": "request-must-be-object"})
            return

        method = str(payload.get("method", "GET")).upper()
        url = str(payload.get("url", ""))
        headers = {
            str(k): str(v)
            for k, v in (payload.get("headers") or {}).items()
        }
        body = payload.get("body") or {}
        if not isinstance(body, dict):
            body = {}

        parsed = urlsplit(url)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        challenges = challenge_for_request(method, parsed.path or "/")
        matches: list[dict[str, Any]] = []

        for ch in challenges:
            vuln = local_handle(method, path, headers, body, [ch], mutate=ch.get("mode") != "secure_decoy")
            secure = local_handle(method, path, headers, body, [ch], mutate=False)
            if vuln is None or secure is None:
                continue
            differs = semantic_diff(vuln, secure)
            if ch.get("mode") == "vulnerable" and differs:
                matches.append(
                    {
                        "challenge_id": ch["id"],
                        "family": ch["family"],
                        "vulnerable_status": vuln[0],
                        "secure_status": secure[0],
                        "behavioral_difference": True,
                    }
                )

        self._json_response(
            200,
            {
                "valid_target": parsed.hostname == "lab-mutator",
                "matches": matches,
                "ground_truth_not_exposed": True,
            },
        )

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--worker-port", type=int, default=3000)
    parser.add_argument("--eval-port", type=int, default=9000)
    parser.add_argument("--upstream-host", default="juice-shop")
    parser.add_argument("--upstream-port", type=int, default=3000)
    args = parser.parse_args()

    global SPEC, UPSTREAM, UPSTREAM_PORT
    SPEC = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    UPSTREAM = args.upstream_host
    UPSTREAM_PORT = args.upstream_port

    worker_server = ThreadingHTTPServer(("0.0.0.0", args.worker_port), WorkerHandler)
    eval_server = ThreadingHTTPServer(("0.0.0.0", args.eval_port), EvaluatorHandler)

    worker_thread = threading.Thread(target=worker_server.serve_forever, daemon=True)
    eval_thread = threading.Thread(target=eval_server.serve_forever, daemon=True)
    worker_thread.start()
    eval_thread.start()
    print(
        json.dumps(
            {
                "benchmark_id": SPEC["benchmark_id"],
                "difficulty": SPEC["difficulty"],
                "worker_port": args.worker_port,
                "evaluator_port": args.eval_port,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    try:
        worker_thread.join()
    finally:
        worker_server.shutdown()
        eval_server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
