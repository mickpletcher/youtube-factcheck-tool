# Tasks

- [x] T001 Add `.github/copilot-instructions.md` with repo specific workflow rules.
  Files: `.github/copilot-instructions.md`
  Verification: File exists and reflects the current dual stack repo.

- [x] T002 Add reusable prompt files under `.github/prompts/`.
  Files: `.github/prompts/*.prompt.md`
  Verification: Prompt set exists for requirements, spec, plan, tasks, audit, implementation, regression, and release review.

- [x] T003 Add a tracked current state audit document.
  Files: `docs/repo-audit.md`
  Verification: File exists and matches the current repo baseline.

- [x] T004 Add baseline numbered spec package for the current repository foundation.
  Files: `specs/001-dual-stack-factcheck-foundation/*`
  Verification: `requirements.md`, `spec.md`, `plan.md`, and `tasks.md` all exist.

- [x] T005 Update root docs to expose the new workflow.
  Files: `README.md`, `CHANGELOG.md`
  Verification: README links to the new audit and spec files.

- [x] T006 Run regression checks after the retrofit.
  Files: none
  Verification: `py -3.11 -m pytest python_tests -q` and `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1`
