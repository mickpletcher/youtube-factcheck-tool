# Generate Plan For YouTube Fact Check Tool

Create an execution plan for the target spec package in this repository.

## Planning Rules

1. Build from the approved `requirements.md` and `spec.md`.
2. Prefer additive changes over destructive changes.
3. Group work by coherent implementation slices.
4. Identify exact files and folders likely to change.
5. Include verification steps after each major slice.
6. Separate stable retrofit work from follow up debt that should not be folded into the same change.

## Required Considerations

1. Python dependency changes in `requirements.txt`
2. PowerShell compatibility in `powershell_app`
3. `python_tests` and `powershell_tests` updates or gaps
4. `README.md` and `CHANGELOG.md` updates
5. Shared contract alignment between Python and PowerShell

## Output Format

Write `specs/<NNN-name>/plan.md` with:

1. Objective
2. Assumptions
3. Ordered phases
4. Per phase file touch list
5. Validation steps
6. Rollback or safety notes when applicable
