# Blind Benchmark Harness

Implementation-only control-plane components for the Endless Hardcore Benchmark.

- `generate_benchmark.py` creates a hidden mutation specification and cryptographic commitment when a new campaign is needed.
- `mutator.py` proxies a pinned Juice Shop instance and applies the controller-selected hidden campaign overlay.
- `evaluate_benchmark.py` replays worker evidence against an evaluator-only network and writes aggregate results plus a solve decision.
- `benchmark_campaign.py` keeps an unsolved hidden campaign alive across activations using controller-only workflow state.

The worker does not receive this directory as part of its workspace.

The harness must never mutate authorization, safety, repository control-plane, credential, or truth-reporting invariants.

The benchmark is intentionally a **Juice Shop-derived black-box target**, not a claim that every generated case corresponds to a real-world vulnerability. The evaluator measures research behavior and reproducible discovery.
