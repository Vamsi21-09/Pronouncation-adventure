"""Application settings and secrets manager."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load any local .env file if present
load_dotenv()


class ConfigurationError(Exception):
    """Raised when critical configuration or secrets are missing or malformed."""
    pass


@dataclass(frozen=True)
class Settings:
    """Immutable application settings container."""
    supabase_url: str
    supabase_anon_key: str
    teacher_override_hash: Optional[str] = None
    pronunciation_pass_threshold: int = 75
    short_word_pass_threshold: int = 90
    star_3_min_accuracy: float = 85.0
    star_3_max_mistakes: int = 0
    star_3_max_skips_overrides: int = 0
    star_2_min_accuracy: float = 70.0
    star_2_max_mistakes: int = 2
    star_2_max_skips_overrides: int = 1

    def is_configured(self) -> bool:
        """Check if Supabase credentials are placeholder or empty."""
        if not self.supabase_url or not self.supabase_anon_key:
            return False
        url_lower = self.supabase_url.lower()
        key_lower = self.supabase_anon_key.lower()
        if "your-project-id" in url_lower or "your-anon-key" in key_lower:
            return False
        if "placeholder" in url_lower or "placeholder" in key_lower:
            return False
        return True


def get_settings() -> Settings:
    """
    Retrieve application settings from Streamlit secrets or environment variables.
    Always reads current values to support hot-reloading when secrets.toml is edited.
    
    Raises:
        ConfigurationError: If SUPABASE_URL or SUPABASE_ANON_KEY are missing.
    """
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    teacher_override_hash: Optional[str] = None

    pronunciation_pass_threshold = 75
    short_word_pass_threshold = 90
    star_3_min_accuracy = 85.0
    star_3_max_mistakes = 0
    star_3_max_skips_overrides = 0
    star_2_min_accuracy = 70.0
    star_2_max_mistakes = 2
    star_2_max_skips_overrides = 1

    # 1. Attempt reading from Streamlit secrets (if Streamlit is running)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                supabase_url = str(st.secrets["SUPABASE_URL"])
            if "SUPABASE_ANON_KEY" in st.secrets:
                supabase_anon_key = str(st.secrets["SUPABASE_ANON_KEY"])
            if "TEACHER_OVERRIDE_HASH" in st.secrets:
                teacher_override_hash = str(st.secrets["TEACHER_OVERRIDE_HASH"])
            if "PRONUNCIATION_PASS_THRESHOLD" in st.secrets:
                pronunciation_pass_threshold = int(st.secrets["PRONUNCIATION_PASS_THRESHOLD"])
            if "SHORT_WORD_PASS_THRESHOLD" in st.secrets:
                short_word_pass_threshold = int(st.secrets["SHORT_WORD_PASS_THRESHOLD"])
            if "STAR_3_MIN_ACCURACY" in st.secrets:
                star_3_min_accuracy = float(st.secrets["STAR_3_MIN_ACCURACY"])
            if "STAR_2_MIN_ACCURACY" in st.secrets:
                star_2_min_accuracy = float(st.secrets["STAR_2_MIN_ACCURACY"])
    except Exception:
        pass

    # 2. Fall back to environment variables / .env
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_anon_key:
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if not teacher_override_hash:
        teacher_override_hash = os.getenv("TEACHER_OVERRIDE_HASH")
    if os.getenv("PRONUNCIATION_PASS_THRESHOLD"):
        try:
            pronunciation_pass_threshold = int(os.getenv("PRONUNCIATION_PASS_THRESHOLD"))
        except ValueError:
            pass
    if os.getenv("SHORT_WORD_PASS_THRESHOLD"):
        try:
            short_word_pass_threshold = int(os.getenv("SHORT_WORD_PASS_THRESHOLD"))
        except ValueError:
            pass
    if os.getenv("STAR_3_MIN_ACCURACY"):
        try:
            star_3_min_accuracy = float(os.getenv("STAR_3_MIN_ACCURACY"))
        except ValueError:
            pass
    if os.getenv("STAR_2_MIN_ACCURACY"):
        try:
            star_2_min_accuracy = float(os.getenv("STAR_2_MIN_ACCURACY"))
        except ValueError:
            pass

    if not supabase_url or not supabase_anon_key:
        missing = []
        if not supabase_url:
            missing.append("SUPABASE_URL")
        if not supabase_anon_key:
            missing.append("SUPABASE_ANON_KEY")
        raise ConfigurationError(
            f"Missing required configuration key(s): {', '.join(missing)}. "
            "Please ensure they are set in .streamlit/secrets.toml or your environment variables."
        )

    return Settings(
        supabase_url=supabase_url.strip(),
        supabase_anon_key=supabase_anon_key.strip(),
        teacher_override_hash=teacher_override_hash.strip() if teacher_override_hash else None,
        pronunciation_pass_threshold=pronunciation_pass_threshold,
        short_word_pass_threshold=short_word_pass_threshold,
        star_3_min_accuracy=star_3_min_accuracy,
        star_3_max_mistakes=star_3_max_mistakes,
        star_3_max_skips_overrides=star_3_max_skips_overrides,
        star_2_min_accuracy=star_2_min_accuracy,
        star_2_max_mistakes=star_2_max_mistakes,
        star_2_max_skips_overrides=star_2_max_skips_overrides,
    )


def reset_settings_cache() -> None:
    """No-op retained for backwards compatibility."""
    pass
