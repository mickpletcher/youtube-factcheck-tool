# Changelog

## 2026-05-01

### Repository structure

1. Split the Python implementation into `python_app` and `python_tests`.
2. Reserved separate folders for the future PowerShell implementation in `powershell_app` and `powershell_tests`.
3. Updated Python imports to use the new `python_app` package path.
4. Updated test mocks and references to match the renamed package paths.

### Documentation

1. Updated `README.md` to reflect the new repo layout.
2. Updated the run and test commands in `README.md` for the `python_app` and `python_tests` structure.
3. Updated `PROJECT_SCAN.md` so it reflects the current package layout and run commands.
4. Added `futureiupgrades.md` with tiered upgrade ideas for immediate, medium term, and longer term work.

### Validation

1. Installed the Python dependencies from `requirements.txt`.
2. Ran the Python test suite with `py -3.11 -m pytest python_tests -q`.
3. Confirmed the current result is `67 passed`.
