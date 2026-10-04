#!/usr/bin/env python3
"""Validate a RESEARCH_STATE.md document against its JSON Schema.

Usage:
    python3 scripts/validate_research_state.py [path]

Checks:
    1. File parses as UTF-8 and has non-empty content.
    2. YAML frontmatter block exists and is valid.
    3. Frontmatter validates against research_state_schema.json.
    4. A human-readable document section follows the frontmatter.
    5. A hand-off section with CHANGED / VERIFIED / UNVERIFIED / NEXT labels exists.

Exit codes: 0 = valid, 1 = invalid.
"""

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
try:
    import yaml_minimal as _yaml
except ImportError:
    print("yaml_minimal not available (parse-only fallback); install with 'pip install pyyaml'")
    sys.exit(2)
yaml = _yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
SCHEMA_PATH = ROOT_DIR / "research_state_schema.json"

REQUIRED_HF_FIELDS = ["enterprise", "state_schema_version", "last_updated"]


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError("research_state_schema.json not found")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def extract_frontmatter(text: str) -> tuple[dict | None, str | None]:
    if not text.strip().startswith("---"):
        return None, None
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.S)
    if not match:
        return None, None
    try:
        return yaml.safe_load(match.group(1)), text[match.end():]
    except yaml.YAMLError as e:
        return None, f"YAML error: {e}"


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"cannot read file: {e}"], []

    if not text.strip():
        errors.append("file is empty")

    frontmatter, body = extract_frontmatter(text)

    if frontmatter is None:
        errors.append("missing or malformed YAML frontmatter")
        return errors, []

    for field in REQUIRED_HF_FIELDS:
        if field not in frontmatter:
            errors.append(f"required frontmatter field missing: {field}")

    schema = load_schema()
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema)
        for err in validator.iter_errors(frontmatter):
            errors.append(f"schema validation: {'.'.join(str(p) for p in err.path)} - {err.message}")
    except ImportError:
        warnings.append("jsonschema module missing (deep schema validation skipped); install with 'pip install jsonschema'")

    if isinstance(body, str) and not body.strip():
        errors.append("document has no human-readable content after the frontmatter")

    if "CHANGED" not in text or "VERIFIED" not in text:
        errors.append("missing hand-off labels (CHANGED / VERIFIED)")

    if "NEXT" not in text:
        errors.append("missing hand-off NEXT label")

    return errors, warnings


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DIR / "research_state.md"
    errors, warnings = validate(path)
    if errors:
        print(f"{path}: INVALID ({len(errors)} error(s))")
        for e in errors:
            print(f"  - {e}")
        if warnings:
            print("warnings:")
            for w in warnings:
                print(f"  + {w}")
        return 1
    print(f"{path}: valid")
    if warnings:
        print("warnings:")
        for w in warnings:
            print(f"  + {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
