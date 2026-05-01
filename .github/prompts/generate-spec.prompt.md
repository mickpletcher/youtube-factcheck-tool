# Generate Spec For YouTube Fact Check Tool

Use the approved requirements document in the target `specs/<NNN-name>/` folder to produce a technical specification for this repository.

## Repository Context

1. Python and PowerShell are both first class stacks.
2. `python_app` contains the FastAPI implementation.
3. `powershell_app` contains the native PowerShell implementation.
4. `python_tests` and `powershell_tests` are the current automated test surfaces.

## Instructions

1. Read the relevant `requirements.md` and inspect the affected code.
2. Describe the current architecture that the change must fit into.
3. Define concrete implementation boundaries by file or module area.
4. Specify data flow, interfaces, command surfaces, and documentation changes.
5. Include validation expectations for Python and PowerShell where relevant.
6. Explicitly list risks if the change affects transcript acquisition, LLM calls, research, scoring, or shared report shape.

## Output Format

Write `specs/<NNN-name>/spec.md` with:

1. Scope
2. Baseline architecture
3. Proposed design
4. Impacted files or folders
5. Data and control flow
6. Testing and verification strategy
7. Rollout or compatibility notes
8. Out of scope items
