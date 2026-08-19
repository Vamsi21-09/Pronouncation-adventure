"""Repository for level completion results, accuracy, stars, and summary metrics in Supabase."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class LevelResultsRepositoryError(Exception):
    """Base exception for level_results database operations."""
    pass


class LevelResultsRepository:
    """Encapsulates all database access for the level_results table."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_level_result(self, student_id: str, level_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch level completion result for a student and level.
        
        Args:
            student_id: The UUID of the student.
            level_id: The UUID of the level.
            
        Returns:
            Dict representing the level_result row, or None if not yet completed.
        """
        try:
            response = (
                self.client.table("level_results")
                .select("*")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query level_results for student %s level %s: %s", student_id, level_id, e)
            raise LevelResultsRepositoryError(f"Error fetching level result: {e}") from e

    def get_all_level_results(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all level completion results for a student.
        
        Args:
            student_id: The UUID of the student.
            
        Returns:
            List of level_results rows.
        """
        try:
            response = (
                self.client.table("level_results")
                .select("*")
                .eq("student_id", student_id)
                .order("completed_at", desc=True)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query all level_results for student %s: %s", student_id, e)
            raise LevelResultsRepositoryError(f"Error fetching student level results: {e}") from e

    def save_level_result(
        self,
        student_id: str,
        level_id: str,
        score: int,
        accuracy: float,
        words_completed: int,
        mistakes: int,
        streak_at_completion: int,
        stars: int
    ) -> Dict[str, Any]:
        """
        Idempotently insert or retrieve the level completion result record.
        
        RLS & IMMUTABILITY ARCHITECTURE:
        - Checks for an existing result first and returns it.
        - Uses direct INSERT (never requires UPDATE RLS policies).
        - If a race condition occurs during concurrent requests, catches the unique constraint
          violation on (student_id, level_id) and returns the authoritative persisted record.
        
        Args:
            student_id: The UUID of the student.
            level_id: The UUID of the level.
            score: Accumulated level score.
            accuracy: Overall accuracy percentage (0.0 - 100.0).
            words_completed: Number of successfully pronounced words.
            mistakes: Total attempt mistakes during the level.
            streak_at_completion: Student's streak at the moment of level completion.
            stars: Calculated star rating (1 to 3).
            
        Returns:
            The persisted level_results record.
        """
        # 1. Check if record already exists
        existing = self.get_level_result(student_id, level_id)
        if existing:
            return existing

        clamped_stars = max(1, min(3, int(stars)))
        payload = {
            "student_id": student_id,
            "level_id": level_id,
            "score": int(score),
            "accuracy": round(float(accuracy), 2),
            "words_completed": int(words_completed),
            "mistakes": int(mistakes),
            "streak_at_completion": int(streak_at_completion),
            "stars": clamped_stars,
        }

        # 2. Insert once
        try:
            response = self.client.table("level_results").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            err_str = str(e).lower()
            # If concurrent execution inserted the record between check and insert:
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str or "already exists" in err_str:
                existing_race = self.get_level_result(student_id, level_id)
                if existing_race:
                    return existing_race
            logger.error("Failed to save level result for student %s level %s: %s", student_id, level_id, e)
            raise LevelResultsRepositoryError(f"Error saving level result: {e}") from e


def get_level_results_repository(client: Optional[Client] = None) -> LevelResultsRepository:
    """Helper factory for LevelResultsRepository."""
    return LevelResultsRepository(client=client)


# Convenient alias
get_level_results_repo = get_level_results_repository
