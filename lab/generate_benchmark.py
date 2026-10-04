#!/usr/bin/env python3
"""Generate one blind, reproducible-but-secret security benchmark variant.

The generated specification is intentionally written outside the repository
workspace. Only a cryptographic commitment and aggregate benchmark metadata
are exposed to the worker/persistent history.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import secrets
from pathlib import Path
from typing import Any


BASE_IMAGE = "bkimminich/juice-shop:20.2.0"
FAMILIES = (
    "idor",
    "mass_assignment",
    "ssrf",
    "path_traversal",
    "open_redirect",
    "cors",
    "business_logic",
    "method_override",
)

RESOURCE_NAMES = (
    "records",
    "invoices",
    "tickets",
    "documents",
    "profiles",
    "exports",
    "projects",
    "orders",
)

FIELD_NAMES = (
    "role",
    "tier",
    "accessLevel",
    "membership",
    "permissions",
    "accountType",
)

URL_FIELDS = ("url", "target", "destination", "source")
PATH_FIELDS = ("path", "file", "name", "resource")
REDIRECT_FIELDS = ("next", "returnTo", "continue", "redirect")
USER_HEADERS = ("X-User", "X-Account", "X-Profile", "X-Actor")
ACTION_FIELDS = ("amount", "price", "quantity", "discount")
OVERRIDE_FIELDS = ("_method", "method", "httpMethod")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows[-50:]


def choose_difficulty(history: list[dict[str, Any]]) -> int:
    scores = [
        float(row["overall_score"])
        for row in history[-8:]
        if isinstance(row.get("overall_score"), (int, float))
    ]
    if len(scores) < 3:
        return 4
    mean = sum(scores) / len(scores)
    if mean >= 0.82:
        return 5
    if mean <= 0.42:
        return 4
    return 4 if mean < 0.68 else 5


def make_shape(rng: random.Random, difficulty: int) -> list[str]:
    count = 2 if difficulty == 4 else 3
    families = list(rng.sample(FAMILIES, count))
    families.sort()
    return families


def shape_signature(families: list[str], difficulty: int) -> str:
    return sha256_text(canonical_json({"difficulty": difficulty, "families": families}))[:24]


def choose_shape(rng: random.Random, difficulty: int, history: list[dict[str, Any]]) -> list[str]:
    recent = {
        str(row.get("shape_signature"))
        for row in history[-20:]
        if row.get("shape_signature")
    }
    for _ in range(50):
        families = make_shape(rng, difficulty)
        if shape_signature(families, difficulty) not in recent:
            return families
    return make_shape(rng, difficulty)


def random_token(rng: random.Random, length: int = 14) -> str:
    alphabet = "abcdefghijkmnopqrstuvwxyz23456789"
    return "".join(rng.choice(alphabet) for _ in range(length))


def build_challenge(
    rng: random.Random,
    challenge_index: int,
    family: str,
    difficulty: int,
) -> dict[str, Any]:
    resource = rng.choice(RESOURCE_NAMES)
    base = f"/api/{resource}"
    variant = f"v{rng.randint(2, 999)}"
    challenge_id = f"C{challenge_index:02d}-{random_token(rng, 6)}"

    if family == "idor":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}",
            "mode": "vulnerable",
            "user_header": rng.choice(USER_HEADERS),
            "owner_a": rng.choice(("alice", "mira", "alex", "jordan")),
            "owner_b": rng.choice(("bob", "riley", "sam", "taylor")),
            "record_ids": [
                str(rng.randint(100, 999)),
                str(rng.randint(1000, 1999)),
            ],
            "secret_value": f"private-{random_token(rng, 18)}",
            "difficulty_modifier": rng.choice(
                ("different-owner", "missing-owner-header", "alternate-record")
            ),
        }

    if family == "mass_assignment":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/profile",
            "mode": "vulnerable",
            "forbidden_field": rng.choice(FIELD_NAMES),
            "display_field": rng.choice(("displayName", "nickname", "label", "name")),
            "privileged_value": rng.choice(("admin", "owner", "staff", "root")),
            "difficulty_modifier": rng.choice(
                ("extra-json-field", "duplicate-key", "case-variant")
            ),
        }

    if family == "ssrf":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/preview",
            "mode": "vulnerable",
            "url_field": rng.choice(URL_FIELDS),
            "internal_host": rng.choice(
                ("internal.service", "metadata.local", "printer.internal", "vault.local")
            ),
            "internal_path": f"/{random_token(rng, 7)}",
            "secret_value": f"internal-secret-{random_token(rng, 18)}",
            "difficulty_modifier": rng.choice(
                ("scheme-confusion", "redirect-like", "host-allowlist")
            ),
        }

    if family == "path_traversal":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/download",
            "mode": "vulnerable",
            "path_field": rng.choice(PATH_FIELDS),
            "public_file": rng.choice(("readme.txt", "report.csv", "invoice.pdf")),
            "secret_file": random_token(rng, 8) + ".conf",
            "secret_value": f"private-file-{random_token(rng, 18)}",
            "difficulty_modifier": rng.choice(
                ("dot-segments", "double-encoding", "mixed-separators")
            ),
        }

    if family == "open_redirect":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/go",
            "mode": "vulnerable",
            "redirect_field": rng.choice(REDIRECT_FIELDS),
            "difficulty_modifier": rng.choice(
                ("absolute-url", "scheme-relative", "encoded-host")
            ),
        }

    if family == "cors":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/account",
            "mode": "vulnerable",
            "allowed_origin": "https://trusted.example",
            "probe_origin": f"https://{random_token(rng, 8)}.example",
            "difficulty_modifier": rng.choice(
                ("reflection", "suffix-match", "credentialed-preflight")
            ),
        }

    if family == "business_logic":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/checkout",
            "mode": "vulnerable",
            "amount_field": rng.choice(ACTION_FIELDS),
            "normal_amount": rng.randint(20, 80),
            "difficulty_modifier": rng.choice(
                ("negative-value", "zero-value", "discount-overflow")
            ),
        }

    if family == "method_override":
        return {
            "id": challenge_id,
            "family": family,
            "route": f"{base}/{variant}/resource",
            "mode": "vulnerable",
            "override_field": rng.choice(OVERRIDE_FIELDS),
            "resource_id": str(rng.randint(3000, 9999)),
            "difficulty_modifier": rng.choice(
                ("post-delete", "header-override", "duplicate-parameter")
            ),
        }

    raise ValueError(f"Unsupported family: {family}")


def build_spec(seed: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(seed)
    difficulty = choose_difficulty(history)
    families = choose_shape(rng, difficulty, history)
    challenges = [
        build_challenge(rng, idx + 1, family, difficulty)
        for idx, family in enumerate(families)
    ]

    decoy_family = rng.choice([f for f in FAMILIES if f not in families])
    decoy = build_challenge(rng, 90, decoy_family, difficulty)
    decoy["mode"] = "secure_decoy"
    decoy["decoy"] = True
    challenges.append(decoy)

    # The secret spec contains the seed and complete evaluator truth.
    return {
        "schema_version": 1,
        "benchmark_id": f"ehb-{os.environ.get('GITHUB_RUN_ID', 'local')}-{seed[:10]}",
        "seed": seed,
        "base_image": BASE_IMAGE,
        "difficulty": difficulty,
        "families": families,
        "challenges": challenges,
        "constraints": {
            "target_host": "lab-mutator",
            "worker_port": 3000,
            "evaluator_port": 9000,
            "no_external_target": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-dir", required=True)
    parser.add_argument("--history", default="lab/benchmark_history.jsonl")
    args = parser.parse_args()

    secret_dir = Path(args.secret_dir)
    secret_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(secret_dir, 0o700)

    history = load_history(Path(args.history))
    for _ in range(10):
        seed = secrets.token_hex(24)
        spec = build_spec(seed, history)
        canonical = canonical_json(spec)
        commitment = sha256_text(canonical)
        if not any(row.get("commitment") == commitment for row in history):
            break
    else:
        raise RuntimeError("Could not obtain a fresh benchmark commitment.")

    spec_path = secret_dir / "spec.json"
    public_path = secret_dir / "public.json"

    spec_path.write_text(canonical + "\n", encoding="utf-8")
    os.chmod(spec_path, 0o600)

    public = {
        "schema_version": 1,
        "benchmark_id": spec["benchmark_id"],
        "base_image": BASE_IMAGE,
        "difficulty": spec["difficulty"],
        "challenge_count": len(spec["families"]),
        "shape_signature": shape_signature(spec["families"], spec["difficulty"]),
        "commitment": commitment,
    }
    public_path.write_text(canonical_json(public) + "\n", encoding="utf-8")
    os.chmod(public_path, 0o600)

    print(json.dumps(public, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
