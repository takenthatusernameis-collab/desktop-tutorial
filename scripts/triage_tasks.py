#!/usr/bin/env python3
"""Triage candidate research tasks against the enterprise prioritization rubric
and the false-positive checklist.

This is the executable form of research_state.md Section 10 (prioritization
rubric) and Section 11 (decision-quality checklist). It converts the documented
capability into something that can be run, audited, and reused across
activations — directly addressing F3 (task-selection capability is the current
bottleneck) and F5 (the decision-quality checklist existed only as documentation).
The false-positive checklist is now evaluated automatically per candidate and can
override an otherwise acceptable rubric decision to "defer".

Usage:
    # Triage candidate tasks recorded in research_state.md frontmatter:
    python3 scripts/triage_tasks.py

    # Triage a single stand-alone intake record (used for isolated tests):
    python3 scripts/triage_tasks.py --standalone sample-candidates/illustrative-example.md

Exit codes:
    0  triage completed, no validation errors
    1  validation errors found
    2  missing dependency (pyyaml)

Hard constraints enforced (never scored away):
    - Authorization gate: a candidate is rejected (not scored) unless
      auth_verified_by is populated.
    - Out-of-scope or unverified targets are never scored.
    - A candidate with an incomplete decision-quality checklist (< {CHECKLIST_THRESHOLD}
      of {len(CHECKLIST_ITEMS)} items) is deferred regardless of rubric score.
    - Only candidates with intake_status "awaiting_triage" are scored; others
      are reported in summary form.
"""

import datetime
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml not available; install with 'pip install pyyaml'")
    sys.exit(2)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
STATE_PATH = ROOT_DIR / "research_state.md"
REPORTS_DIR = ROOT_DIR / "reports"

# ---------------------------------------------------------------------------
# Prioritization rubric (mirrors research_state.md Section 10). Keep in sync.
# ---------------------------------------------------------------------------

SCOPE_SIZE_SCORES = {"small": 1, "medium": 2, "large": 3}
SPECIFICITY_SCORES = {"vague": 1, "moderate": 2, "specific": 3}
NOVELTY_SCORES = {"common": 1, "documented pattern": 2, "potentially novel": 3}
EVIDENCE_SCORES = {"none": 1, "partial": 2, "substantial": 3}

MAX_RUBRIC_SCORE = 12  # 4 criteria x 3 points
ACCEPT_THRESHOLD = 8   # priority_total >= 8 and auth gate clear => research
DEFER_THRESHOLD = 5    # 5 <= total < 8 => defer
AUTH_FIELD = "auth_verified_by"
REQUIRED_FIELDS = ["task_id", "intake_status", "authorized_target", "scope_boundary",
                   "source_reference", "hypothesis"]

# ---------------------------------------------------------------------------
# False-positive checklist (mirrors research_state.md Section 11). Keep in sync.
# ---------------------------------------------------------------------------

CHECKLIST_ITEMS = [
    "The hypothesis is falsifiable and scoped to an authorized target only.",
    "The scope boundary is explicitly stated and any out-of-scope behavior is noted.",
    "Expected behavior under the null hypothesis is recorded (what would refute the hypothesis).",
    "At least one common false-positive class matching the hypothesis is identified and ruled out.",
    "The minimum safe interaction to test the hypothesis is defined; no destructive, disruptive, or stealthy action is included.",
    "Reproduction conditions are specified so the result is independently checkable.",
    "Evidence quality (high / medium / low) is assigned per observation, with source references.",
    "A null result (hypothesis refuted) is acceptable and recorded if that is the outcome — negative results reduce uncertainty and are preserved.",
    "The finding status is chosen from: verified / unverified / rejected / false-positive, never 'confirmed' without the above checks.",
]

# ---------------------------------------------------------------------------
# False-positive checklist evaluator (triage-time decision-quality check)
# ---------------------------------------------------------------------------
# This implements research_state.md Section 11 as an automated content
# evaluator: for each candidate, it checks whether the record contains the
# decision-quality content required for a safe, falsifiable investigation, and
# returns per-item results (done/partial/missing) plus a completeness score.
# A low checklist score overrides an otherwise acceptable rubric decision to
# "defer", because a high-scoring hypothesis that lacks decision-quality
# preparation is a deferral case, not a research case.

# checklist item index -> (required_fields, optional_partial_fields)
# An item is 'done' if any required field is non-empty.
CHECKLIST_EVIDENCE = [
    ({"hypothesis"}, {"authorized_target", "scope_boundary"}),            # 1
    ({"scope_boundary"}, set()),                                          # 2
    ({"success_criteria"}, set()),                                        # 3
    ({"rejected_false_positives"}, set()),                                # 4
    ({"safe_interaction"}, set()),                                        # 5
    ({"reproduction_conditions"}, set()),                                 # 6
    ({"evidence_quality"}, set()),                                        # 7
    ({"accept_null_result"}, set()),                                      # 8
    ({"triage_decision"}, set()),                                         # 9
]

CHECKLIST_THRESHOLD = DEFER_THRESHOLD  # minimum completed items (of 9) before research is permitted


def evaluate_checklist(task: dict) -> dict:
    """Evaluate a candidate record against the Section 11 checklist.

    Returns {"items": [...], "score": float, "n": int} where each item has
    {"item": int, "text": str, "status": "done"/"partial"/"missing", "reason": str}.
    score is the number of completed items (done=1, partial=0.5, missing=0).
    """
    flat = {k: str(v or "").strip().lower() for k, v in task.items()}
    results: list[dict] = []
    total = 0.0
    for idx, (required, partials) in enumerate(CHECKLIST_EVIDENCE):
        text = CHECKLIST_ITEMS[idx]
        present = [f for f in required if flat.get(f)]
        if present:
            status, reason, score = "done", f"present: {', '.join(present)}", 1.0
        else:
            pv = " ".join(flat.get(f, "") for f in partials)
            if "false positive" in pv or "false-positive" in pv:
                status, reason, score = (
                    "partial",
                    "related content present but no explicit ruling-out field",
                    0.5,
                )
            elif "null" in pv or "refut" in pv or "expected" in pv:
                status, reason, score = (
                    "partial",
                    "related content present but no explicit decision-quality field",
                    0.5,
                )
            else:
                status, reason, score = (
                    "missing",
                    f"field(s) required: {', '.join(required)}",
                    0.0,
                )
        total += score
        results.append({"item": idx + 1, "text": text, "status": status, "reason": reason})
    return {"items": results, "score": total, "n": len(CHECKLIST_ITEMS)}


def finalize_decision(rubric_decision: str, checklist: dict) -> tuple[str, str | None]:
    """Return the final triage decision after considering checklist completeness.

    A checklist score below CHECKLIST_THRESHOLD overrides the rubric decision
    to "defer" only when the rubric decision was "research"; a research-worthy
    hypothesis with incomplete decision-quality prep is a deferral case, not
    a reject case. Otherwise returns the rubric decision unchanged.
    """
    if checklist["score"] < CHECKLIST_THRESHOLD and rubric_decision == "research":
        return (
            "defer",
            (
                f"Rubric decision '{rubric_decision}' overridden: decision-quality "
                f"checklist only {checklist['score']:.1f}/{checklist['n']} items "
                f"complete (< {CHECKLIST_THRESHOLD} required for research)."
            ),
        )
    return rubric_decision, None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_rubric(task: dict) -> dict | None:
    """Score a candidate against the prioritization rubric.

    Returns a dict of criterion-name -> score, or None if a criterion value is
    unrecognised (in which case the candidate is rejected with a note).
    """
    scores: dict[str, int] = {}
    rubric_pairs = [
        ("scope_size", SCOPE_SIZE_SCORES, task.get("scope_size", "")),
        ("hypothesis_specificity", SPECIFICITY_SCORES, task.get("hypothesis_specificity", "")),
        ("novelty", NOVELTY_SCORES, task.get("novelty", "")),
        ("evidence_available", EVIDENCE_SCORES, task.get("evidence_available", "")),
    ]
    for name, mapping, value in rubric_pairs:
        key = str(value).strip().lower()
        if key not in mapping:
            return None
        scores[name] = mapping[key]
    return scores


def decide(total: int, auth_gate: bool) -> tuple[str, str]:
    """Return (triage_decision, decision_reason) given auth gate and total."""
    if not auth_gate:
        return "reject", "Authorization gate failed: auth_verified_by not populated."
    if total >= ACCEPT_THRESHOLD:
        return "research", (
            f"Priority total {total}/{MAX_RUBRIC_SCORE} meets the accept threshold "
            "(>= {accept}); authorization gate clear."
        ).format(accept=ACCEPT_THRESHOLD)
    if total >= DEFER_THRESHOLD:
        return "defer", (
            f"Priority total {total}/{MAX_RUBRIC_SCORE} is below the accept threshold "
            f"(>= {ACCEPT_THRESHOLD}) but above the reject floor ({DEFER_THRESHOLD - 1}); "
            "defer pending further hypothesis refinement or authorization evidence."
        )
    return "reject", (
        f"Priority total {total}/{MAX_RUBRIC_SCORE} is below the defer threshold "
        f"(>= {DEFER_THRESHOLD}); scope is narrow, hypothesis is weak, or evidence is lacking."
    )


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


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


def load_state(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter, _ = extract_frontmatter(text)
    return frontmatter


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------


def triage_task(task: dict) -> dict:
    """Run the full triage on a single candidate task record."""
    result = {
        "task_id": task.get("task_id", "unknown"),
        "intake_status": task.get("intake_status"),
        "auth_gate": {
            "status": "fail",
            "reason": None,
        },
        "rubric_scores": None,
        "priority_total": None,
        "decision": None,
        "reason": None,
        "rubric_decision": None,
        "rubric_reason": None,
        "checklist": [],
        "checklist_score": None,
        "checklist_n": None,
        "errors": [],
    }

    # 1. Required-field validation
    for field in REQUIRED_FIELDS:
        val = task.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            result["errors"].append(f"required field missing: {field}")

    # 2. Authorization gate (hard constraint — not scored away)
    auth_val = task.get(AUTH_FIELD) or ""
    if not str(auth_val).strip():
        result["auth_gate"] = {
            "status": "fail",
            "reason": f"Authorization gate failed: {AUTH_FIELD} not populated.",
        }
        result["decision"], result["reason"] = decide(0, False)
        return result

    # 3. Rubric scoring
    scores = score_rubric(task)
    if scores is None:
        result["decision"], result["reason"] = (
            "reject",
            "Unrecognised rubric criterion value; candidate rejected pending intake correction.",
        )
        return result
    result["rubric_scores"] = scores
    result["priority_total"] = sum(scores.values())

    # 4. Decision, adjusted by decision-quality checklist
    rubric_decision, rubric_reason = decide(result["priority_total"], True)
    checklist = evaluate_checklist(task)
    decision, reason = finalize_decision(rubric_decision, checklist)
    result["decision"] = decision
    result["reason"] = reason
    result["rubric_decision"] = rubric_decision
    result["rubric_reason"] = rubric_reason
    result["checklist"] = checklist["items"]
    result["checklist_score"] = checklist["score"]
    result["checklist_n"] = checklist["n"]
    result["checklist_threshold"] = CHECKLIST_THRESHOLD

    return result


def run_triage(tasks: list[dict], source_path: Path) -> dict:
    """Triage all candidate tasks and return the report data."""
    statuses = {"not_verified": [], "awaiting_triage": [], "triaged": [],
                "decided": [], "researching": [], "other": [], "errors": []}
    auth_gate_failures = []
    triaged = []

    for task in tasks:
        task_id = task.get("task_id", "<missing id>")
        status = task.get("intake_status", "not_verified")
        if status not in statuses:
            statuses["other"].append(task_id)
        elif status in ("not_verified", "awaiting_triage", "triaged", "decided", "researching"):
            statuses[status].append(task_id)

    # First pass: scan ALL candidates for auth-gate failures (auth is a hard gate,
    # not a scored criterion, so report it regardless of intake_status).
    for task in tasks:
        task_id = task.get("task_id", "<missing id>")
        if triage_task(task)["priority_total"] is None:
            auth_gate_failures.append(task_id)

    # Second pass: score only awaiting_triage candidates.
    for task in tasks:
        if task.get("intake_status") != "awaiting_triage":
            continue
        result = triage_task(task)
        if result["errors"]:
            statuses["errors"].append(task.get("task_id", "<missing id>"))
        if result["priority_total"] is None:
            continue
        if result["decision"]:
            triaged.append((task, result))

    # Ranking: sort by priority_total desc, then task_id for determinism
    triaged_sorted = sorted(
        triaged, key=lambda pair: (-pair[1]["priority_total"], pair[0].get("task_id", ""))
    )

    decisions = {}
    for _, r in triaged_sorted:
        decisions[r["decision"]] = decisions.get(r["decision"], 0) + 1

    return {
        "source_path": str(source_path),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "auth_gate_failures": auth_gate_failures,
        "pending_statuses": {k: statuses[k] for k in ("triaged", "decided", "researching")},
        "other_statuses": statuses["other"],
        "validation_errors": statuses["errors"],
        "ranking": triaged_sorted,
        "decisions": decisions,
        "checklist_threshold": CHECKLIST_THRESHOLD,
        "checklist_n": len(CHECKLIST_ITEMS),
    }


# ---------------------------------------------------------------------------
# Standalone mode (single intake file as one candidate record)
# ---------------------------------------------------------------------------


def intake_to_candidate(frontmatter: dict) -> dict:
    """Map an intake-template frontmatter into a candidate_tasks record."""
    rubric_fields = ["scope_size", "hypothesis_specificity", "novelty", "evidence_available"]
    candidate = {
        "task_id": str(frontmatter.get("task_id", "INTAKE-UNKNOWN")),
        "intake_status": "awaiting_triage",
        "authorized_target": str(frontmatter.get("authorized_target", "")),
        "scope_boundary": str(frontmatter.get("scope_boundary", "")),
        "auth_verified_by": str(frontmatter.get("auth_verified_by", "")),
        "source_reference": str(frontmatter.get("source_reference", "")),
        "source_system": str(frontmatter.get("source_system", "")),
        "hypothesis": str(frontmatter.get("hypothesis", "")),
        "why_this_target": str(frontmatter.get("why_this_target", "")),
        "success_criteria": str(frontmatter.get("success_criteria", "")),
    }
    for f in rubric_fields:
        candidate[f] = str(frontmatter.get(f, ""))
    return candidate


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def format_rubric_row(task, result) -> str:
    ss = result["rubric_scores"] or {}
    inv = {
        "scope_size": {v: k for k, v in SCOPE_SIZE_SCORES.items()},
        "hypothesis_specificity": {v: k for k, v in SPECIFICITY_SCORES.items()},
        "novelty": {v: k for k, v in NOVELTY_SCORES.items()},
        "evidence_available": {v: k for k, v in EVIDENCE_SCORES.items()},
    }
    vals = []
    for key in ["scope_size", "hypothesis_specificity", "novelty", "evidence_available"]:
        v = ss.get(key)
        vals.append(inv[key].get(v, "?") if isinstance(v, int) else "?")
    return (
        f"| {task.get('task_id', '?')} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | "
        f"{result['priority_total']}/12 | {result['decision']} |"
    )


def build_report(data: dict) -> str:
    lines = []
    lines.append("# Candidate Task Triage Report")
    lines.append("")
    lines.append(f"- **Report generated:** {data['generated_at']}")
    lines.append(f"- **Tool:** scripts/triage_tasks.py v0.2.0 (dependency-light; mirrors research_state.md Sections 10-11)")
    lines.append(f"- **Source document:** {data['source_path']}")
    lines.append(f"- **Scoring thresholds:** research >= {ACCEPT_THRESHOLD}, defer {DEFER_THRESHOLD}-{ACCEPT_THRESHOLD - 1}, reject < {DEFER_THRESHOLD} (priority total out of {MAX_RUBRIC_SCORE})")
    lines.append("")
    lines.append("## 1. Authorization gate")
    lines.append("")
    if data["auth_gate_failures"]:
        lines.append(f"The following candidates failed the authorization gate and were rejected without scoring:")
        lines.append("")
        for tid in data["auth_gate_failures"]:
            lines.append(f"- {tid}")
        lines.append("")
    else:
        lines.append("All recorded candidates have `auth_verified_by` populated.")
        lines.append("")
    lines.append("## 2. Ranking (awaiting_triage candidates)")
    lines.append("")
    lines.append("| task_id | scope | specificity | novelty | evidence | total | decision |")
    lines.append("|---|---|---|---|---|---|---|")
    for task, result in data["ranking"]:
        lines.append(format_rubric_row(task, result))
    lines.append("")
    lines.append("## 3. Decision summary")
    lines.append("")
    total = sum(data["decisions"].values())
    lines.append(f"- Total candidates triaged: {total}")
    lines.append(f"- research: {data['decisions'].get('research', 0)}")
    lines.append(f"- defer: {data['decisions'].get('defer', 0)}")
    lines.append(f"- reject: {data['decisions'].get('reject', 0)}")
    if data["auth_gate_failures"]:
        lines.append(f"- auth-gated (not verified): {len(data['auth_gate_failures'])}")
    lines.append("")
    lines.append("## 4. Lifecycle status summary")
    lines.append("")
    lines.append(f"- awaiting_triage: {len(data['auth_gate_failures']) + total}")
    lines.append(f"- triaged: {len(data['pending_statuses'].get('triaged', []))}")
    lines.append(f"- decided: {len(data['pending_statuses'].get('decided', []))}")
    lines.append(f"- researching: {len(data['pending_statuses'].get('researching', []))}")
    if data["other_statuses"]:
        lines.append(f"- other statuses: {data['other_statuses']}")
    if data["validation_errors"]:
        lines.append(f"- validation errors: {data['validation_errors']}")
    lines.append("")
    lines.append("## 5. Detailed triage results")
    lines.append("")
    if not data["ranking"]:
        lines.append("No candidates with intake_status `awaiting_triage` were found in the source.")
        lines.append("")
    for task, result in data["ranking"]:
        lines.append(f"### {task.get('task_id', '?')}")
        lines.append("")
        lines.append(f"- **Status:** {result['intake_status']}")
        lines.append(f"- **Authorized target:** {task.get('authorized_target', '')}")
        lines.append(f"- **Scope boundary:** {task.get('scope_boundary', '')}")
        lines.append(f"- **Hypothesis:** {task.get('hypothesis', '')}")
        lines.append(f"- **Priority total:** {result['priority_total']}/12")
        lines.append(f"- **Triage decision:** {result['decision']}")
        lines.append(f"- **Decision reason:** {result['reason']}")
        lines.append("")
        lines.append("**Rubric detail:**")
        ss = result["rubric_scores"] or {}
        rubric_map = {
            "scope_size": ("Scope size / surface area", SCOPE_SIZE_SCORES),
            "hypothesis_specificity": ("Hypothesis specificity", SPECIFICITY_SCORES),
            "novelty": ("Novelty", NOVELTY_SCORES),
            "evidence_available": ("Evidence available", EVIDENCE_SCORES),
        }
        for key, (label, mapping) in rubric_map.items():
            val = ss.get(key)
            label_text = ", ".join(k for k, v in mapping.items() if v == val)
            lines.append(f"- {label}: {label_text} ({val} pts)")
        lines.append("**False-positive checklist results (Section 11, triage-time content evaluation):**")
        lines.append("")
        lines.append(f"- Score: {result['checklist_score']:.1f}/{result['checklist_n']} items complete "
                      f"(threshold for research >= {result['checklist_threshold']})")
        lines.append("")
        lines.append("| item | status |")
        lines.append("|---|---|")
        for item in result["checklist"]:
            lines.append(f"| {item['item']} | {item['status']} |")
        lines.append("")
        done_items = [i["item"] for i in result["checklist"] if i["status"] == "done"]
        missing_items = [i["item"] for i in result["checklist"] if i["status"] == "missing"]
        partial_items = [i["item"] for i in result["checklist"] if i["status"] == "partial"]
        lines.append(f"- Completed: {', '.join(str(i) for i in done_items)} | "
                     f"partial: {', '.join(str(i) for i in partial_items)} | "
                     f"missing: {', '.join(str(i) for i in missing_items)}.")
        if result.get("rubric_decision") and result["rubric_decision"] != result["decision"]:
            lines.append(
                f"**Decision override:** rubric decision was '{result['rubric_decision']}' "
                f"but the decision-quality checklist is incomplete; final decision is "
                f"'{result['decision']}'."
            )
            lines.append("")
    lines.append("## 6. Method notes")
    lines.append("")
    lines.append("- The rubric criteria and their point scales mirror research_state.md Section 10.")
    lines.append("- The checklist mirrors research_state.md Section 11 (decision-quality checklist) and is now "
                  "evaluated automatically; completeness can override an otherwise acceptable rubric decision to 'defer'.")
    lines.append("- Authorization clarity is a hard gate, not a scoreable dimension; a candidate that fails it is rejected regardless of rubric score.")
    lines.append("- This tool never scores, accepts, or rejects any unauthorized target: all candidates must pass the authorization gate in D4 before research begins.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser_args = sys.argv[1:]
    standalone = False
    target = None

    if parser_args and parser_args[0] == "--standalone":
        standalone = True
        target = Path(parser_args[1]) if len(parser_args) > 1 else None
    else:
        target = STATE_PATH

    if target and not target.exists():
        print(f"ERROR: source file not found: {target}")
        return 1

    if standalone:
        frontmatter, _ = extract_frontmatter(target.read_text(encoding="utf-8"))
        if frontmatter is None:
            print(f"ERROR: no YAML frontmatter in {target}")
            return 1
        candidate = intake_to_candidate(frontmatter)
        report_data = run_triage([candidate], target)
        # mark where the link would go
        report_data["report_type"] = "standalone"
    else:
        if not STATE_PATH.exists():
            print(f"ERROR: research_state.md not found at {STATE_PATH}")
            return 1
        frontmatter = load_state(STATE_PATH)
        if frontmatter is None:
            print(f"ERROR: {STATE_PATH} has no YAML frontmatter")
            return 1
        tasks = frontmatter.get("candidate_tasks", [])
        if not tasks:
            print("No candidate_tasks section found in research_state.md. "
                  "Add candidate tasks via task-intake-template.md and record them in the "
                  "research_state.md frontmatter under `candidate_tasks: []`.")
            return 1
        report_data = run_triage(tasks, STATE_PATH)
        report_data["report_type"] = "research_state"

    # Build and persist report
    report = build_report(report_data)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"triage_{stamp}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Triage report written: {report_path}")
    print(report)

    errors = report_data.get("validation_errors", [])
    gate_failures = report_data["auth_gate_failures"]
    if errors or gate_failures:
        print("\nNOTE: these candidates were not scored (validation errors and/or auth gate).")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
