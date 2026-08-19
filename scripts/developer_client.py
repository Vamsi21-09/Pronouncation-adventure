"""Privileged Supabase client factory strictly for offline developer utilities and database seeding.

SECURITY NOTICE:
- The Service Role Key bypasses all Row-Level Security (RLS) policies.
- This module and its client MUST NEVER be imported or referenced by runtime application code
  (app.py, pages/, services/, or standard runtime repositories).
- It is strictly restricted to offline maintenance scripts (scripts/seed_content.py).
"""
from __future__ import annotations

import os
from typing import Optional
from pathlib import Path
from supabase import create_client, Client
from config.settings import get_settings, ConfigurationError

# Prefer Python standard library tomllib (Python 3.11+), fallback to toml
try:
    import tomllib
except ImportError:
    import toml as tomllib  # type: ignore


class PrivilegedConfigurationError(Exception):
    """Raised when developer-only privileged credentials are missing or invalid."""
    pass


def _read_toml_file(file_path: Path) -> dict:
    """Safely parse TOML file with tomllib or toml."""
    if not file_path.exists():
        return {}
    try:
        if hasattr(tomllib, "loads"):
            # tomllib.loads accepts str or bytes
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        elif hasattr(tomllib, "load"):
            return tomllib.load(str(file_path))
    except Exception:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import toml
                return toml.load(f)
        except Exception:
            pass
    return {}


def get_service_role_key() -> Optional[str]:
    """
    Safely retrieve the developer-only privileged key from environment
    variables or local .streamlit/secrets.toml.
    Supports SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET_KEY, and common aliases.
    Never exposes or logs the actual credential.
    """
    key_aliases = [
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "SERVICE_ROLE_KEY",
        "SUPABASE_SERVICE_KEY",
    ]

    # 1. Check environment variables
    for alias in key_aliases:
        env_val = os.getenv(alias)
        if env_val and env_val.strip() and not env_val.strip().lower().startswith("your-"):
            return env_val.strip()

    # 2. Check Streamlit runtime secrets (if active)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for alias in key_aliases:
                if alias in st.secrets:
                    val = str(st.secrets[alias]).strip()
                    if val and not val.lower().startswith("your-"):
                        return val
    except Exception:
        pass

    # 3. Check local secrets file paths
    candidate_paths = [
        Path(".streamlit/secrets.toml"),
        Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml",
    ]

    for p in candidate_paths:
        data = _read_toml_file(p)
        for alias in key_aliases:
            if alias in data:
                val = str(data[alias]).strip()
                if val and not val.lower().startswith("your-"):
                    return val

    return None


def get_privileged_supabase_client() -> Client:
    """
    Instantiate an isolated, un-cached Supabase Client authenticated with the service role key.
    Bypasses RLS specifically for curriculum data seeding.
    
    Raises:
        PrivilegedConfigurationError: If privileged service role key is not configured.
    """
    settings = get_settings()
    service_role_key = get_service_role_key()

    if not service_role_key:
        raise PrivilegedConfigurationError(
            "SUPABASE_SERVICE_ROLE_KEY is missing. "
            "To seed curriculum content into RLS-protected tables (worlds, levels, words, level_words), "
            "please set SUPABASE_SERVICE_ROLE_KEY in your local .streamlit/secrets.toml or as an environment variable."
        )

    # Instantiate independent standalone client without persisting user auth state
    return create_client(settings.supabase_url, service_role_key)
