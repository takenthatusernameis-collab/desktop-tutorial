#!/usr/bin/env python3
"""Deterministic tests for the research-program controller."""

import json
import tempfile
from pathlib import Path

import research_program as rp


def sample_program(benchmark_id="b1"):
    return {
        "program_version": rp.PROGRAM_VERSION,
        "benchmark_id": benchmark_id,
        "discovery": {
            "surface_map_exhaustive": False,
            "open_world": True,
            "uncertainty_notes": ["initial map is a seed"],
        },
        "surfaces": [
            {
                "surface_id": "surface-a",
                "name": "A",
                "description": "test surface",
                "origin": "kilo",
                "status": "ACTIVE",
                "priority": 1,
                "current_intensity": 2,
                "coverage_estimate": 0.1,
                "uncertainty": 0.8,
                "reasonable_effort_evidence": {"generations": 0},
                "promising_branches": [],
                "known_anomalies": [],
                "related_surfaces": [],
                "evolutionary_families": ["family-a"],
                "reopen_triggers": ["new endpoint"],
                "history": [],
            },
            {
                "surface_id": "surface-b",
                "name": "B",
                "description": "maintenance surface",
                "origin": "kilo",
                "status": "DEPRIORITIZED",
                "priority": 0.2,
                "current_intensity": 1,
                "coverage_estimate": 0.6,
                "uncertainty": 0.4,
                "reasonable_effort_evidence": {"generations": 0},
                "promising_branches": [],
                "known_anomalies": [],
                "related_surfaces": [],
                "evolutionary_families": ["family-b"],
                "reopen_triggers": ["new anomaly"],
                "history": ["low-yield retained"],
            },
        ],
        "evolution_families": [
            {
                "family_id": "family-a",
                "surface_id": "surface-a",
                "name": "query",
                "purpose": "read-only query differential testing",
                "status": "ACTIVE",
                "generation": 1,
                "population_size": 8,
                "mutation_operators": ["BASELINE", "QUERY_EDGE_VALUES"],
                "selection_policy": "reproducible differences",
                "exploration_exploitation_policy": "balanced",
                "novelty_requirement": "new response signature",
                "seed_requests": [{"method": "GET", "path": "/search", "query": {"q": "alpha"}, "headers": {}}],
                "best_candidates": [],
                "lineage": [],
                "results_history": [],
                "coverage_history": [],
                "information_gain_history": [],
                "false_positive_history": [],
                "independent_reproduction_history": [],
                "reasonable_effort_contribution": {},
                "last_kilo_review": "initial",
                "next_generation_specification": "continue",
            },
            {
                "family_id": "family-b",
                "surface_id": "surface-b",
                "name": "header",
                "purpose": "CORS differential",
                "status": "ACTIVE",
                "generation": 1,
                "population_size": 4,
                "mutation_operators": ["BASELINE", "HEADER_ORIGIN_VARIANTS"],
                "selection_policy": "reproducible differences",
                "exploration_exploitation_policy": "maintenance",
                "novelty_requirement": "new header behavior",
                "seed_requests": [{"method": "GET", "path": "/api", "query": {}, "headers": {}}],
                "best_candidates": [],
                "lineage": [],
                "results_history": [],
                "coverage_history": [],
                "information_gain_history": [],
                "false_positive_history": [],
                "independent_reproduction_history": [],
                "reasonable_effort_contribution": {},
                "last_kilo_review": "initial",
                "next_generation_specification": "maintenance",
            },
        ],
        "portfolio_policy": {
            "max_generations_per_activation": 8,
            "max_candidates_per_generation": 8,
            "exploration_reserve_fraction": 0.25,
        },
    }


def test_new_and_bootstrap(tmp: Path):
    assert rp.run_pre_kilo("fresh", "new", "http://lab-mutator:3000", tmp) == 0
    marker = rp.load_json(tmp / "DISCOVERY_REQUIRED.json")
    assert marker["surface_map_exhaustive"] is False

    (tmp / rp.PROGRAM).unlink(missing_ok=True)
    assert rp.run_pre_kilo("resumed", "old", "http://lab-mutator:3000", tmp) == 0
    marker = rp.load_json(tmp / "DISCOVERY_REQUIRED.json")
    assert marker["discovery"] == "KILO_DISCOVERY_BOOTSTRAP"


def test_portfolio_compiler_and_continuity(tmp: Path):
    program = sample_program()
    rp.write_json(tmp / rp.PROGRAM, program)
    assert len(rp.compile_portfolio(program, rp.load_runtime(tmp))) == 2

    broken = json.loads(json.dumps(program))
    broken["surfaces"] = [broken["surfaces"][0]]
    try:
        rp.validate_continuity(program, broken)
    except rp.ProgramError:
        pass
    else:
        raise AssertionError("surface deletion was accepted")

    invalid = json.loads(json.dumps(program))
    invalid["discovery"]["surface_map_exhaustive"] = True
    try:
        rp.validate_program(invalid, "b1")
    except rp.ProgramError:
        pass
    else:
        raise AssertionError("exhaustive map was accepted")


def test_generation_receipts(tmp: Path):
    program = sample_program()
    rp.write_json(tmp / rp.PROGRAM, program)
    server_response = {
        ("GET", "/search", ""): {"status": 200, "body_sha256": "a", "content_type": "text/plain", "body_length": 5, "location": "", "error": None},
        ("GET", "/search", "q=alpha"): {"status": 200, "body_sha256": "a", "content_type": "text/plain", "body_length": 5, "location": "", "error": None},
    }

    def fake_transport(_target, req):
        from urllib.parse import urlencode
        query = urlencode([(k, v) for k in sorted(req["query"]) for v in req["query"][k]], doseq=True)
        key = (req["method"], req["path"], query)
        value = dict(server_response.get(key, {"status": 200, "body_sha256": "b", "content_type": "text/plain", "body_length": 4, "location": "", "error": None}))
        return value

    state = tmp / "controller"
    result = rp.execute_generation(
        state,
        "http://lab-mutator:3000",
        program["evolution_families"][0],
        1,
        8,
        transport=fake_transport,
    )
    assert result["actual_execution"] is True
    assert result["candidate_count"] > 0
    rp.persist_generation(state, result)
    receipt_rows = rp.read_jsonl(state / rp.RECEIPTS)
    assert len(receipt_rows) == 1
    assert receipt_rows[0]["actual_execution"] is True


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        test_new_and_bootstrap(root / "a")
        test_portfolio_compiler_and_continuity(root / "b")
        test_generation_receipts(root / "c")
    print("research program tests: PASS")


if __name__ == "__main__":
    main()
