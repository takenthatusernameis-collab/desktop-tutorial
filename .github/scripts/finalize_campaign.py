#!/usr/bin/env python3
"""Controller-owned final synthesis and canonical handoff gate."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from campaign_controller import OUTCOME_CLASSES, parse_result, validate_result  # noqa: E402


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def validate_findings(path: Path) -> list[str]:
    data = load_json(path)
    errors: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return ["candidate findings must contain a findings list"]
    allowed_prefix = os.environ.get("SECURITY_RESEARCH_TARGET", "http://lab-mutator:3000").rstrip("/")
    for idx, finding in enumerate(data["findings"]):
        if not isinstance(finding, dict):
            errors.append(f"finding[{idx}] is not an object")
            continue
        request = finding.get("request")
        if not isinstance(request, dict):
            errors.append(f"finding[{idx}] missing request")
            continue
        url = str(request.get("url", ""))
        if not (url.startswith(allowed_prefix + "/") or url == allowed_prefix):
            errors.append(f"finding[{idx}] request URL is outside authorized worker target")
    return errors


def prepare(args: argparse.Namespace) -> int:
    root = Path(args.root)
    campaign = root / "state" / "campaign"
    campaign.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    memos = []
    manifest = load_json(campaign / "CAMPAIGN_MANIFEST.json")
    if not isinstance(manifest, dict):
        raise SystemExit("CAMPAIGN_MANIFEST_MISSING")
    start_agent = int(manifest.get("starting_agent_number", 0) or 0)
    end_agent = int(manifest.get("ending_agent_number", 0) or 0)
    campaign_agent_count = int(manifest.get("agent_count", 0) or 0)
    if start_agent < 1 or end_agent < start_agent or campaign_agent_count != 10:
        raise SystemExit("CAMPAIGN_MANIFEST_INVALID")

    for number in range(start_agent, end_agent + 1):
        task_path = campaign / f"agent_{number:02d}_TASK.json"
        result_path = campaign / f"agent_{number:02d}_RESULT.md"
        if not task_path.is_file():
            errors.append(f"missing task for agent {number:02d}")
            continue
        if not result_path.is_file():
            errors.append(f"missing result for agent {number:02d}")
            continue
        task = load_json(task_path, {})
        result_errors = validate_result(result_path, task)
        if result_errors:
            errors.extend([f"agent {number:02d}: {item}" for item in result_errors])
        fields = parse_result(result_path)
        memos.append({
            "agent_number": number,
            "campaign_slot": number - start_agent + 1,

            "task_id": task.get("task_id", ""),
            "role": task.get("role", ""),
            "outcome": fields.get("OUTCOME_CLASS", ""),
            "decision": fields.get("DECISION", ""),
            "changed": fields.get("CHANGED", ""),
            "verified": fields.get("VERIFIED", ""),
            "unverified": fields.get("UNVERIFIED", ""),
            "observed_effect": fields.get("OBSERVED_EFFECT", ""),
            "uncertainty_targeted": fields.get("UNCERTAINTY_TARGETED", ""),
            "uncertainty_reduced": fields.get("UNCERTAINTY_REDUCED", ""),
            "next": fields.get("NEXT", ""),
        })

    if errors:
        raise SystemExit("CAMPAIGN_FINALIZATION_BLOCKED: " + " | ".join(errors))

    failures = sum(1 for row in memos if row["outcome"] == "INFRASTRUCTURE_FAILURE")
    process_decisions = [row["decision"] for row in memos if row["role"] == "LEARNING_PROCESS"]
    research_outcomes = [row["outcome"] for row in memos if row["role"] == "HIGHER_ORDER_RESEARCH"]

    candidate_findings = root / "reports" / "benchmark_findings_candidate.json"
    canonical_findings = root / "reports" / "benchmark_findings.json"
    canonical_findings.parent.mkdir(parents=True, exist_ok=True)

    finding_errors = validate_findings(candidate_findings) if candidate_findings.is_file() else []
    if candidate_findings.is_file() and not finding_errors:
        shutil.copy2(candidate_findings, canonical_findings)
        findings_source = f"AGENT_{end_agent}_CANDIDATE_PROMOTED_BY_CONTROLLER"
    else:
        canonical_findings.write_text(
            json.dumps(
                {
                    "findings": [],
                    "controller_note": (
                        f"No controller-approved final-session (Agent {end_agent}) finding candidate was available; "
                        "the empty set is an explicit research outcome, not a benchmark claim."
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        findings_source = "EMPTY_CONTROLLER_APPROVED_SET"
        if finding_errors:
            (campaign / "AGENT_10_FINDINGS_REJECTION.md").write_text(
                "\n".join(finding_errors) + "\n", encoding="utf-8"
            )

    proposal_candidate = root / "PROGRAM_PROPOSAL_CANDIDATE.json"
    proposal = root / "PROGRAM_PROPOSAL.json"
    proposal_status = "NOT_PRESENT"
    if proposal_candidate.is_file():
        validator = ROOT / ".kilo" / "validate-program-handoff.py"
        proc = __import__("subprocess").run(
            ["python3", str(validator), "--path", str(proposal_candidate)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            shutil.copy2(proposal_candidate, proposal)
            proposal_status = "PROMOTED"
        else:
            proposal_status = "REJECTED"
            (campaign / "PROGRAM_PROPOSAL_REJECTION.txt").write_text(
                proc.stdout + proc.stderr, encoding="utf-8"
            )

    counts = {name: sum(1 for row in memos if row["outcome"] == name) for name in sorted(OUTCOME_CLASSES)}
    controller_validated_process_improvements = sum(
        1 for row in memos
        if row["role"] == "LEARNING_PROCESS"
        and row["decision"] in {"IMPROVE", "RETAIN"}
        and row["observed_effect"].strip()
        and row["uncertainty_reduced"].strip()
    )

    synthesis = {
        "schema_version": 1,
        "campaign_contract": "CONTROLLED_10_AGENT_SEQUENTIAL",
        "agent_count": 10,
        "campaign_id": manifest.get("campaign_id", ""),
        "starting_agent_number": start_agent,
        "ending_agent_number": end_agent,
        "failure_count": failures,
        "outcome_class_counts": counts,
        "process_decisions": process_decisions,
        "research_outcomes": research_outcomes,
        "controller_validated_process_improvements": controller_validated_process_improvements,
        "validated_new_evidence_candidates": sum(
            1 for row in memos
            if row["outcome"] == "NEW_EVIDENCE"
            and row["verified"].strip()
            and row["uncertainty_reduced"].strip()
        ),
        "falsified_hypotheses": sum(1 for row in memos if row["outcome"] == "FALSIFIED"),
        "unresolved_uncertainty": [row["uncertainty_targeted"] for row in memos if row["uncertainty_targeted"].strip() and not row["uncertainty_reduced"].strip()],
        "research_frontier_advancement_candidates": sum(
            1 for row in memos if row["role"] == "HIGHER_ORDER_RESEARCH" and row["uncertainty_reduced"].strip()
        ),
        "complexity_added": "UNMEASURED_UNTIL_POST_EVALUATION",
        "findings_source": findings_source,
        "program_proposal_status": proposal_status,
        "highest_value_next_action": memos[-1]["next"],
        "memos": memos,
    }
    (campaign / "FINAL_SYNTHESIS.json").write_text(
        json.dumps(synthesis, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    research_report = root / "reports" / "benchmark_research.md"
    if not research_report.is_file():
        research_report.write_text(
            "# Controller Campaign Research Handoff\n\n"
            "Canonical research narrative is intentionally omitted unless the final session produced one.\n",
            encoding="utf-8",
        )

    lines = [
        "# Controller Campaign Synthesis",
        "",
        "The controller validated ten bounded task contracts and ten durable result handoffs.",
        f"- Agent failures: {failures}",
        f"- Process decisions: {', '.join(process_decisions) or 'none'}",
        f"- Controller-validated process-improvement candidates: {controller_validated_process_improvements}",
        f"- Candidate new-evidence outcomes with explicit verification/uncertainty fields: {synthesis['validated_new_evidence_candidates']}",
        f"- Falsified hypotheses: {synthesis['falsified_hypotheses']}",
        f"- Research-frontier advancement candidates: {synthesis['research_frontier_advancement_candidates']}",
        f"- Canonical findings source: {findings_source}",
        f"- Program proposal status: {proposal_status}",
        f"- Highest-value immediate next action: {memos[-1]['next']}",
        "",
        "## Interpretation boundary",
        "The controller validates structure, evidence linkage, scope, and durable handoff integrity. "
        "It does not treat agent assertions as independently proven security findings. Hidden benchmark evaluation remains authoritative for benchmark credit.",
        "",
        "## Agent decisions",
    ]
    for row in memos:
        lines.append(
            f"- Agent {row['agent_number']:02d} (campaign slot {row['campaign_slot']}/10) [{row['role']}] {row['outcome']} / {row['decision']} — {row['observed_effect'][:240]}"
        )
    (campaign / "FINAL_SYNTHESIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("CAMPAIGN_FINALIZED=1")
    return 0


def post_evaluate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    campaign = root / "state" / "campaign"
    synthesis_path = campaign / "FINAL_SYNTHESIS.json"
    if not synthesis_path.is_file():
        raise SystemExit("FINAL_SYNTHESIS_MISSING")
    synthesis = load_json(synthesis_path, {})
    result = load_json(Path(args.result), {})
    synthesis["independent_evaluation"] = {
        "finding_count_submitted": int(result.get("finding_count_submitted", 0) or 0),
        "reproduced_claim_count": int(result.get("reproduced_claim_count", 0) or 0),
        "unmatched_claim_count": int(result.get("unmatched_claim_count", 0) or 0),
        "overall_score": float(result.get("overall_score", 0.0) or 0.0),
        "discovery_rate": float(result.get("discovery_rate", 0.0) or 0.0),
        "reproduction_rate": float(result.get("reproduction_rate", 0.0) or 0.0),
        "precision_component": float(result.get("precision_component", 0.0) or 0.0),
        "evidence_quality": float(result.get("evidence_quality", 0.0) or 0.0),
    }
    synthesis["validated_new_evidence"] = synthesis["independent_evaluation"]["reproduced_claim_count"]
    synthesis["evaluation_note"] = (
        "Independent benchmark replay is the authoritative validation signal for reproduced claims; "
        "process improvements remain subject to future repeated activations."
    )
    synthesis_path.write_text(json.dumps(synthesis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = campaign / "FINAL_SYNTHESIS.md"
    existing = md.read_text(encoding="utf-8") if md.is_file() else "# Controller Campaign Synthesis\n"
    existing += (
        "\n## Independent evaluation\n"
        f"- Reproduced claims: {synthesis['validated_new_evidence']}\n"
        f"- Discovery rate: {synthesis['independent_evaluation']['discovery_rate']}\n"
        f"- Reproduction rate: {synthesis['independent_evaluation']['reproduction_rate']}\n"
        f"- Precision: {synthesis['independent_evaluation']['precision_component']}\n"
        f"- Evidence quality: {synthesis['independent_evaluation']['evidence_quality']}\n"
        f"- Overall score: {synthesis['independent_evaluation']['overall_score']}\n"
    )
    md.write_text(existing, encoding="utf-8")
    print("CAMPAIGN_EVALUATION_APPENDED=1")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("prepare", prepare), ("post-evaluate", post_evaluate)):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", required=True)
        if name == "post-evaluate":
            cmd.add_argument("--result", required=True)
        cmd.set_defaults(func=func)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
