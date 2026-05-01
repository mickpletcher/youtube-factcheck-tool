"""Transcript service.

Attempts to fetch an existing YouTube caption track first.  If no captions are
available the service downloads the audio with yt-dlp and transcribes it with
OpenAI Whisper (requires ``ffmpeg`` to be installed on the host system).
"""

from __future__ import annotations

import os
import re
import tempfile
from typing import Optional
from urllib.parse import parse_qs, urlparse

from python_app.models.schemas import TranscriptResult, TranscriptSource, VideoMetadata


def _extract_video_id(url: str) -> str:
    """Return the YouTube video ID from a URL.

    Supports the following formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/").split("/")[0]
        if video_id:
            return video_id

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path in ("/watch",):
            qs = parse_qs(parsed.query)
            ids = qs.get("v", [])
            if ids:
                return ids[0]
        # /embed/VIDEO_ID or /shorts/VIDEO_ID
        match = re.match(r"^/(?:embed|shorts|v)/([A-Za-z0-9_-]+)", parsed.path)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def _fetch_metadata_yt_dlp(url: str) -> VideoMetadata:
    """Use yt-dlp to fetch video metadata without downloading media."""
    import yt_dlp  # type: ignore

    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_id = info.get("id", _extract_video_id(url))
    title = info.get("title", "Unknown Title")
    channel = info.get("channel") or info.get("uploader") or "Unknown Channel"
    upload_date: Optional[str] = info.get("upload_date")  # YYYYMMDD or None
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    duration: Optional[int] = info.get("duration")

    return VideoMetadata(
        video_id=video_id,
        title=title,
        channel=channel,
        published_at=upload_date,
        duration_seconds=duration,
        url=url,
    )


def get_video_metadata(url: str) -> VideoMetadata:
    """Return metadata for the YouTube video at *url*.

    Falls back to a minimal stub if yt-dlp is unavailable or the request fails.
    """
    try:
        return _fetch_metadata_yt_dlp(url)
    except Exception:
        video_id = _extract_video_id(url)
        return VideoMetadata(
            video_id=video_id,
            title="Unknown Title",
            channel="Unknown Channel",
            url=url,
        )


def _fetch_youtube_captions(video_id: str) -> Optional[TranscriptResult]:
    """Fetch transcript from YouTube's caption track via youtube-transcript-api.

    Returns ``None`` when no transcript is available for the video.
    """
    try:
        from youtube_transcript_api import (  # type: ignore
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        return None

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Prefer manually-created transcripts, then auto-generated ones
        try:
            transcript = transcript_list.find_manually_created_transcript(
                ["en", "en-US", "en-GB"]
            )
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])

        data = transcript.fetch()
        text = " ".join(entry["text"] for entry in data)
        return TranscriptResult(
            text=text,
            source=TranscriptSource.youtube_captions,
            language=transcript.language_code,
        )
    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception:
        return None


def _transcribe_audio(url: str, whisper_model: str = "base") -> Optional[TranscriptResult]:
    """Download the audio track and transcribe it using OpenAI Whisper.

    Requires ``ffmpeg`` to be installed on the host.  Returns ``None`` if
    transcription fails for any reason.
    """
    try:
        import whisper  # type: ignore
        import yt_dlp  # type: ignore
    except ImportError:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.%(ext)s")
        ydl_opts: dict = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",
                }
            ],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception:
            return None

        mp3_path = os.path.join(tmpdir, "audio.mp3")
        if not os.path.exists(mp3_path):
            # Find any audio file in tmpdir
            files = [f for f in os.listdir(tmpdir) if not f.endswith(".%(ext)s")]
            if not files:
                return None
            mp3_path = os.path.join(tmpdir, files[0])

        try:
            model = whisper.load_model(whisper_model)
            result = model.transcribe(mp3_path)
            text: str = result.get("text", "").strip()
            language: str = result.get("language", "en")
            return TranscriptResult(
                text=text,
                source=TranscriptSource.audio_transcription,
                language=language,
            )
        except Exception:
            return None


def get_transcript(url: str, whisper_model: str = "base") -> TranscriptResult:
    """Return a transcript for the YouTube video at *url*.

    Strategy:
    1. Try to fetch YouTube captions via ``youtube-transcript-api``.
    2. If unavailable, download audio and transcribe with Whisper.
    3. If both fail, return an empty transcript with source ``unavailable``.
    """
    video_id = _extract_video_id(url)

    caption_result = _fetch_youtube_captions(video_id)
    if caption_result is not None:
        return caption_result

    audio_result = _transcribe_audio(url, whisper_model=whisper_model)
    if audio_result is not None:
        return audio_result

    return TranscriptResult(text="", source=TranscriptSource.unavailable)
