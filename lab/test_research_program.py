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
    assert rp.validate_state(tmp, "new", "fresh") is None

    rp.write_json(tmp / rp.PROGRAM, sample_program("new"))
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
    prose["surfaces"][0]["current_intensity"] = "full"
    prose["surfaces"][1]["current_intensity"] = "minimal"
    rp.validate_program(prose, "b1")
    plan = rp.compile_portfolio(prose, rp.load_runtime(tmp))
    assert plan
    assert max(item["round"] for item in plan) == 4
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

    generation_drift = json.loads(json.dumps(program))
    generation_drift["evolution_families"][0]["generation"] += 1
    try:
        rp.validate_continuity(program, generation_drift)
    except rp.ProgramError as exc:
        assert "generation changed" in str(exc)
    else:
        raise AssertionError("worker proposal was allowed to change controller-owned generation")

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
    """Exercise handoff while keeping the controller-owned generation cursor unchanged."""
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
    # Execution generation is controller-owned; the worker proposal may evolve
    # strategy content but must preserve the current execution cursor.
    evolved_family["generation"] = 1
    proposal_path = tmp / "PROGRAM_PROPOSAL.json"
    rp.write_json(proposal_path, evolved)

    assert (
        rp.post_kilo(
            "resumed",
            "b1",
            state,
            snapshot,
            proposal_path,
        ) == 0
    ), "post-Kilo validation rejected deterministic PROGRAM_PROPOSAL.json"
    assert rp.load_json(state / rp.PROGRAM) == evolved

def test_method_variant_is_seed_safe():
    head_seed = {
        "method": "HEAD",
        "path": "/health",
        "query": {},
        "headers": {},
    }
    assert rp.mutate_request(head_seed, "METHOD_VARIANTS") == []


def test_validation_rejects_malformed_best_candidate(tmp: Path):
    program = sample_program("candidate-contract")
    candidate = {
        "candidate_id": "wrong-id",
        "parent_candidate_id": None,
        "request": {
            "method": "GET",
            "path": "/search",
            "query": {"q": ["alpha"]},
            "headers": {},
        },
        "mutation": {"operator": "BASELINE"},
        "response_signature": [200, "sha", "text/plain", 4, ""],
    }
    program["evolution_families"][0]["best_candidates"] = [candidate]
    try:
        rp.validate_program(program, "candidate-contract")
    except rp.ProgramError as exc:
        assert "candidate_id" in str(exc)
    else:
        raise AssertionError("malformed best candidate was accepted")


def test_validation_rejects_mismatched_surface_family_reference(tmp: Path):
    program = sample_program("family-reference")
    program["surfaces"][0]["evolutionary_families"] = ["family-b"]
    try:
        rp.validate_program(program, "family-reference")
    except rp.ProgramError as exc:
        assert "owned by" in str(exc)
    else:
        raise AssertionError("mismatched surface family reference was accepted")


def test_validation_rejects_zero_candidate_family(tmp: Path):
    program = sample_program("zero-candidate")
    family = program["evolution_families"][0]
    family["seed_requests"] = [
        {"method": "GET", "path": "/health", "query": {}, "headers": {}}
    ]
    family["mutation_operators"] = ["QUERY_EDGE_VALUES"]
    try:
        rp.validate_program(program, "zero-candidate")
    except rp.ProgramError as exc:
        assert "zero candidates" in str(exc)
    else:
        raise AssertionError("zero-candidate family was accepted")


def test_portfolio_validation_rejects_budget_below_breadth(tmp: Path):
    program = sample_program("budget")
    program["portfolio_policy"]["max_generations_per_activation"] = 1
    try:
        rp.validate_program(program, "budget")
    except rp.ProgramError as exc:
        assert "surface breadth" in str(exc)
    else:
        raise AssertionError("undersized portfolio budget was accepted")


def test_portfolio_budget_preserves_surface_breadth(tmp: Path):
    program = sample_program("breadth")
    # Simulate many high-priority families on one surface competing with a second
    # surface under a deliberately tiny activation budget.
    extras = []
    for index in range(10):
        family = json.loads(json.dumps(program["evolution_families"][0]))
        family["family_id"] = f"family-extra-{index}"
        family["surface_id"] = "surface-a"
        extras.append(family)
    program["evolution_families"].extend(extras)
    program["portfolio_policy"]["max_generations_per_activation"] = 2

    rp.validate_program(program, "breadth")
    plan = rp.compile_portfolio(program, rp.load_runtime(tmp))
    assert len(plan) == 2
    assert {item["surface_id"] for item in plan} == {"surface-a", "surface-b"}


def test_multi_round_pre_kilo_advances_runtime_per_generation(tmp: Path):
    program = sample_program("multi-round")
    program["surfaces"][0]["current_intensity"] = "full"
    program["portfolio_policy"]["max_generations_per_activation"] = 3
    rp.write_json(tmp / rp.PROGRAM, program)

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

    assert (
        rp.run_pre_kilo(
            "resumed",
            "multi-round",
            "http://lab-mutator:3000",
            tmp,
            transport=fake_transport,
        )
        == 0
    )
    runtime = rp.load_json(tmp / rp.RUNTIME)
    persisted = rp.load_json(tmp / rp.PROGRAM)
    assert runtime["families"]["family-a"]["last_executed_generation"] == 2
    assert persisted["evolution_families"][0]["generation"] == 3
    assert runtime["families"]["family-b"]["last_executed_generation"] == 1


def test_validate_state_repairs_ahead_generation_cursor(tmp: Path):
    program = sample_program("repair")
    program["evolution_families"][0]["generation"] = 5
    rp.write_json(tmp / rp.PROGRAM, program)
    rp.write_json(
        tmp / rp.RUNTIME,
        {
            "schema_version": rp.PROGRAM_VERSION,
            "controller_version": rp.CONTROLLER_VERSION,
            "benchmark_id": "repair",
            "families": {
                "family-a": {"last_executed_generation": 3}
            },
            "surfaces": {},
        },
    )
    validated = rp.validate_state(tmp, "repair", "resumed")
    repaired_family = next(
        f for f in validated["evolution_families"] if f["family_id"] == "family-a"
    )
    assert repaired_family["generation"] == 4
    persisted = rp.load_json(tmp / rp.PROGRAM)
    assert persisted["evolution_families"][0]["generation"] == 4


def test_validate_state_rejects_generation_divergence(tmp: Path):
    program = sample_program("continuity")
    rp.write_json(tmp / rp.PROGRAM, program)
    rp.write_json(
        tmp / rp.RUNTIME,
        {
            "schema_version": rp.PROGRAM_VERSION,
            "controller_version": rp.CONTROLLER_VERSION,
            "benchmark_id": "continuity",
            "families": {
                "family-a": {"last_executed_generation": 2}
            },
            "surfaces": {},
        },
    )
    try:
        rp.validate_state(tmp, "continuity", "resumed")
    except rp.ProgramError as exc:
        assert "generation continuity divergence" in str(exc)
    else:
        raise AssertionError("generation divergence was accepted")


def test_materialize_string_effort_evidence(tmp: Path):
    program = sample_program("materialize")
    program["surfaces"][0]["reasonable_effort_evidence"] = "fresh prose evidence"
    rp.write_json(tmp / rp.PROGRAM, program)
    rp.materialize_registries(tmp, program, rp.load_runtime(tmp))
    surfaces = rp.load_json(tmp / rp.SURFACES)
    effort = surfaces["surfaces"][0]["reasonable_effort_evidence"]
    assert effort["evidence"] == "fresh prose evidence"
    assert effort["generations"] == 0


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
        test_portfolio_budget_preserves_surface_breadth(root / "f")
        test_portfolio_validation_rejects_budget_below_breadth(root / "g")
        test_validation_rejects_zero_candidate_family(root / "h")
        test_validation_rejects_malformed_best_candidate(root / "l")
        test_validation_rejects_mismatched_surface_family_reference(root / "m")
        test_method_variant_is_seed_safe()
        test_materialize_string_effort_evidence(root / "i")
        test_validate_state_rejects_generation_divergence(root / "j")
        test_multi_round_pre_kilo_advances_runtime_per_generation(root / "k")
        test_post_kilo_execution_regression(root / "post-kilo")
    print("research program tests: PASS")


if __name__ == "__main__":
    main()
