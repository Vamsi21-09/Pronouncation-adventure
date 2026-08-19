"""Repository for the profiles table in Supabase."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ProfileRepositoryError(Exception):
    """Base exception for profile database operations."""
    pass


class ProfilesRepository:
    """Encapsulates all database access for student/user profiles."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a student profile by user ID.
        
        Args:
            user_id: The UUID of the authenticated user.
            
        Returns:
            Dict representing the profile row, or None if not found.
        """
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get profile for user %s: %s", user_id, e)
            raise ProfileRepositoryError(f"Error fetching profile: {e}") from e

    def get_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Look up a profile by unique username.
        
        Args:
            username: The unique username to query.
            
        Returns:
            Dict representing the profile row, or None if not found.
        """
        try:
            response = self.client.table("profiles").select("*").eq("username", username.strip().lower()).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query profile by username %s: %s", username, e)
            raise ProfileRepositoryError(f"Error querying username: {e}") from e

    def create_profile(
        self,
        user_id: str,
        username: str,
        display_name: Optional[str] = None,
        role: str = "student"
    ) -> Dict[str, Any]:
        """
        Create a new student profile row.
        
        Args:
            user_id: The UUID of the auth.users record.
            username: Unique username.
            display_name: Optional display/nickname.
            role: Profile role ('student', 'teacher', 'admin'). Defaults to 'student'.
            
        Returns:
            The created profile dict.
        """
        clean_username = username.strip().lower()
        payload = {
            "id": user_id,
            "username": clean_username,
            "display_name": display_name.strip() if display_name else clean_username,
            "role": role,
            "total_score": 0,
            "current_streak": 0,
            "best_streak": 0,
        }
        try:
            response = self.client.table("profiles").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            logger.error("Failed to create profile for user %s: %s", user_id, e)
            raise ProfileRepositoryError(f"Error creating profile: {e}") from e

    def update_display_name(self, user_id: str, display_name: str) -> Dict[str, Any]:
        """
        Update the display_name for an authenticated user.
        
        Args:
            user_id: The UUID of the user.
            display_name: The new display name.
            
        Returns:
            The updated profile dict.
        """
        cleaned_name = display_name.strip()
        if not cleaned_name:
            raise ProfileRepositoryError("Display name cannot be empty.")
            
        try:
            response = (
                self.client.table("profiles")
                .update({"display_name": cleaned_name})
                .eq("id", user_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            latest = self.get_profile(user_id)
            if latest:
                return latest
            return {"id": user_id, "display_name": cleaned_name}
        except Exception as e:
            logger.error("Failed to update display_name for user %s: %s", user_id, e)
            raise ProfileRepositoryError(f"Error updating display name: {e}") from e

    def update_stats(
        self,
        user_id: str,
        score_delta: int = 0,
        new_current_streak: Optional[int] = None,
        new_best_streak: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update student total_score and streak metrics.
        
        Args:
            user_id: The student user UUID.
            score_delta: Points to add to existing total_score.
            new_current_streak: If provided, explicitly sets current_streak.
            new_best_streak: If provided, explicitly sets best_streak.
            
        Returns:
            The updated profile record dict.
        """
        try:
            current = self.get_profile(user_id) or {}
            old_score = current.get("total_score", 0) or 0
            old_streak = current.get("current_streak", 0) or 0
            old_best = current.get("best_streak", 0) or 0

            updated_score = max(0, old_score + score_delta)
            updated_streak = old_streak if new_current_streak is None else max(0, new_current_streak)
            updated_best = max(old_best, updated_streak) if new_best_streak is None else max(old_best, new_best_streak)

            payload = {
                "total_score": updated_score,
                "current_streak": updated_streak,
                "best_streak": updated_best,
            }

            response = (
                self.client.table("profiles")
                .update(payload)
                .eq("id", user_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {**current, **payload}
        except Exception as e:
            logger.error("Failed to update stats for student %s: %s", user_id, e)
            raise ProfileRepositoryError(f"Error updating student stats: {e}") from e

    def reset_streak(self, user_id: str) -> Dict[str, Any]:
        """
        Reset student's current_streak to 0 upon a genuine pronunciation failure.
        Preserves best_streak and total_score.
        """
        return self.update_stats(user_id=user_id, score_delta=0, new_current_streak=0)


def get_profiles_repository(client: Optional[Client] = None) -> ProfilesRepository:
    """Helper factory for ProfilesRepository."""
    return ProfilesRepository(client=client)
