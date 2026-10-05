#!/usr/bin/env python3
"""Deterministic tests for the research-program controller."""

import json
import sys
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
    persisted = rp.load_json(tmp / rp.PROGRAM)
    validated = rp.validate_state(tmp, "new", "fresh")
    assert validated["benchmark_id"] == "new"
    marker = rp.load_json(tmp / "DISCOVERY_REQUIRED.json")
    assert marker["surface_map_exhaustive"] is False

    (tmp / rp.PROGRAM).unlink(missing_ok=True)
    assert rp.run_pre_kilo("resumed", "old", "http://lab-mutator:3000", tmp) == 0
    marker = rp.load_json(tmp / "DISCOVERY_REQUIRED.json")
    assert marker["discovery"] == "KILO_DISCOVERY_BOOTSTRAP"


def test_portfolio_compiler_and_continuity(tmp: Path):
    program = sample_program()
    program["surfaces"][0]["priority"] = "HIGH"
    program["surfaces"][0]["uncertainty"] = "high - qualitative uncertainty retained from worker research"
    program["surfaces"][1]["priority"] = "LOW"
    program["surfaces"][1]["uncertainty"] = "medium - bounded maintenance uncertainty"
    rp.validate_program(program, "b1")
    compiled = rp.compile_portfolio(program, rp.load_runtime(tmp))
    assert compiled

    # Worker research may also preserve unlabelled explanatory uncertainty prose.
    prose = json.loads(json.dumps(program))
    prose["surfaces"][0]["uncertainty"] = (
        "whether the evaluator expects the current response type; "
        "text can drift between requests"
    )
    rp.validate_program(prose, "b1")
    assert rp.compile_portfolio(prose, rp.load_runtime(tmp))
    program["surfaces"][0]["status"] = "VERIFIED"
    rp.validate_program(program, "b1")
    program["surfaces"][0]["status"] = "NEGATED"
    rp.validate_program(program, "b1")
    rp.write_json(tmp / rp.PROGRAM, program)
    plan = rp.compile_portfolio(program, rp.load_runtime(tmp))
    assert len(plan) == 3
    family_a_generations = [
        item["generation"] for item in plan if item["family_id"] == "family-a"
    ]
    assert family_a_generations == [1, 2]

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
    orphan = json.loads(json.dumps(program))
    orphan["surfaces"][0]["status"] = "CANDIDATE"
    orphan["surfaces"][1]["status"] = "ACTIVE"
    orphan["surfaces"][1]["evolutionary_families"] = []
    orphan["evolution_families"] = [orphan["evolution_families"][0]]
    try:
        rp.validate_program(orphan, "b1")
    except rp.ProgramError as exc:
        assert "surface-b" in str(exc)
        assert "CANDIDATE" in str(exc)
    else:
        raise AssertionError("orphan active surface was accepted")



def test_evolution_parent_carry_forward(tmp: Path):
    program = sample_program()
    family = program["evolution_families"][0]
    state = tmp / "controller"

    def fake_transport(_target, req):
        query = req["query"].get("q", [""])[0]
        body_sha = "baseline" if query == "alpha" else "mutated"
        return {
            "status": 200,
            "body_sha256": body_sha,
            "content_type": "text/plain",
            "body_length": len(body_sha),
            "location": "",
            "error": None,
        }

    first = rp.execute_generation(
        state,
        "http://lab-mutator:3000",
        family,
        1,
        8,
        transport=fake_transport,
    )
    assert first["promising_candidates"], "first generation did not retain a reproducible parent"
    selected_request = first["promising_candidates"][0]["request"]
    assert selected_request["query"]["q"] != ["alpha"]

    rp.persist_generation(state, first)
    rp.update_runtime(state, program, [first])
    family["best_candidates"] = first["promising_candidates"]
    family["generation"] = 2

    second = rp.execute_generation(
        state,
        "http://lab-mutator:3000",
        family,
        2,
        8,
        transport=fake_transport,
    )
    selected_parent_id = rp.candidate_id(selected_request)
    assert any(
        row["parent_candidate_id"] == selected_parent_id
        for row in second["parent_lineage"]
    ), "generation 2 did not mutate from the selected parent"


def test_cross_session_program_progression(tmp: Path):
    program = sample_program()
    state = tmp / "controller"
    rp.write_json(state / rp.PROGRAM, program)
    rp.write_json(
        state / "DISCOVERY_REQUIRED.json",
        {"benchmark_id": "b1", "discovery": "KILO_DISCOVERY_BOOTSTRAP"},
    )

    family = json.loads(json.dumps(program["evolution_families"][0]))

    def fake_transport(_target, req):
        query = req["query"].get("q", [""])[0]
        body_sha = "baseline" if query == "alpha" else "mutated"
        return {
            "status": 200,
            "body_sha256": body_sha,
            "content_type": "text/plain",
            "body_length": len(body_sha),
            "location": "",
            "error": None,
        }

    first = rp.execute_generation(
        state,
        "http://lab-mutator:3000",
        family,
        1,
        8,
        transport=fake_transport,
    )
    assert first["promising_candidates"], "G1 did not produce a retained candidate"
    selected_request = first["promising_candidates"][0]["request"]
    selected_parent_id = rp.candidate_id(selected_request)

    rp.persist_generation(state, first)
    runtime = rp.update_runtime(state, program, [first])

    persisted = rp.load_json(state / rp.PROGRAM)
    persisted_family = persisted["evolution_families"][0]
    persisted_family["best_candidates"] = first["promising_candidates"]
    persisted_family["generation"] = 2
    rp.write_json(state / rp.PROGRAM, persisted)

    reloaded_program = rp.load_json(state / rp.PROGRAM)
    reloaded_family = reloaded_program["evolution_families"][0]

    second = rp.execute_generation(
        state,
        "http://lab-mutator:3000",
        reloaded_family,
        2,
        8,
        transport=fake_transport,
    )
    assert any(
        row["parent_candidate_id"] == selected_parent_id
        for row in second["parent_lineage"]
    ), "G2 did not inherit the persisted G1 parent"
    assert second["generation"] == 2

    rp.persist_generation(state, second)
    runtime = rp.update_runtime(state, reloaded_program, [second])
    assert runtime["families"]["family-a"]["last_executed_generation"] == 2

    final_program = rp.load_json(state / rp.PROGRAM)
    assert final_program["evolution_families"][0]["generation"] == 2


def test_post_kilo_execution_regression(tmp: Path):
    """Exercise the trusted post-Kilo validator against a real deterministic G1->G2 evolution."""
    program = sample_program()
    state = tmp / "state"
    snapshot = tmp / "snapshot"
    state.mkdir(parents=True, exist_ok=True)
    snapshot.mkdir(parents=True, exist_ok=True)

    rp.write_json(state / rp.PROGRAM, program)
    rp.write_json(snapshot / rp.PROGRAM, program)

    family = json.loads(json.dumps(program["evolution_families"][0]))

    def fake_transport(_target, req):
        query = req["query"].get("q", [""])[0]
        body_sha = "baseline" if query == "alpha" else "mutated"
        return {
            "status": 200,
            "body_sha256": body_sha,
            "content_type": "text/plain",
            "body_length": len(body_sha),
            "location": "",
            "error": None,
        }

    first = rp.execute_generation(
        tmp / "execution",
        "http://lab-mutator:3000",
        family,
        1,
        8,
        transport=fake_transport,
    )
    assert first["actual_execution"] is True
    assert first["promising_candidates"], "deterministic G1 produced no retained parent"

    evolved = json.loads(json.dumps(program))
    evolved_family = evolved["evolution_families"][0]
    evolved_family["best_candidates"] = first["promising_candidates"]
    evolved_family["generation"] = 2
    rp.write_json(state / rp.PROGRAM, evolved)

    assert (
        rp.post_kilo("resumed", "b1", state, snapshot) == 0
    ), "post-Kilo validation rejected deterministic evolved PROGRAM.json"

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
        if len(sys.argv) > 1 and sys.argv[1] == "--post-kilo-regression":
            test_post_kilo_execution_regression(root / "post-kilo")
            print("post-Kilo execution regression: PASS")
            return
        test_new_and_bootstrap(root / "a")
        test_portfolio_compiler_and_continuity(root / "b")
        test_generation_receipts(root / "c")
        test_cross_session_program_progression(root / "e")
        test_evolution_parent_carry_forward(root / "d")
        test_post_kilo_execution_regression(root / "post-kilo")
    print("research program tests: PASS")


if __name__ == "__main__":
    main()
