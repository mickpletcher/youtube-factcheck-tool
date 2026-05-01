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
4. Added `futureiupgrades.md` with tiered upgrade ideas for immediate, medium term, and longer term work.
5. Expanded `README.md` into a detailed usage guide for Python and PowerShell.

### Validation

1. Installed the Python dependencies from `requirements.txt`.
2. Ran the Python test suite with `py -3.11 -m pytest python_tests -q`.
3. Confirmed the current result is `67 passed`.
4. Ran `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1`.
5. Confirmed the current PowerShell test result is `6 passed`.
6. Ran `.\powershell_app\Invoke-YouTubeFactCheck.ps1` against a live YouTube URL and confirmed the command returns a valid report object.
