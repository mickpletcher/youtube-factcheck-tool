# Future Upgrades

This file tracks practical next steps for the project based on the current Python and PowerShell implementations.

## Tier 1

Do these first. They close obvious gaps and reduce setup friction.

1. Add explicit timeout and error handling for OpenAI calls, DuckDuckGo calls, and `yt-dlp` work.
2. Add a basic request size and claim count guard so a single request cannot trigger excessive work.
3. Add a repo level contract document that defines the shared request and response shape for Python and PowerShell.

## Tier 2

Do these after the basics are stable. They improve performance, test coverage, and deployment readiness.

1. Expand `powershell_tests` to cover live subtitle parsing, OpenAI response parsing, and file output behavior.
2. Bring the PowerShell report formatting closer to the Python report output so cross comparison is easier.
3. Convert the Python research and verdict stages to run concurrently where it is safe to do so.
4. Cache Whisper model loading so audio fallback does not reload the model on every request.
5. Add integration tests that exercise the full API with mocked external providers.
6. Add a `pyproject.toml` or `pytest.ini` so test behavior and tooling are explicit.
7. Add a `Dockerfile` for the Python API with documented runtime requirements.
8. Add response metadata for timing, provider path used, and partial failure details.
9. Add an option to persist JSON and Markdown reports to disk for later review.

## Tier 3

Do these once the core service is reliable and the dual implementation direction is clear.

1. Add a PowerShell hosted API layer with parity to the Python request and response contract.
2. Add a side by side comparison harness that runs the same input through Python and PowerShell and highlights output differences.
3. Add pluggable research providers so DuckDuckGo is not the only evidence source.
4. Add source quality scoring so authoritative domains carry more weight than generic web results.
5. Add a queue based or background job mode for long running fact checks.
6. Add authentication, rate limiting, and usage tracking for production deployment.
7. Add a simple web UI for submitting videos and reading saved reports.
8. Add export targets for markdown files, JSON archives, and downstream automation tools.
9. Add claim review workflows that let a human override or annotate verdicts before final publishing.
