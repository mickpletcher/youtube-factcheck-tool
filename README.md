# YouTube Fact Check Tool

This repo checks a YouTube video, pulls metadata, gets a transcript, extracts factual claims, researches those claims, scores credibility, and returns a JSON report plus a Markdown report.

The repo contains two implementations:

1. A Python API in `python_app`
2. A native PowerShell pipeline in `powershell_app`

## Project Docs

1. [CHANGELOG.md](CHANGELOG.md)
2. [PROJECT_SCAN.md](PROJECT_SCAN.md)
3. [CONTRACT.md](CONTRACT.md)
4. [future-upgrades.md](future-upgrades.md)
5. [docs/repo-audit.md](docs/repo-audit.md)
6. [specs/001-dual-stack-factcheck-foundation/spec.md](specs/001-dual-stack-factcheck-foundation/spec.md)

## Repo Layout

```text
python_app/
python_tests/
powershell_app/
powershell_tests/
.env.example
.gitignore
requirements.txt
README.md
CHANGELOG.md
PROJECT_SCAN.md
CONTRACT.md
future-upgrades.md
docs/
specs/
```

## What The Tool Does

1. Accepts a YouTube URL
2. Pulls video metadata
3. Tries YouTube captions first
4. Falls back to transcription when captions are not available
5. Extracts factual claims
6. Searches for evidence
7. Scores each claim
8. Builds JSON and Markdown output

## Development Workflow

Use the repo spec workflow for non trivial changes:

1. Create the next numbered folder under `specs/`
2. Write `requirements.md`
3. Write `spec.md`
4. Write `plan.md`
5. Write `tasks.md`
6. Implement the change
7. Audit the result
8. Run regression checks

The baseline retrofit package for this repo is:

1. [specs/001-dual-stack-factcheck-foundation/requirements.md](specs/001-dual-stack-factcheck-foundation/requirements.md)
2. [specs/001-dual-stack-factcheck-foundation/spec.md](specs/001-dual-stack-factcheck-foundation/spec.md)
3. [specs/001-dual-stack-factcheck-foundation/plan.md](specs/001-dual-stack-factcheck-foundation/plan.md)
4. [specs/001-dual-stack-factcheck-foundation/tasks.md](specs/001-dual-stack-factcheck-foundation/tasks.md)

Reusable Copilot prompts live in `.github/prompts/`.

## Requirements

### Shared

1. Windows PowerShell
2. Python 3.11 or newer
3. Internet access

### External tools used by the PowerShell pipeline

1. `yt-dlp`
2. `ffmpeg`

The Python API can also use `yt-dlp` and Whisper on the fallback transcript path.

Both runtime entry points now validate `yt-dlp` and `ffmpeg` at startup and fail early if either tool is missing from `PATH`.

### OpenAI

`OPENAI_API_KEY` is optional.

If it is missing:

1. Python falls back to heuristic claim extraction and verdict scoring
2. PowerShell falls back to heuristic claim extraction and verdict scoring
3. PowerShell cannot use OpenAI audio transcription fallback

## Configuration

Copy the example file first:

```powershell
Copy-Item .env.example .env
```

Current example file:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=60
WHISPER_MODEL=base
OPENAI_TRANSCRIPTION_MODEL=whisper-1
YT_DLP_TIMEOUT_SECONDS=60
DUCKDUCKGO_TIMEOUT_SECONDS=20
MAX_CLAIMS=10
RESEARCH_MAX_RESULTS=5
```

Settings are used like this:

1. `OPENAI_API_KEY`
   Used by both implementations for claim extraction and verdict scoring
2. `OPENAI_MODEL`
   Used by both implementations for chat completions
3. `WHISPER_MODEL`
   Used by the Python implementation for local Whisper fallback
4. `OPENAI_TRANSCRIPTION_MODEL`
   Used by the PowerShell implementation for OpenAI audio transcription fallback
5. `OPENAI_TIMEOUT_SECONDS`
   Used by both implementations for OpenAI request timeouts
6. `YT_DLP_TIMEOUT_SECONDS`
   Used by both implementations for `yt-dlp` request and process timeouts
7. `DUCKDUCKGO_TIMEOUT_SECONDS`
   Used by both implementations for DuckDuckGo request timeouts
8. `MAX_CLAIMS`
   Shared extraction limit with a hard cap of `25`
9. `RESEARCH_MAX_RESULTS`
   Shared research limit

Request guardrails:

1. URL length is limited to `2048` characters
2. Effective `MAX_CLAIMS` is limited to `25`

## Tutorial 1: Run The Native PowerShell Pipeline

### Step 1: Open PowerShell In The Repo

```powershell
Set-Location "C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\youtube-factcheck-tool"
```

### Step 2: Confirm External Tools

```powershell
Get-Command yt-dlp
Get-Command ffmpeg
```

### Step 3: Create The Environment File

```powershell
Copy-Item .env.example .env
```

Add your values to `.env`.

### Step 4: Run A Fact Check

```powershell
.\powershell_app\Invoke-YouTubeFactCheck.ps1 `
    -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

The script now writes structured progress logs for:

1. Metadata
2. Transcript fetch
3. Claim extraction
4. Research
5. Verdict scoring
6. Report generation

The final object is still written to standard output as JSON.

The native PowerShell path now applies explicit timeouts to `yt-dlp`, DuckDuckGo, and OpenAI calls and falls back cleanly when those provider calls fail.

### Step 5: Save Output Files

```powershell
.\powershell_app\Invoke-YouTubeFactCheck.ps1 `
    -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" `
    -JsonOutputPath ".\factcheck-result.json" `
    -MarkdownOutputPath ".\factcheck-report.md"
```

This creates:

1. `factcheck-result.json`
2. `factcheck-report.md`

### Step 6: Run PowerShell Tests

```powershell
Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1
```

## Tutorial 2: Run The Python API From PowerShell

### Step 1: Create And Activate A Virtual Environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Python Dependencies

```powershell
py -3.11 -m pip install -r requirements.txt
```

### Step 3: Create The Environment File

```powershell
Copy-Item .env.example .env
```

### Step 4: Start The API

```powershell
py -3.11 -m uvicorn python_app.main:app --reload
```

The API now validates `yt-dlp` and `ffmpeg` during startup. If either tool is missing, the server exits with a clear error.

Available endpoints:

1. `http://localhost:8000/health`
2. `http://localhost:8000/docs`
3. `http://localhost:8000/openapi.json`
4. `http://localhost:8000/factcheck`

### Step 5: Call The API From PowerShell

```powershell
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/factcheck" `
    -ContentType "application/json" `
    -Body $body
```

The API now writes structured logs for transcript fetch, claim extraction, research, verdict scoring, and report generation.

The API now applies explicit timeouts to `yt-dlp`, DuckDuckGo, and OpenAI calls and falls back cleanly when those provider calls fail.

### Step 6: Save The API Response To Files

```powershell
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/factcheck" `
    -ContentType "application/json" `
    -Body $body

$result | ConvertTo-Json -Depth 10 | Set-Content .\factcheck-result.json
$result.report_markdown | Set-Content .\factcheck-report.md
```

### Step 7: Run Python Tests

```powershell
py -3.11 -m pytest python_tests -q
```

## Tutorial 3: Call The Python API From Python

Start the API first:

```powershell
py -3.11 -m uvicorn python_app.main:app --reload
```

Then call it from Python:

```python
import json
import requests

payload = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}

response = requests.post(
    "http://localhost:8000/factcheck",
    json=payload,
    timeout=300,
)
response.raise_for_status()

data = response.json()

print(json.dumps(data, indent=2))

with open("factcheck-result.json", "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)

with open("factcheck-report.md", "w", encoding="utf-8") as handle:
    handle.write(data["report_markdown"])
```

## Response Shape

The shared contract for both implementations is defined in [CONTRACT.md](CONTRACT.md).

```json
{
  "video": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Example Title",
    "channel": "Example Channel",
    "published_at": "2024-01-01",
    "duration_seconds": 123,
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  },
  "transcript_source": "youtube_captions",
  "claims": [
    {
      "id": "claim_1",
      "text": "Example factual claim.",
      "verdict": "Supported",
      "confidence": 0.85,
      "explanation": "Why the claim was scored this way.",
      "sources": [
        "https://example.com/source"
      ]
    }
  ],
  "summary": "Overall summary text.",
  "overall_credibility_score": 0.72,
  "report_markdown": "# Fact Check Report\n..."
}
```

## Troubleshooting

### `yt-dlp` is missing

Install `yt-dlp` and make sure it is in `PATH`.

The Python API and the native PowerShell path now fail at startup if it is missing.

### `ffmpeg` is missing

Install `ffmpeg` and make sure it is in `PATH`.

The Python API and the native PowerShell path now fail at startup if it is missing.

### PowerShell returns no claims

Check these first:

1. The transcript may not contain clear factual statements
2. `OPENAI_API_KEY` may be missing
3. The video may not be a good fact check sample

### Python API returns weaker results than expected

Check `.env` and confirm `OPENAI_API_KEY` is set.

### Tests fail after refactoring

Python imports should use `python_app.*`.

Run:

```powershell
py -3.11 -m pytest python_tests -q
Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1
```
