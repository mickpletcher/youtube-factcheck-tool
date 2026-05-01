# YouTube Fact Check Tool

This project accepts a YouTube URL, extracts video metadata, pulls a transcript, finds factual claims, researches those claims, scores their credibility, and returns a final report in JSON and Markdown.

The current working implementation is in Python.

You can use it in two practical ways today:

1. Run the Python API from PowerShell
2. Run the Python API and call it from Python

The `powershell_app` and `powershell_tests` folders are reserved for a future native PowerShell implementation. They are not the active application yet.

## Project Docs

1. [CHANGELOG.md](CHANGELOG.md)
2. [PROJECT_SCAN.md](PROJECT_SCAN.md)
3. [futureiupgrades.md](futureiupgrades.md)

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
futureiupgrades.md
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

## Tutorial 1: Run The Tool From PowerShell

This is the easiest path on Windows.

### Step 1: Open PowerShell In The Repo

Open PowerShell and change into the repo folder.

```powershell
Set-Location "C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\youtube-factcheck-tool"
```

### Step 2: Create A Virtual Environment

```powershell
py -3.11 -m venv .venv
```

### Step 3: Activate The Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run this in the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 5: Create The Environment File

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

### Step 6: Start The API

```powershell
python -m uvicorn python_app.main:app --reload
```

When the server starts, use:

1. API base URL: `http://localhost:8000`
2. Swagger docs: `http://localhost:8000/docs`
3. OpenAPI JSON: `http://localhost:8000/openapi.json`
4. Health check: `http://localhost:8000/health`

### Step 7: Test The Health Endpoint From PowerShell

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

Expected result:

```json
{
  "status": "ok"
}
```

### Step 8: Submit A YouTube URL From PowerShell

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

### Step 9: Save The Result To Files From PowerShell

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

This gives you:

1. `factcheck-result.json`
2. `factcheck-report.md`

### Step 10: Run The Python Tests From PowerShell

```powershell
py -3.11 -m pytest python_tests -v
```

## Tutorial 2: Use The Tool From Python

This path is useful if you want to script calls, build automation, or integrate the API into another Python project.

### Step 1: Set Up The Environment

You can use the same setup as the PowerShell tutorial:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Then start the API:

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

The active application is the Python package in `python_app`.

### PowerShell

There is not yet a native PowerShell implementation of the fact check pipeline.

Right now, PowerShell support means:

1. You can install dependencies from PowerShell
2. You can run the Python API from PowerShell
3. You can call the API from PowerShell
4. You can save reports from PowerShell

The future native PowerShell implementation will live under `powershell_app`.

## Troubleshooting

### PowerShell Will Not Activate The Virtual Environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### `ffmpeg` Is Missing

If a video has no captions and audio transcription fails, make sure `ffmpeg` is installed and available in `PATH`.

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
