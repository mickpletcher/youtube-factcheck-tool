# Specification

## Scope

This retrofit adds a GitHub Copilot spec workflow to the existing repository. It does not change the fact check runtime behavior.

## Baseline Architecture

1. `python_app` contains a FastAPI route plus service modules for metadata, transcript fetch, claim extraction, research, verdict scoring, and report generation.
2. `powershell_app` contains a native PowerShell pipeline and script entry point for the same workflow.
3. `python_tests` and `powershell_tests` provide current verification coverage.
4. Root docs currently provide setup, usage, and change tracking.

## Proposed Design

1. Add `.github/copilot-instructions.md` with repository rules for dual stack fact check work.
2. Add `.github/prompts/` with prompt files that support:
   1. Requirements generation
   2. Spec generation
   3. Plan generation
   4. Task generation
   5. Audit review
   6. Implementation from spec
   7. Regression testing
   8. Release readiness review
3. Add `docs/repo-audit.md` as a tracked current state snapshot.
4. Add `specs/001-dual-stack-factcheck-foundation/` as the baseline numbered spec package for this repository.
5. Update `README.md` and `CHANGELOG.md` so the new workflow is visible and tracked.

## Impacted Files And Folders

1. `.github/copilot-instructions.md`
2. `.github/prompts/*.prompt.md`
3. `docs/repo-audit.md`
4. `specs/001-dual-stack-factcheck-foundation/requirements.md`
5. `specs/001-dual-stack-factcheck-foundation/spec.md`
6. `specs/001-dual-stack-factcheck-foundation/plan.md`
7. `specs/001-dual-stack-factcheck-foundation/tasks.md`
8. `README.md`
9. `CHANGELOG.md`

## Data And Control Flow

1. Contributor identifies a non trivial change.
2. Contributor creates the next numbered folder under `specs/`.
3. Contributor uses the prompts to produce `requirements.md`, `spec.md`, `plan.md`, and `tasks.md`.
4. Implementation work proceeds against that package.
5. Audit and regression prompts are used before merge.

## Testing And Verification Strategy

1. Validate that the new docs and folders exist at the expected paths.
2. Run the existing Python tests to confirm no Python behavior regressed.
3. Run the existing PowerShell tests to confirm no PowerShell behavior regressed.

## Rollout And Compatibility Notes

1. This is a documentation and workflow retrofit.
2. It is backward compatible with the current codebase.
3. Future numbered spec folders should follow the same shape as `001-dual-stack-factcheck-foundation`.

## Out Of Scope

1. CI changes
2. Runtime code refactors unrelated to the workflow retrofit
3. Feature parity changes between Python and PowerShell
