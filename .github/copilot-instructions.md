# YouTube Fact Check Tool Copilot Instructions

## Scope

This repository is an existing dual stack fact check tool with a Python API and a native PowerShell pipeline. Treat it as a retrofit first codebase, not a greenfield project.

## Core Rules

1. Preserve the current Python and PowerShell runtime surfaces unless a change explicitly replaces one of them.
2. Favor additive changes over rewrites.
3. Keep the shared report contract aligned across both implementations.
4. Do not silently invent product capabilities that are not already present in the repo.
5. Keep setup and run commands accurate for Windows PowerShell.

## Architecture Rules

1. Python API code belongs in `python_app`.
2. Python tests belong in `python_tests`.
3. Native PowerShell pipeline code belongs in `powershell_app`.
4. PowerShell tests belong in `powershell_tests`.
5. Shared behavior changes should update both implementations or clearly document any intentional gap.
6. Keep orchestration logic in route and entry point layers thin when it can live in service functions.

## Configuration Rules

1. Keep `.env.example` aligned with the real settings in code.
2. Preserve the current split between `WHISPER_MODEL` for Python and `OPENAI_TRANSCRIPTION_MODEL` for PowerShell unless a spec explicitly unifies them.
3. Do not add secrets or machine specific paths to tracked files.

## Testing Expectations

1. Python changes should keep `py -3.11 -m pytest python_tests -q` passing when Python code is affected.
2. PowerShell changes should keep `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1` passing when PowerShell code is affected.
3. Avoid depending on live credentials in default tests.
4. When behavior changes, update tests and docs in the same change.

## Refactor Safety Rules

1. Do not rename top level repo folders without an explicit migration task.
2. Do not collapse the dual stack layout into a single implementation.
3. Do not remove the current JSON and Markdown report outputs unless the spec explicitly includes that change.

## Documentation Rules

1. Keep the root `README.md` aligned with the actual repo contents and commands.
2. Record significant repo shaping work under `specs/`.
3. Update `CHANGELOG.md` for meaningful structure, workflow, or behavior changes.

## Spec Driven Delivery Requirement

All future non trivial work should align to a spec package:

1. Create or update `requirements.md`
2. Create or update `spec.md`
3. Create or update `plan.md`
4. Create or update `tasks.md`
5. Implement only what the spec covers
6. Audit the implementation against the spec
7. Run regression checks before merge

If code and spec disagree, update one deliberately. Do not leave them drifting.
