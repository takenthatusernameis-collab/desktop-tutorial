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

## Authorization

Before any real target interaction, establish a clear authorization boundary from a bug-bounty program, owned system, lab, CTF, or comparable permitted environment.

Do not store credentials in the repository.

## Verification

After workflow changes are committed, manually trigger the workflow and inspect Kilo installation, free-model discovery, worker outcome, trusted persistence, and the activation log.

A green workflow alone is not proof that a security-research conclusion is correct.
