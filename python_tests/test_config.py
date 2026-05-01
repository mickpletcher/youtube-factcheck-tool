"""Tests for application settings."""

from python_app.config import Settings


class TestSettings:
    def test_clamps_max_claims_to_hard_limit(self):
        settings = Settings(max_claims=100, _env_file=None)
        assert settings.max_claims == 25

    def test_clamps_max_claims_to_minimum(self):
        settings = Settings(max_claims=0, _env_file=None)
        assert settings.max_claims == 1
