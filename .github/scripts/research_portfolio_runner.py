#!/usr/bin/env python3
"""Launch the trusted research-program controller inside the authorized worker network."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    image = os.environ.get("EHB_KILO_IMAGE")
    if not image:
        raise SystemExit("EHB_KILO_IMAGE is required")
    research_program = root / "lab" / "research_program.py"
    controller = ["python3", str(research_program), "validate",
        "--mode", os.environ["BENCHMARK_CAMPAIGN_MODE"],
        "--benchmark-id", os.environ["BENCHMARK_ID"],
        "--state-dir", str(root / "state" / "research")]
    try:
        subprocess.run(controller, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Persisted research-program validation failed before Docker execution "
            f"(exit {exc.returncode})."
        ) from exc

    cmd = [
        "docker", "run", "--rm",
        "--network", "ehb-worker-net",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--mount", f"type=bind,source={state_dir},target=/workspace/state",
        "--mount", f"type=bind,source={research_program},target=/workspace/research_program.py,readonly",
        "-w", "/workspace", image,
        "python3", "/workspace/research_program.py", "pre-kilo",
        "--mode", os.environ["BENCHMARK_CAMPAIGN_MODE"],
        "--benchmark-id", os.environ["BENCHMARK_ID"],
        "--target", os.environ["SECURITY_RESEARCH_TARGET"],
        "--state-dir", "/workspace/state/research",
    ]
    return subprocess.run(cmd, check=True).returncode


if __name__ == "__main__":
    raise SystemExit(main())
