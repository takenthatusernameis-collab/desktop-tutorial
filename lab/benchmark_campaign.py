#!/usr/bin/env python3
"""Controller-side persistence for the blind benchmark campaign.

This module never runs inside the Kilo worker. It uses GitHub Actions artifacts
as controller-only durable state so an unsolved hidden benchmark can survive
multiple workflow activations without becoming visible to the worker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


ARTIFACT_NAME = "desktop-tutorial-active-benchmark"
API_VERSION = "2026-03-10"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def artifact_request(url: str, token: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "desktop-tutorial-benchmark-controller",
        },
    )


def write_env(values: dict[str, str]) -> None:
    env_path = os.environ.get("GITHUB_ENV")
    if not env_path:
        return
    with open(env_path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def validate_pair(secret_dir: Path) -> dict[str, Any]:
    spec_path = secret_dir / "spec.json"
    public_path = secret_dir / "public.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    commitment = sha256_text(canonical_json(spec))
    if commitment != public.get("commitment"):
        raise RuntimeError("Persistent benchmark commitment mismatch.")
    if spec.get("benchmark_id") != public.get("benchmark_id"):
        raise RuntimeError("Persistent benchmark ID mismatch.")
    if spec.get("difficulty") != public.get("difficulty"):
        raise RuntimeError("Persistent benchmark difficulty mismatch.")
    return public


def latest_artifact(repo: str, token: str) -> dict[str, Any] | None:
    url = (
        f"https://api.github.com/repos/{repo}/actions/artifacts"
        f"?per_page=100&name={ARTIFACT_NAME}"
    )
    with urllib.request.urlopen(artifact_request(url, token), timeout=20) as response:
        payload = json.load(response)
    candidates = [
        item for item in payload.get("artifacts", [])
        if isinstance(item, dict) and not item.get("expired")
    ]
    candidates.sort(key=lambda item: item.get("created_at", ""))
    return candidates[-1] if candidates else None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Expose GitHub's signed artifact redirect without forwarding auth headers."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def restore_archive(artifact: dict[str, Any], token: str, destination: Path) -> None:
    archive_url = artifact.get("archive_download_url")
    if not archive_url:
        raise RuntimeError("Persistent benchmark artifact has no download URL.")

    archive_path = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "previous-benchmark.zip"
    opener = urllib.request.build_opener(_NoRedirect())

    try:
        opener.open(artifact_request(archive_url, token), timeout=30)
    except urllib.error.HTTPError as error:
        if error.code not in {301, 302, 303, 307, 308}:
            raise
        location = error.headers.get("Location")
        if not location:
            raise RuntimeError(
                f"Persistent benchmark artifact redirect returned HTTP {error.code} without a Location header."
            ) from error
        # The Location is a signed storage URL; deliberately do not send the
        # GitHub API bearer token to that external host.
        with urllib.request.urlopen(location, timeout=30) as response:
            archive_path.write_bytes(response.read())
    else:
        raise RuntimeError("Persistent benchmark artifact endpoint did not redirect to a signed download URL.")

    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)


def restore_campaign(secret_dir: Path, active_dir: Path, history: Path) -> str:
    secret_dir.mkdir(parents=True, exist_ok=True)
    active_dir.mkdir(parents=True, exist_ok=True)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    mode = "fresh"
    previous_artifact_id = ""

    if repo and token:
        artifact = latest_artifact(repo, token)
        if artifact is not None:
            previous_artifact_id = str(artifact.get("id", ""))
            restore_archive(artifact, token, active_dir)
            state_path = active_dir / "state.json"
            public_path = active_dir / "public.json"
            spec_path = active_dir / "spec.json"
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
            status = state.get("status")
            if status == "solved":
                mode = "fresh"
            elif status == "active":
                if not public_path.is_file() or not spec_path.is_file():
                    raise RuntimeError("Active benchmark artifact is missing required hidden state.")
                shutil.copy2(public_path, secret_dir / "public.json")
                shutil.copy2(spec_path, secret_dir / "spec.json")
                validate_pair(secret_dir)
                mode = "resumed"
                print(f"Resuming active benchmark campaign: {state.get('benchmark_id', 'unknown')}")
            else:
                raise RuntimeError(f"Unknown persistent benchmark state: {status!r}")
        else:
            print("No prior persistent benchmark artifact exists; creating the first campaign.")

    if mode == "fresh":
        subprocess.run(
            [
                "python3",
                "lab/generate_benchmark.py",
                "--secret-dir",
                str(secret_dir),
                "--history",
                str(history),
            ],
            check=True,
        )
        validate_pair(secret_dir)
        print("Started a new benchmark campaign.")

    public = json.loads((secret_dir / "public.json").read_text(encoding="utf-8"))
    write_env(
        {
            "BENCHMARK_CAMPAIGN_MODE": mode,
            "PREVIOUS_BENCHMARK_ARTIFACT_ID": previous_artifact_id,
            "BENCHMARK_ID": str(public["benchmark_id"]),
            "BENCHMARK_COMMITMENT": str(public["commitment"]),
            "BENCHMARK_DIFFICULTY": str(public["difficulty"]),
            "SECURITY_RESEARCH_TARGET": "http://lab-mutator:3000",
            "LAB_SECRET_DIR": str(secret_dir),
            "EHB_WORKER_DIR": str(Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ehb-worker"),
        }
    )
    return mode


def challenge_is_solved(result: dict[str, Any]) -> bool:
    challenge_count = int(result.get("challenge_count") or 0)
    return bool(
        challenge_count > 0
        and int(result.get("unique_challenges_validated") or 0) >= challenge_count
        and int(result.get("finding_count_submitted") or 0) >= challenge_count
        and float(result.get("reproduction_rate") or 0.0) >= 1.0
        and float(result.get("precision_component") or 0.0) >= 1.0
        and float(result.get("evidence_quality") or 0.0) >= 0.8
        and bool(result.get("challenge_solved"))
    )


def prepare_state(
    secret_dir: Path,
    output_dir: Path,
    result_path: Path,
    evaluate_outcome: str,
    persist_outcome: str,
    run_id: str,
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    public = json.loads((secret_dir / "public.json").read_text(encoding="utf-8"))

    solved = False
    if evaluate_outcome == "success" and persist_outcome == "success" and result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        solved = challenge_is_solved(result)

    status = "solved" if solved else "active"
    shutil.copy2(secret_dir / "public.json", output_dir / "public.json")
    if status == "active":
        shutil.copy2(secret_dir / "spec.json", output_dir / "spec.json")

    state = {
        "schema_version": 1,
        "status": status,
        "benchmark_id": public["benchmark_id"],
        "commitment": public["commitment"],
        "difficulty": public["difficulty"],
        "challenge_count": public["challenge_count"],
        "controller_run_id": run_id,
        "solved_this_activation": solved,
    }
    (output_dir / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(state, sort_keys=True))
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    restore = sub.add_parser("restore")
    restore.add_argument("--secret-dir", required=True)
    restore.add_argument("--active-dir", required=True)
    restore.add_argument("--history", default="lab/benchmark_history.jsonl")

    state = sub.add_parser("prepare-state")
    state.add_argument("--secret-dir", required=True)
    state.add_argument("--output-dir", required=True)
    state.add_argument("--result", required=True)
    state.add_argument("--evaluate-outcome", required=True)
    state.add_argument("--persist-outcome", required=True)
    state.add_argument("--run-id", required=True)

    args = parser.parse_args()

    if args.command == "restore":
        restore_campaign(Path(args.secret_dir), Path(args.active_dir), Path(args.history))
        return 0

    prepare_state(
        Path(args.secret_dir),
        Path(args.output_dir),
        Path(args.result),
        args.evaluate_outcome,
        args.persist_outcome,
        args.run_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
