# youtube-factcheck-tool

A Python FastAPI service that accepts a YouTube episode URL, pulls the transcript, extracts factual claims, researches those claims against trusted sources, and generates a credibility report.

## What it does

- Accepts a YouTube video URL
- Pulls video metadata
- Retrieves the transcript when captions exist
- Supports fallback transcription later if no transcript is available
- Extracts objective claims from the transcript
- Fact checks claims against trusted sources
- Generates a JSON response and a Markdown report

## MVP scope

This starter version is intentionally lean. It gives you:

- FastAPI app bootstrap
- `/health` endpoint
- `/analyze` endpoint
- request and response models
- service layer stubs for transcript, claim extraction, research, scoring, and report generation
- modular folder structure for expansion

## Planned workflow

1. Submit a YouTube URL to the API.
2. Extract the video ID and basic metadata.
3. Pull the transcript.
4. Extract factual claims.
5. Research each claim using trusted sources.
6. Score the overall credibility.
7. Return a structured result and a Markdown report.

## Project structure

```text
youtube-factcheck-tool/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── analyze.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube_service.py
│   │   ├── transcript_service.py
│   │   ├── claim_extractor.py
│   │   ├── research_service.py
│   │   ├── verdict_service.py
│   │   └── report_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py
│   │   └── response_models.py
│   └── utils/
│       ├── __init__.py
│       └── url_parser.py
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/mickpletcher/youtube-factcheck-tool.git
cd youtube-factcheck-tool
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### macOS or Linux

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`
- Swagger docs at `http://127.0.0.1:8000/docs`

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "en",
    "max_claims": 10
  }'
```

## Example response shape

```json
{
  "video": {
    "video_id": "dQw4w9WgXcQ",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "title": "Example Video",
    "channel": "Example Channel",
    "published_at": null
  },
  "transcript": {
    "method": "placeholder",
    "language": "en",
    "reliability": "unknown",
    "text": "..."
  },
  "claims": [],
  "scores": {
    "claim_accuracy": 0,
    "source_quality": 0,
    "transcript_reliability": 0,
    "claim_coverage": 0,
    "overall_validity": 0,
    "final_verdict": "Not yet scored"
  },
  "report": "# Analysis Report\n..."
}
```

## Next build steps

- Wire in YouTube Data API metadata lookup
- Add `youtube-transcript-api`
- Add `yt-dlp` subtitle fallback
- Add audio transcription fallback with Whisper
- Add real claim extraction using an LLM or NLP pipeline
- Add trusted-source research and citation ranking
- Add persistence with SQLite or Postgres
- Add background jobs for long-running analyses

## Security notes

- Do not hardcode API keys
- Store secrets in environment variables or a `.env` file that is ignored by Git
- Treat transcript libraries as brittle because unofficial YouTube access can break
- Keep a source audit trail for every verdict

## License

This starter scaffold is ready for Apache 2.0 or MIT. If you selected Apache 2.0 during repo creation, GitHub will add it automatically.
