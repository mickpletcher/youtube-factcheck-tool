# Repository Audit

## Snapshot

Date: 2026 05 01

This repository currently has two working implementations for the same fact check workflow:

1. A FastAPI Python application in `python_app`
2. A native PowerShell pipeline in `powershell_app`

Both implementations can produce the same top level report shape:

1. `video`
2. `transcript_source`
3. `claims`
4. `summary`
5. `overall_credibility_score`
6. `report_markdown`

## Current Architecture

### Python

1. `python_app/main.py`
   FastAPI entry point and logging setup
2. `python_app/routes/factcheck.py`
   Pipeline orchestration for metadata, transcript fetch, claim extraction, research, verdict scoring, and report generation
3. `python_app/services/transcript_service.py`
   Video metadata, YouTube captions, and local Whisper fallback
4. `python_app/services/claim_extractor.py`
   OpenAI or heuristic claim extraction
5. `python_app/services/research_service.py`
   DuckDuckGo research
6. `python_app/services/verdict_service.py`
   OpenAI or heuristic verdict scoring
7. `python_app/services/report_generator.py`
   Summary, scoring, and Markdown rendering

### PowerShell

1. `powershell_app/Invoke-YouTubeFactCheck.ps1`
   Script entry point
2. `powershell_app/YouTubeFactCheck.psm1`
   Full native pipeline

## Current Verification Baseline

Validated on 2026 05 01:

1. `py -3.11 -m pytest python_tests -q`
   Result: 67 passed
2. `Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1`
   Result: 6 passed

## Current Strengths

1. Clear repo split between Python and PowerShell
2. Shared report contract across both implementations
3. Real test coverage on both stacks
4. Root README now reflects current layout and commands
5. Config example and ignore rules now exist at the repo root

## Current Gaps

1. No timeout handling around external providers
2. No startup validation for external tools
3. No dedicated contract document beyond the README and audit docs
4. PowerShell and Python transcript fallback use different config names by design and that needs to stay documented
5. No numbered spec workflow existed before this retrofit

## Retrofit Recommendation

Future non trivial work in this repo should use numbered spec packages under `specs/` and keep Python and PowerShell changes aligned when they affect the shared report contract or shared user workflow.
