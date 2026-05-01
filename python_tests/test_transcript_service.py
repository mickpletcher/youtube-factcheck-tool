"""Tests for the transcript service."""

import pytest
from unittest.mock import patch

from python_app.services.transcript_service import (
    _extract_video_id,
    get_transcript,
    get_video_metadata,
    validate_runtime_dependencies,
)
from python_app.models.schemas import TranscriptSource, VideoMetadata


# ---------------------------------------------------------------------------
# _extract_video_id
# ---------------------------------------------------------------------------


class TestExtractVideoId:
    def test_standard_watch_url(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert _extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert _extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_watch_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxyz"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        assert _extract_video_id("https://m.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            _extract_video_id("https://vimeo.com/123456")

    def test_youtube_url_without_id_raises(self):
        with pytest.raises(ValueError):
            _extract_video_id("https://www.youtube.com/")


# ---------------------------------------------------------------------------
# get_video_metadata – stub fallback
# ---------------------------------------------------------------------------


class TestGetVideoMetadata:
    def test_fallback_returns_video_metadata_on_error(self, mocker):
        """When yt-dlp raises an exception the service returns a stub."""
        mocker.patch(
            "python_app.services.transcript_service._fetch_metadata_yt_dlp",
            side_effect=Exception("network error"),
        )
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_video_metadata(url)
        assert isinstance(result, VideoMetadata)
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.url == url

    def test_returns_yt_dlp_metadata(self, mocker):
        expected = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel="Test Channel",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        mocker.patch(
            "python_app.services.transcript_service._fetch_metadata_yt_dlp",
            return_value=expected,
        )
        result = get_video_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.title == "Test Video"
        assert result.channel == "Test Channel"


# ---------------------------------------------------------------------------
# get_transcript
# ---------------------------------------------------------------------------


class TestGetTranscript:
    def test_returns_youtube_captions_when_available(self, mocker):
        from python_app.models.schemas import TranscriptResult

        caption = TranscriptResult(
            text="Hello world.",
            source=TranscriptSource.youtube_captions,
            language="en",
        )
        mocker.patch(
            "python_app.services.transcript_service._fetch_youtube_captions",
            return_value=caption,
        )
        result = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.source == TranscriptSource.youtube_captions
        assert result.text == "Hello world."

    def test_falls_back_to_audio_transcription(self, mocker):
        from python_app.models.schemas import TranscriptResult

        audio = TranscriptResult(
            text="Audio transcript.",
            source=TranscriptSource.audio_transcription,
            language="en",
        )
        mocker.patch(
            "python_app.services.transcript_service._fetch_youtube_captions",
            return_value=None,
        )
        mocker.patch(
            "python_app.services.transcript_service._transcribe_audio",
            return_value=audio,
        )
        result = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.source == TranscriptSource.audio_transcription

    def test_returns_unavailable_when_both_fail(self, mocker):
        mocker.patch(
            "python_app.services.transcript_service._fetch_youtube_captions",
            return_value=None,
        )
        mocker.patch(
            "python_app.services.transcript_service._transcribe_audio",
            return_value=None,
        )
        result = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.source == TranscriptSource.unavailable
        assert result.text == ""


class TestValidateRuntimeDependencies:
    def test_passes_when_required_tools_exist(self):
        with patch("python_app.services.transcript_service.shutil.which", return_value="C:\\tools\\bin"):
            validate_runtime_dependencies()

    def test_raises_when_required_tool_is_missing(self):
        def fake_which(tool_name):
            if tool_name == "yt-dlp":
                return "C:\\tools\\yt-dlp.exe"
            return None

        with patch("python_app.services.transcript_service.shutil.which", side_effect=fake_which):
            with pytest.raises(RuntimeError, match="ffmpeg"):
                validate_runtime_dependencies()
