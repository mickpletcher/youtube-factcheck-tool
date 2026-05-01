# Plan

## Objective

Add a GitHub Copilot spec workflow to this repository without changing the current Python or PowerShell runtime behavior.

## Assumptions

1. The existing repo structure remains the source of truth.
2. The baseline spec package should describe the current state, not a future redesign.
3. Existing tests remain the regression gate for this retrofit.

## Ordered Phases

### Phase 1

Create the workflow scaffolding.

Files:

1. `.github/copilot-instructions.md`
2. `.github/prompts/*.prompt.md`

Validation:

1. Confirm the files exist in the expected locations.

### Phase 2

Create the baseline repository documentation package.

Files:

1. `docs/repo-audit.md`
2. `specs/001-dual-stack-factcheck-foundation/requirements.md`
3. `specs/001-dual-stack-factcheck-foundation/spec.md`
4. `specs/001-dual-stack-factcheck-foundation/plan.md`
5. `specs/001-dual-stack-factcheck-foundation/tasks.md`

Validation:

1. Confirm the package reflects the live repo structure and commands.

### Phase 3

Expose the workflow in tracked top level docs.

Files:

1. `README.md`
2. `CHANGELOG.md`

Validation:

1. Confirm the README links point to tracked files.

### Phase 4

Run regression checks.

Files:

1. No new source files

Validation:

1. `py -3.11 -m pytest python_tests -q`
2. `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1`

## Rollback And Safety Notes

1. This retrofit should be reversible by removing the added workflow files if needed.
2. No runtime entry point or API contract should change in this work.
