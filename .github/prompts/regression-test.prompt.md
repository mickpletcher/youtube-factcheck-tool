# Run Regression Tests For YouTube Fact Check Tool

Run regression checks for the affected areas of this repository after implementation work.

## Instructions

1. Use the target spec package to identify affected runtime surfaces.
2. Run Python tests when Python code or shared docs or config changed.
3. Run PowerShell tests when PowerShell code or shared docs or config changed.
4. Add targeted smoke checks when the change affects commands, entry points, or file outputs.
5. Report exact commands and exact results.

## Default Commands

```powershell
py -3.11 -m pytest python_tests -q
Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1
```

## Output Format

Summarize:

1. Commands run
2. Results
3. Failures or warnings
4. Follow up work if something could not be validated
