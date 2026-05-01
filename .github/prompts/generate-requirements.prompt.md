# Generate Requirements For YouTube Fact Check Tool

You are working in the `youtube-factcheck-tool` repository, which is an existing dual stack codebase with a Python API and a native PowerShell pipeline.

## Goal

Create or update a numbered spec package requirement document that reflects a real change needed in this repository.

## Instructions

1. Inspect the current repo before writing requirements.
2. Anchor requirements to existing folders, modules, and entry points.
3. Preserve current working behavior unless the requested change explicitly replaces it.
4. Distinguish current state facts from proposed behavior.
5. Write concrete, testable requirements.
6. Include non goals when the request could accidentally expand scope.
7. Call out impacts on:
   - `python_app`
   - `python_tests`
   - `powershell_app`
   - `powershell_tests`
   - config and `.env.example`
   - `README.md` and `CHANGELOG.md`

## Output Format

Update `specs/<NNN-name>/requirements.md`

Include:

1. Change summary
2. Current baseline
3. Numbered functional requirements
4. Numbered non functional requirements
5. Non goals
6. Acceptance signals

Do not write implementation details here. Save those for `spec.md` and `plan.md`.
