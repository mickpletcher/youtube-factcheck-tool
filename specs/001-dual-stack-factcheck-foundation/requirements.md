# Requirements

## Change Summary

Retrofit this repository with a GitHub Copilot spec workflow so future non trivial work can follow a consistent requirements, spec, plan, task, audit, and regression process.

## Current Baseline

1. The repository already has a Python implementation in `python_app`.
2. The repository already has a native PowerShell implementation in `powershell_app`.
3. Root docs currently explain setup and usage, but there is no numbered spec package workflow.
4. There is no repo specific Copilot instruction file or reusable prompt set in `.github/prompts`.

## Functional Requirements

1. The repository must include a repo specific Copilot instruction file under `.github/`.
2. The repository must include reusable prompts for requirements, spec, plan, tasks, audit, implementation, regression, and release review.
3. The repository must include a numbered baseline spec package under `specs/` that documents the current repository foundation.
4. The baseline spec package must describe the current dual stack architecture and not invent unimplemented features.
5. The repository must include a tracked audit style document that gives future agents and engineers a quick current state reference.
6. The root `README.md` must link to the spec workflow assets and explain how future work should use them.

## Non Functional Requirements

1. The retrofit must preserve the current runtime behavior.
2. The retrofit must preserve the current repo layout.
3. The retrofit docs must use file names and commands that match the live repo.
4. The retrofit must be practical for both human contributors and coding agents.

## Non Goals

1. Do not redesign the fact check pipeline.
2. Do not change the Python or PowerShell report contract.
3. Do not add CI workflow changes in this retrofit.
4. Do not add new product features unrelated to the spec workflow.

## Acceptance Signals

1. `.github/copilot-instructions.md` exists with repo specific guidance.
2. `.github/prompts/` contains the reusable prompt set.
3. `specs/001-dual-stack-factcheck-foundation/` exists with `requirements.md`, `spec.md`, `plan.md`, and `tasks.md`.
4. `docs/repo-audit.md` exists and reflects the current repo.
5. `README.md` points contributors to the new spec workflow.
