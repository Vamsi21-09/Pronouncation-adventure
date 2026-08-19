"""Supabase client factory and provider with robust JWT session propagation."""
from __future__ import annotations

import logging
from typing import Any, Optional
from supabase import create_client, Client
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Fallback for standalone/script environments
_standalone_client: Optional[Client] = None
_standalone_credentials: Optional[tuple[str, str]] = None


def _create_raw_client(url: str, key: str) -> Client:
    """Instantiate a new stateless Supabase client with anon key."""
    return create_client(url, key)


def set_client_auth_token(client: Client, token: Optional[str]) -> None:
    """
    Attach JWT access token (or fallback to anon key) to PostgREST client
    so that PostgreSQL Row Level Security (RLS) policies (auth.uid() = ...) are properly evaluated.
    """
    try:
        settings = get_settings()
        anon_key = settings.supabase_anon_key
        target_token = token.strip() if (token and token.strip()) else anon_key
        auth_header = f"Bearer {target_token}"

        # 1. Update postgrest.auth
        try:
            client.postgrest.auth(target_token)
        except Exception:
            pass

        # 2. Update postgrest.headers
        if hasattr(client.postgrest, "headers"):
            headers = client.postgrest.headers
            for k in list(headers.keys()):
                if k.lower() == "authorization":
                    del headers[k]
            headers["authorization"] = auth_header

        # 3. Update postgrest.session.headers (httpx.Client)
        if hasattr(client.postgrest, "session") and hasattr(client.postgrest.session, "headers"):
            sess_headers = client.postgrest.session.headers
            for k in list(sess_headers.keys()):
                if k.lower() == "authorization":
                    del sess_headers[k]
            sess_headers["authorization"] = auth_header
    except Exception as e:
        logger.debug("Could not set postgrest auth token: %s", e)


def get_supabase_client(token: Optional[str] = None) -> Client:
    """
    Retrieve the shared Supabase client.
    Uses st.cache_resource when inside a Streamlit application with automatic key-based cache invalidation.
    Dynamically applies the active authenticated session's JWT access token to PostgREST.
    """
    settings = get_settings()
    url = settings.supabase_url
    key = settings.supabase_anon_key

    client: Optional[Client] = None

    try:
        import streamlit as st
        # Only use st.cache_resource if we are in an active Streamlit runtime context
        if hasattr(st, "cache_resource"):
            @st.cache_resource(show_spinner=False)
            def _cached_client(_url: str, _key: str) -> Client:
                return _create_raw_client(_url, _key)

            client = _cached_client(url, key)
    except Exception as e:
        logger.debug("Streamlit cache_resource not active; using standalone instance: %s", e)

    if client is None:
        global _standalone_client, _standalone_credentials
        if _standalone_client is None or _standalone_credentials != (url, key):
            _standalone_client = _create_raw_client(url, key)
            _standalone_credentials = (url, key)
        client = _standalone_client

    # Dynamically extract and apply session JWT to PostgREST client
    effective_token: Optional[str] = token

    try:
        import streamlit as st
        if hasattr(st, "session_state"):
            if not effective_token:
                # Check dedicated auth_token string
                raw_auth_token = st.session_state.get("auth_token")
                if raw_auth_token and isinstance(raw_auth_token, str):
                    effective_token = raw_auth_token

            if not effective_token:
                # Check session dict or object
                sess = st.session_state.get("session")
                if sess:
                    if isinstance(sess, dict) and sess.get("access_token"):
                        effective_token = sess["access_token"]
                    elif hasattr(sess, "access_token"):
                        effective_token = getattr(sess, "access_token", None)

            if effective_token:
                set_client_auth_token(client, effective_token)
            elif not st.session_state.get("authenticated"):
                set_client_auth_token(client, None)
        elif effective_token:
            set_client_auth_token(client, effective_token)
    except Exception:
        if effective_token:
            set_client_auth_token(client, effective_token)

    return client


def reset_client_cache() -> None:
    """Reset cached standalone client instance (useful for testing)."""
    global _standalone_client, _standalone_credentials
    _standalone_client = None
    _standalone_credentials = None
