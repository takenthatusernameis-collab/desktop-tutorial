#!/usr/bin/env python3
"""Controller for the controlled ten-session research campaign.

This controller owns task decomposition, task validation, handoff validation,
and compact durable campaign state. It does not execute Kilo and it never
dispatches another workflow/session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

OUTCOME_CLASSES = {
    "NEW_EVIDENCE",
    "NEW_HYPOTHESIS",
    "FALSIFIED",
    "NO_NEW_INFORMATION",
    "INFRASTRUCTURE_FAILURE",
}
DECISIONS = {"IMPROVE", "RETAIN", "REJECT", "UNVERIFIED"}
CAMPAIGN_AGENT_COUNT = 10
GLOBAL_COUNTER_NAME = "GLOBAL_AGENT_COUNTER.json"
CAMPAIGN_MANIFEST_NAME = "CAMPAIGN_MANIFEST.json"

TASK_FIELDS = (
    "task_id",
    "agent_number",
    "role",
    "objective",
    "primary_question",
    "bottleneck",
    "information_gap",
    "bounded_action",
    "deliverable",
    "success_evidence_criterion",
    "stop_condition",
    "out_of_scope",
    "verification_requirement",
)

RESULT_FIELDS = (
    "OUTCOME_CLASS:",
    "TASK_ID:",
    "PRIMARY_QUESTION:",
    "BOTTLENECK:",
    "INFORMATION_GAP:",
    "BOUNDED_ACTION:",
    "DELIVERABLE:",
    "SUCCESS_EVIDENCE_CRITERION:",
    "STOP_CONDITION:",
    "OUT_OF_SCOPE:",
    "VERIFICATION_REQUIREMENT:",
    "CHANGED:",
    "VERIFIED:",
    "UNVERIFIED:",
    "OBSERVED_EFFECT:",
    "UNCERTAINTY_TARGETED:",
    "UNCERTAINTY_REDUCED:",
    "DECISION:",
    "NEXT:",
)


def read_text(path: Path, limit: int = 18000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def parse_result(path: Path) -> dict[str, str]:
    text = read_text(path, limit=20000)
    lines = text.splitlines()
    fields: dict[str, str] = {}
    for idx, line in enumerate(lines):
        for field in RESULT_FIELDS:
            if line.startswith(field):
                value = line.split(":", 1)[1].strip()
                continuation: list[str] = []
                for later in lines[idx + 1 :]:
                    if any(later.startswith(prefix) for prefix in RESULT_FIELDS):
                        break
                    if later.strip():
                        continuation.append(later.strip())
                if continuation:
                    value = " ".join([value, *continuation]).strip()
                fields[field[:-1]] = value
                break
    return fields


def validate_task(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in TASK_FIELDS:
        if field == "agent_number":
            continue
        if field not in task or not isinstance(task[field], str) or not task[field].strip():
            errors.append(f"missing/empty task field: {field}")
    agent_number = int(task.get("agent_number", 0) or 0)
    if agent_number < 1:
        errors.append("agent_number must be >= 1")
    expected_role = "LEARNING_PROCESS" if agent_number % 2 else "HIGHER_ORDER_RESEARCH"
    if task.get("role") != expected_role:
        errors.append(f"role must be {expected_role}")
    if "\n" in str(task.get("primary_question", "")):
        errors.append("primary_question must be one line")
    if "\n" in str(task.get("stop_condition", "")):
        errors.append("stop_condition must be one line")
    if task.get("task_id", "").startswith("task-") is False:
        errors.append("task_id must use task-* namespace")
    return errors


def validate_result(path: Path, expected_task: dict[str, Any]) -> list[str]:
    fields = parse_result(path)
    errors: list[str] = []
    missing = [field[:-1] for field in RESULT_FIELDS if not fields.get(field[:-1], "").strip()]
    errors.extend(f"missing result field: {field}" for field in missing)

    outcome = fields.get("OUTCOME_CLASS", "")
    if outcome not in OUTCOME_CLASSES:
        errors.append(f"invalid OUTCOME_CLASS: {outcome!r}")

    decision = fields.get("DECISION", "")
    if decision not in DECISIONS:
        errors.append(f"invalid DECISION: {decision!r}")

    if fields.get("TASK_ID") != expected_task.get("task_id"):
        errors.append("TASK_ID does not match controller-selected task")

    next_value = fields.get("NEXT", "")
    if "\n" in next_value or next_value.count(";") >= 2:
        errors.append("NEXT must be one bounded action on one line")
    if len(next_value) > 360:
        errors.append("NEXT is too broad/verbose for a single immediate action")

    if outcome == "INFRASTRUCTURE_FAILURE" and not fields.get("UNVERIFIED"):
        errors.append("INFRASTRUCTURE_FAILURE must explain what remains unverified")
    return errors


def recent_memos(campaign_dir: Path) -> list[tuple[int, Path, dict[str, str]]]:
    rows: list[tuple[int, Path, dict[str, str]]] = []
    for path in sorted(campaign_dir.glob("agent_*_RESULT.md")):
        match = re.search(r"agent_(\d+)_RESULT\.md$", path.name)
        if not match:
            continue
        number = int(match.group(1))
        rows.append((number, path, parse_result(path)))
    return rows


def evidence_signals(root: Path) -> list[str]:
    source_paths = [
        root / "LEARNING_STATE.md",
        root / "SOLVER_FEEDBACK.md",
        root / "reports" / "benchmark_research.md",
        root / "research_state.md",
    ]
    corpus = "\n".join(read_text(path, 12000) for path in source_paths).lower()
    signals: list[str] = []
    if any(token in corpus for token in ("repeated", "exhausted", "converged", "no new information", "diminishing")):
        signals.append("selection-concentration")
    if any(token in corpus for token in ("unverified", "mismatch", "zero", "precision", "replay")):
        signals.append("evidence-mismatch")
    if any(token in corpus for token in ("persist", "durable", "missing at activation", "wiped", "handoff")):
        signals.append("persistence")
    if any(token in corpus for token in ("hypothesis", "frontier", "coverage", "untested", "unknown")):
        signals.append("hypothesis-frontier")
    return signals or ["hypothesis-frontier"]


def signal_excerpt(root: Path) -> str:
    candidates: list[str] = []
    for rel in ("LEARNING_STATE.md", "SOLVER_FEEDBACK.md", "reports/benchmark_research.md", "research_state.md"):
        text = read_text(root / rel, 16000)
        for line in text.splitlines():
            clean = line.strip()
            if not clean:
                continue
            lower = clean.lower()
            if any(token in lower for token in (
                "gap:", "strategy delta", "bottleneck", "next:", "unverified",
                "exhausted", "converged", "diminishing", "persistence",
            )):
                candidates.append(clean)
            if len(candidates) >= 6:
                break
        if len(candidates) >= 6:
            break
    if not candidates:
        return "No compact bottleneck signal was available; inspect the full authorized durable research state."
    return " | ".join(candidates[:6])[:1800]


def task_id(agent_number: int, slug: str) -> str:
    digest = hashlib.sha256(f"{agent_number}:{slug}".encode()).hexdigest()[:10]
    return f"task-{agent_number:02d}-{slug}-{digest}"


def build_task(agent_number: int, root: Path, campaign_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    role = "LEARNING_PROCESS" if agent_number % 2 else "HIGHER_ORDER_RESEARCH"
    memos = recent_memos(campaign_dir)
    previous = memos[-1][2] if memos else {}
    signals = evidence_signals(root)
    excerpt = signal_excerpt(root)

    candidates: list[dict[str, Any]] = []

    if agent_number > 1 and previous:
        prev_decision = previous.get("DECISION", "UNVERIFIED")
        prev_effect = previous.get("OBSERVED_EFFECT", "")
        prev_next = previous.get("NEXT", "")
        if agent_number % 2 == 1:
            slug = "evaluate-prior-research-effect"
            candidates.append({
                "task_id": task_id(agent_number, slug),
                "agent_number": agent_number,
                "role": role,
                "objective": "Improve or falsify the learning process using observed evidence from the preceding research session.",
                "primary_question": "Did the preceding focused research task produce the predicted learning effect, or did it only create activity?",
                "bottleneck": "Unverified effect of the preceding process/research choice.",
                "information_gap": f"Whether the preceding decision ({prev_decision}) materially changed useful uncertainty; prior observed effect: {prev_effect[:420]}",
                "bounded_action": "Inspect the preceding result, its evidence, and the durable state it changed; perform one bounded comparison or audit that can distinguish useful learning from activity.",
                "deliverable": "A compact evidence-backed assessment of the preceding session's effect and one revised process decision.",
                "success_evidence_criterion": "A concrete observable comparison supports RETAIN, IMPROVE, REJECT, or UNVERIFIED without relying on agent confidence.",
                "stop_condition": "Stop once one discriminating observation determines whether the preceding intervention merits retention, change, rejection, or remains unverified.",
                "out_of_scope": "No broad research sweep, no unrelated code redesign, and no new benchmark family merely to create activity.",
                "verification_requirement": "Cross-check the claim against durable repository evidence and at least one independent artifact or observation.",
            })
        else:
            slug = "test-prior-process-intervention"
            candidates.append({
                "task_id": task_id(agent_number, slug),
                "agent_number": agent_number,
                "role": role,
                "objective": "Use the current learning process to test the highest-value unresolved research implication of the preceding intervention.",
                "primary_question": "Does the preceding process decision improve the quality or discrimination of the next bounded research action?",
                "bottleneck": f"Need empirical evidence for the preceding decision ({prev_decision}).",
                "information_gap": prev_next or "Whether the preceding process decision produces better evidence than the prior baseline.",
                "bounded_action": "Run one controller-approved research comparison or independent reproduction that directly tests the preceding process decision; stop after the result can discriminate between the competing explanations.",
                "deliverable": "One reproducible research result plus an explicit assessment of whether the preceding process intervention helped.",
                "success_evidence_criterion": "The comparison produces new evidence, falsification, or strong negative evidence that could change the next task decision.",
                "stop_condition": "Stop immediately after the bounded comparison answers the primary question or becomes clearly non-discriminating.",
                "out_of_scope": "No general scanning, no challenge-ID targeting, no hidden-evaluator inference, and no unrelated infrastructure edits.",
                "verification_requirement": "Use a fresh request, control, or independent reproduction when the target supports it; preserve negative evidence.",
            })

    if not candidates:
        if role == "LEARNING_PROCESS":
            prioritized = [
                ("selection-concentration", "task-selection-bias",
                 "Is current task selection over-favoring already-explored or low-yield directions?",
                 "Repeated or converged work may be consuming effort without reducing meaningful uncertainty.",
                 "Compare recent durable task choices with their observed outcomes; identify one decision rule that would preferentially select a more discriminating unresolved question.",
                 "A compact comparison shows whether selection concentration is a real bottleneck and whether one bounded rule change is justified."),
                ("evidence-mismatch", "falsification-quality",
                 "Is the current research process biased toward plausible claims that lack decisive independent verification?",
                 "Claims are useful only when evidence can discriminate them from benign alternatives.",
                 "Inspect the strongest recent claim and run one falsification or control check that targets its key alternative explanation.",
                 "A concrete control either removes the concern or demonstrates an evidence-quality gap that should change process."),
                ("persistence", "durable-learning-gap",
                 "Does the current persistence mechanism preserve the information future agents actually need to choose better work?",
                 "Recurring loss, overwrite, or low-signal handoffs can force repeated rediscovery.",
                 "Trace one recent handoff from observation to durable state and identify one missing or ambiguous decision-relevant fact.",
                 "The trace identifies a specific persistence defect or shows that the current mechanism is adequate."),
                ("hypothesis-frontier", "hypothesis-diversity",
                 "Is the current hypothesis-generation process exploring sufficiently different explanations for the unresolved frontier?",
                 "A narrow hypothesis distribution reduces discrimination even when activity is high.",
                 "Compare a small recent sample of hypotheses and classify whether they represent materially different explanations; propose one bounded diversification rule.",
                 "Evidence shows either meaningful diversity or a specific concentration pattern with a justified intervention."),
            ]
            for signal, slug, question, bottleneck, action, criterion in prioritized:
                if signal in signals:
                    candidates.append({
                        "task_id": task_id(agent_number, slug),
                        "agent_number": agent_number,
                        "role": role,
                        "objective": "Improve or evaluate the research-learning process at the highest-value observed bottleneck.",
                        "primary_question": question,
                        "bottleneck": bottleneck,
                        "information_gap": f"Current durable signals: {', '.join(signals)}. Evidence excerpt: {excerpt[:900]}",
                        "bounded_action": action,
                        "deliverable": "A compact process diagnosis with one decision: IMPROVE, RETAIN, REJECT, or UNVERIFIED.",
                        "success_evidence_criterion": criterion,
                        "stop_condition": "Stop after the single bounded comparison is sufficient to choose one process decision.",
                        "out_of_scope": "No broad redesign, no unrelated security sweep, no hidden benchmark inference, and no changes to protected controller infrastructure.",
                        "verification_requirement": "Use recent durable evidence and one independent artifact, comparison, or observation before making the process decision.",
                    })
                    break
        else:
            slug = "frontier-advance"
            open_next = previous.get("NEXT", "") if previous else ""
            candidates.append({
                "task_id": task_id(agent_number, slug),
                "agent_number": agent_number,
                "role": role,
                "objective": "Advance the highest-value unresolved authorized research question using the current learner.",
                "primary_question": "What single bounded research action can most reduce the highest-value unresolved uncertainty on the current frontier?",
                "bottleneck": "The current research frontier still contains at least one unresolved, decision-relevant uncertainty.",
                "information_gap": open_next or f"Durable frontier signals: {', '.join(signals)}. Evidence excerpt: {excerpt[:900]}",
                "bounded_action": "Select one unresolved hypothesis or research frontier from durable evidence and execute exactly one discriminating experiment or independent reproduction with a control.",
                "deliverable": "One reproducible research observation, falsification, or strong negative result tied to the selected frontier question.",
                "success_evidence_criterion": "The bounded action materially changes what the controller should believe or do next.",
                "stop_condition": "Stop when the single experiment has a discriminating result or becomes clearly non-informative.",
                "out_of_scope": "No broad exploratory campaign, no hidden-evaluator inference, no unauthorized target expansion, and no unrelated infrastructure work.",
                "verification_requirement": "Record the exact observation and preserve the control/negative evidence needed for independent review.",
            })

    selected = candidates[0]
    # Enforce the controller-owned identity regardless of which candidate template
    # produced the selected task. This is a firewall invariant, not worker input.
    selected["agent_number"] = agent_number
    selected["role"] = role
    selected["candidate_count"] = len(candidates)
    selected["selection_basis"] = {
        "signals": signals,
        "durable_evidence_excerpt": excerpt,
        "previous_task_id": previous.get("TASK_ID", "") if previous else "",
        "previous_decision": previous.get("DECISION", "") if previous else "",
    }
    return selected, candidates, excerpt


def write_brief(task: dict[str, Any], brief_path: Path) -> None:
    lines = [
        f"# Controller-selected focused task — Agent {int(task['agent_number']):02d} (campaign slot {int(task['campaign_slot'])}/10)",
        "",
        f"ROLE: {task['role']}",
        f"TASK_ID: {task['task_id']}",
        "",
        "## Objective",
        task["objective"],
        "",
        "## Primary question",
        task["primary_question"],
        "",
        "## Bottleneck",
        task["bottleneck"],
        "",
        "## Information gap",
        task["information_gap"],
        "",
        "## Bounded action",
        task["bounded_action"],
        "",
        "## Deliverable",
        task["deliverable"],
        "",
        "## Evidence gate",
        task["success_evidence_criterion"],
        "",
        "## Stop condition",
        task["stop_condition"],
        "",
        "## Out of scope",
        task["out_of_scope"],
        "",
        "## Verification requirement",
        task["verification_requirement"],
        "",
        "## Session contract",
        "ONE primary question.",
        "ONE bounded objective.",
        "ONE meaningful deliverable.",
        "ONE evidence gate.",
        "ONE explicit stop condition.",
        "ZERO intentional scope expansion.",
        "Previous-agent claims are hypotheses until independently verified.",
        "Do not launch another Kilo session, workflow, recursive agent, or hidden campaign.",
        "Do not commit or push.",
        "Do not modify protected controller artifacts.",
        "Use durable repository state and this task brief as the communication medium.",
        "Before finishing, create state/campaign/RESULT.md using every required RESULT field from AGENTS.md.",
    ]
    brief_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_json_file(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_manifest(campaign_dir: Path) -> dict[str, Any]:
    manifest = load_json_file(campaign_dir / CAMPAIGN_MANIFEST_NAME)
    if not isinstance(manifest, dict):
        raise SystemExit("CAMPAIGN_MANIFEST_MISSING")
    required = ("campaign_id", "agent_count", "starting_agent_number", "ending_agent_number")
    if any(key not in manifest for key in required):
        raise SystemExit("CAMPAIGN_MANIFEST_INVALID")
    if int(manifest["agent_count"]) != CAMPAIGN_AGENT_COUNT:
        raise SystemExit("CAMPAIGN_AGENT_COUNT_INVALID")
    return manifest


def command_start_campaign(args: argparse.Namespace) -> int:
    root = Path(args.root)
    campaign_dir = root / "state" / "campaign"
    campaign_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = campaign_dir / CAMPAIGN_MANIFEST_NAME
    existing = load_json_file(manifest_path)
    if isinstance(existing, dict) and existing.get("campaign_id") == args.campaign_id:
        print(json.dumps(existing, sort_keys=True))
        return 0

    counter_path = campaign_dir / GLOBAL_COUNTER_NAME
    counter = load_json_file(counter_path, {})
    next_agent = int(counter.get("next_agent_number", 1) or 1)
    if next_agent < 1:
        raise SystemExit("GLOBAL_AGENT_COUNTER_INVALID")

    start = next_agent
    end = start + CAMPAIGN_AGENT_COUNT - 1
    manifest = {
        "schema_version": 1,
        "campaign_id": str(args.campaign_id),
        "agent_count": CAMPAIGN_AGENT_COUNT,
        "starting_agent_number": start,
        "ending_agent_number": end,
        "allocation": "RESERVED",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    counter_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "next_agent_number": end + 1,
                "last_reserved_campaign_id": str(args.campaign_id),
                "last_reserved_ending_agent_number": end,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


def command_prepare(args: argparse.Namespace) -> int:
    root = Path(args.root)
    campaign_dir = root / "state" / "campaign"
    campaign_dir.mkdir(parents=True, exist_ok=True)
    agent_dir = Path(args.agent_root)
    agent_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(campaign_dir)
    slot = int(args.campaign_slot)
    if slot < 1 or slot > CAMPAIGN_AGENT_COUNT:
        raise SystemExit("CAMPAIGN_SLOT_INVALID")
    agent_number = int(manifest["starting_agent_number"]) + slot - 1

    task, candidates, _ = build_task(agent_number, root, campaign_dir)
    task["agent_number"] = agent_number
    task["campaign_slot"] = slot
    task["campaign_id"] = str(manifest["campaign_id"])
    task["campaign_agent_count"] = CAMPAIGN_AGENT_COUNT
    task["role"] = "LEARNING_PROCESS" if agent_number % 2 else "HIGHER_ORDER_RESEARCH"
    errors = validate_task(task)
    if errors:
        raise SystemExit("TASK_FIREWALL_REJECTED: " + "; ".join(errors))

    (agent_dir / "state" / "campaign").mkdir(parents=True, exist_ok=True)
    (agent_dir / "state" / "campaign" / "TASK.json").write_text(
        json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (agent_dir / "state" / "campaign" / "TASK_CANDIDATES.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    context_dir = Path(args.context_dir)
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / f"agent_{agent_number:02d}_TASK.json").write_text(
        json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_brief(task, context_dir / f"agent_{agent_number:02d}_TASK.md")
    print(json.dumps({
        "task_id": task["task_id"],
        "agent_number": agent_number,
        "campaign_slot": slot,
        "campaign_id": manifest["campaign_id"],
        "role": task["role"],
        "candidate_count": task["candidate_count"],
    }, sort_keys=True))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    errors = validate_task(task)
    if errors:
        raise SystemExit("TASK_INVALID: " + "; ".join(errors))
    print("TASK_VALID=1")
    return 0


def command_validate_result(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    errors = validate_result(Path(args.result), task)
    if errors:
        raise SystemExit("RESULT_INVALID: " + "; ".join(errors))
    print("RESULT_VALID=1")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    start_campaign = sub.add_parser("start-campaign")
    start_campaign.add_argument("--root", required=True)
    start_campaign.add_argument("--campaign-id", required=True)
    start_campaign.set_defaults(func=command_start_campaign)

    prepare = sub.add_parser("prepare-agent")
    prepare.add_argument("--root", required=True)
    prepare.add_argument("--agent-root", required=True)
    prepare.add_argument("--context-dir", required=True)
    prepare.add_argument("--campaign-slot", type=int, required=True)
    prepare.set_defaults(func=command_prepare)

    validate = sub.add_parser("validate-task")
    validate.add_argument("--task", required=True)
    validate.set_defaults(func=command_validate)

    validate_result_cmd = sub.add_parser("validate-result")
    validate_result_cmd.add_argument("--task", required=True)
    validate_result_cmd.add_argument("--result", required=True)
    validate_result_cmd.set_defaults(func=command_validate_result)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
