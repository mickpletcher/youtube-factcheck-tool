# YouTube Fact Check Tool

This project accepts a YouTube URL, extracts video metadata, pulls a transcript, finds factual claims, researches those claims, scores their credibility, and returns a final report in JSON and Markdown.

The repo now contains two working implementations:

1. A Python API in `python_app`
2. A native PowerShell pipeline in `powershell_app`

## Project Docs

1. [CHANGELOG.md](CHANGELOG.md)
2. [PROJECT_SCAN.md](PROJECT_SCAN.md)

## Current Project Layout

```text
python_app/
python_tests/
powershell_app/
powershell_tests/
requirements.txt
.env.example
README.md
CHANGELOG.md
PROJECT_SCAN.md
```

## What The Tool Does

1. Accepts a YouTube URL.
2. Pulls video metadata.
3. Tries to load YouTube captions first.
4. Falls back to audio transcription when captions are not available.
5. Extracts factual claims from the transcript.
6. Searches for evidence related to each claim.
7. Scores each claim as Supported, Contradicted, Disputed, or Unverified.
8. Returns a final report as structured JSON plus Markdown.

## Requirements

### Required

1. Windows PowerShell or another shell you prefer
2. Python 3.11 or newer
3. Internet access

### Required For Better Results

1. An OpenAI API key

Without `OPENAI_API_KEY`, the app still runs, but claim extraction and verdict scoring fall back to simpler heuristic logic.

### Required For Audio Fallback

1. `ffmpeg`

If a video does not have captions, the app tries to download audio and transcribe it. That fallback path depends on `ffmpeg`.

## Configuration

The app reads settings from `.env`.

Copy the example file first:

```powershell
Copy-Item .env.example .env
```

Then update `.env` with the values you want.

### Available Settings

| Setting | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | No | empty | Enables LLM based claim extraction and verdict scoring |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model used for OpenAI calls |
| `MAX_CLAIMS` | No | `10` | Maximum claims extracted from a video |
| `RESEARCH_MAX_RESULTS` | No | `5` | Search results collected for each claim |
| `WHISPER_MODEL` | No | `base` | Whisper model used for audio transcription fallback |

## Tutorial 1: Run The Native PowerShell Tool

This path runs the PowerShell implementation directly.

### Step 1: Open PowerShell In The Repo

Open PowerShell and change into the repo folder.

```powershell
Set-Location "C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\youtube-factcheck-tool"
```

### Step 2: Install External Tools

The PowerShell implementation expects these tools to be available in `PATH`:

1. `yt-dlp`
2. `ffmpeg`

You can verify them with:

```powershell
Get-Command yt-dlp
Get-Command ffmpeg
```

### Step 3: Create The Environment File

```powershell
Copy-Item .env.example .env
```

Open `.env` and set your values.

At minimum, add your OpenAI key if you want the full LLM path:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
MAX_CLAIMS=10
RESEARCH_MAX_RESULTS=5
WHISPER_MODEL=base
```

### Step 4: Run The PowerShell Fact Check Command

```powershell
.\powershell_app\Invoke-YouTubeFactCheck.ps1 `
    -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This returns JSON to the console.

### Step 5: Save The PowerShell Result To Files

```powershell
.\powershell_app\Invoke-YouTubeFactCheck.ps1 `
    -Url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" `
    -JsonOutputPath ".\factcheck-result.json" `
    -MarkdownOutputPath ".\factcheck-report.md"
```

This gives you:

1. `factcheck-result.json`
2. `factcheck-report.md`

This gives you:

1. `factcheck-result.json`
2. `factcheck-report.md`

### Step 6: Run The PowerShell Tests

```powershell
Invoke-Pester .\powershell_tests\YouTubeFactCheck.Tests.ps1
```

### Step 7: How The PowerShell Flow Works

The PowerShell implementation does this:

1. Gets video metadata with `yt-dlp`
2. Tries to download English subtitles with `yt-dlp`
3. Falls back to OpenAI audio transcription if captions are not available and `OPENAI_API_KEY` is set
4. Extracts claims with OpenAI or a heuristic fallback
5. Searches DuckDuckGo for evidence
6. Scores claims with OpenAI or a heuristic fallback
7. Builds the same report shape used by the Python side

## Tutorial 2: Run The Python API From PowerShell

This path uses the FastAPI implementation.

This path is useful if you want to script calls, build automation, or integrate the API into another Python project.

### Step 1: Set Up The Python Environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### Step 2: Start The Python API

```powershell
python -m uvicorn python_app.main:app --reload
```

When the server starts, use:

1. API base URL: `http://localhost:8000`
2. Swagger docs: `http://localhost:8000/docs`
3. OpenAPI JSON: `http://localhost:8000/openapi.json`
4. Health check: `http://localhost:8000/health`

### Step 3: Test The Health Endpoint

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

### Step 4: Submit A YouTube URL From PowerShell

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

### Step 5: Save The Python API Result To Files

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

### Step 6: Run The Python Tests

```powershell
py -3.11 -m pytest python_tests -v
```

## Tutorial 3: Use The Python API From Python

This path is useful if you want to script calls, build automation, or integrate the API into another Python project.

### Step 1: Start The Python API

```powershell
python -m uvicorn python_app.main:app --reload
```

### Step 2: Call The API From A Python Script

Create a Python script in any location and call the local API.

```python
import json
import requests

url = "http://localhost:8000/factcheck"
payload = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}

response = requests.post(url, json=payload, timeout=300)
response.raise_for_status()

data = response.json()

print(json.dumps(data, indent=2))

with open("factcheck-result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

with open("factcheck-report.md", "w", encoding="utf-8") as f:
    f.write(data["report_markdown"])
```

### Step 3: Run The Python Client Script

```powershell
python .\your_script_name.py
```

### Step 4: Use The Interactive Docs

If you prefer not to write a script yet, open:

`http://localhost:8000/docs`

Then:

1. Open `POST /factcheck`
2. Click `Try it out`
3. Paste a YouTube URL
4. Submit the request
5. Review the response

## Response Shape

The API returns a report object with these main fields:

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

## Current Implementation Notes

### Python

The FastAPI implementation lives in `python_app`.

### PowerShell

The native PowerShell implementation lives in `powershell_app`.

It uses:

1. `yt-dlp` for metadata and subtitles
2. DuckDuckGo HTML results for research
3. OpenAI REST calls for claim extraction and verdict scoring when `OPENAI_API_KEY` is set
4. OpenAI audio transcription for subtitle fallback when captions are missing

## Troubleshooting

### PowerShell Will Not Activate The Virtual Environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### `ffmpeg` Is Missing

If a video has no captions and audio transcription fails, make sure `ffmpeg` is installed and available in `PATH`.

### The PowerShell Tool Returns No Claims

This usually means one of these:

1. The transcript did not contain clear factual statements
2. `OPENAI_API_KEY` is not set, so heuristic claim extraction was used
3. The selected video is not a good fact check sample

### The API Starts But Results Look Weak

Check whether `OPENAI_API_KEY` is set in `.env`.

If it is missing, the app uses heuristic fallback logic for claim extraction and verdict scoring.

### Tests Fail After Renaming Or Refactoring

Run:

```powershell
py -3.11 -m pytest python_tests -v
```

If imports or mocks still point to `app.*`, update them to `python_app.*`.

## Architecture Notes

1. Each service is stateless.
2. The route layer coordinates metadata, transcript, claim extraction, research, verdict scoring, and report generation.
3. The app can still run without OpenAI credentials through fallback logic.
4. Audio transcription only runs when captions are unavailable.
