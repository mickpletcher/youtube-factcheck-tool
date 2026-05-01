# Changelog

## 2026-05-01

### Repository structure

1. Split the Python implementation into `python_app` and `python_tests`.
2. Added a native PowerShell implementation in `powershell_app` and Pester tests in `powershell_tests`.
3. Updated Python imports to use the new `python_app` package path.
4. Updated test mocks and references to match the renamed package paths.

### Documentation

1. Updated `README.md` to reflect the new repo layout.
2. Updated the run and test commands in `README.md` for the `python_app` and `python_tests` structure.
3. Updated `PROJECT_SCAN.md` so it reflects the current package layout and run commands.
4. Added `future-upgrades.md` with tiered upgrade ideas for immediate, medium term, and longer term work.
5. Expanded `README.md` into a detailed usage guide for Python and PowerShell.
6. Replaced `.env.example` with a repo specific version that matches the current Python and PowerShell settings.
7. Replaced the root `.gitignore` with repo specific ignore rules for `.env`, Python caches, local artifacts, and editor noise.
8. Rewrote `README.md` so setup and run steps match the current repo layout and PowerShell commands.

### Logging

1. Added structured stage logging to the Python fact check route for metadata, transcript fetch, claim extraction, research, verdict scoring, and report generation.
2. Added structured stage logging to the native PowerShell pipeline for metadata, transcript fetch, claim extraction, research, verdict scoring, and report generation.

### Runtime validation

1. Added Python startup validation for required external tools so the API now fails early when `yt-dlp` or `ffmpeg` is missing from `PATH`.
2. Added native PowerShell startup validation for required external tools so the pipeline now fails early when `yt-dlp` or `ffmpeg` is missing from `PATH`.

### Spec workflow

1. Added `.github/copilot-instructions.md` with repo specific guidance for dual stack fact check work.
2. Added `.github/prompts/` with reusable prompts for requirements, spec, planning, tasks, audit, implementation, regression, and release review.
3. Added `docs/repo-audit.md` as a tracked current state repo audit.
4. Added `specs/001-dual-stack-factcheck-foundation/` as the baseline GitHub Copilot spec package for this repository.
5. Updated `README.md` to expose the new spec workflow and links.

### Validation

1. Installed the Python dependencies from `requirements.txt`.
2. Ran the Python test suite with `py -3.11 -m pytest python_tests -q`.
3. Confirmed the current result is `69 passed`.
4. Ran `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1`.
5. Confirmed the current PowerShell test result is `7 passed`.
6. Ran `.\powershell_app\Invoke-YouTubeFactCheck.ps1` against a live YouTube URL and confirmed the command returns a valid report object.
