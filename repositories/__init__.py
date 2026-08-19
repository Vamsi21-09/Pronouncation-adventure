"""Repositories module for Pronunciation Adventure."""
from .supabase_client import get_supabase_client
from .profiles_repo import ProfilesRepository, get_profiles_repository
from .content_repo import ContentRepository, get_content_repository
from .progress_repo import ProgressRepository, get_progress_repository
from .attempts_repo import AttemptsRepository, get_attempts_repository

__all__ = [
    "get_supabase_client",
    "ProfilesRepository",
    "get_profiles_repository",
    "ContentRepository",
    "get_content_repository",
    "ProgressRepository",
    "get_progress_repository",
    "AttemptsRepository",
    "get_attempts_repository",
]
