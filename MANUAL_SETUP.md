# Manual Setup

The repository-side architecture follows the separation pattern used by X: trusted scheduler/control-plane files are distinct from autonomous worker instructions and ordinary research state.

## Worker loop

The intended workflow:
- wakes every 5 minutes;
- permits one active worker activation;
- uses a disposable GitHub-hosted runner;
- runs Kilo inside the bounded repository workspace;
- prevents recursive workflow dispatch;
- restores protected control-plane files before persistence;
- rejects high-confidence credential material and other unsafe persistence.

The workflow is research-only and must not be used as a substitute for explicit authorization.

## Optional evolutionary mode

The worker may use a controlled-mutation loop when a candidate representation, safe mutation space, and trustworthy evaluator are available.

Conceptually:

GENERATE / MUTATE -> EVALUATE -> SELECT -> PRESERVE LINEAGE -> REPEAT

This can be useful for evolving research hypotheses, prioritization heuristics, safe test harnesses, analysis rules, evidence workflows, or report transformations.

The mode is explicitly optional. It should be bypassed when simpler experimentation is more informative.

Authorization, safety, scope, credential handling, least privilege, and protected control-plane files are immutable constraints, never optimization variables.

## Authorization

Before any real target interaction, establish a clear authorization boundary from a bug-bounty program, owned system, lab, CTF, or comparable permitted environment.

Do not store credentials in the repository.

## Verification

After workflow changes are committed, manually trigger the workflow and inspect Kilo installation, free-model discovery, worker outcome, trusted persistence, and activation logging.

For evolutionary experiments, also inspect lineage/provenance, evaluator configuration, stopping conditions, promotion decisions, and any independent or held-out validation.

A green workflow or higher evaluator score alone is not proof that a security-research conclusion is correct.

## Inspiration

The optional evolutionary pattern is conceptually informed by AlphaEvolve, Google's LLM-assisted evolutionary coding system that combines candidate generation, automated evaluation, and evolutionary selection. See:
https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
https://arxiv.org/abs/2506.13131
