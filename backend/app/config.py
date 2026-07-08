"""Application configuration, loaded from environment / .env file.

Every setting is prefixed with AC_ (Ambient Care) to avoid collisions.
See .env.example for documentation of each value.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    family_passcode: str = "1234"
    jwt_secret: str = "change-me-please-use-a-long-random-string"
    jwt_expire_days: int = 90
    timezone: str = "Asia/Jerusalem"
    message_ttl_hours: int = 24
    # Arabic display font (see renderer._FONTS for the supported names).
    display_font: str = "Cairo"
    # Day-mode background. Keep it very light: on the 1-bit e-ink panel any
    # non-near-white value renders as a grainy dither. A soft warm ivory reads
    # as calm paper on the device and softer than pure white in the browser.
    day_bg: str = "#F4F1EA"
    trmnl_poll_key: str = ""
    database_path: str = "data/ambient_care.db"
    default_message: str = (
        "نحن نحبّك ونفكّر بك دائماً. نتمنّى لك يوماً هادئاً وجميلاً"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AC_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed only once."""
    return Settings()
