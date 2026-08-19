"""Repository for badges catalog and student badge achievements."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class BadgesRepositoryError(Exception):
    """Base exception for badges operations."""
    pass


class BadgesRepository:
    """Manages badges catalog and student achievements in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_all_badges(self) -> List[Dict[str, Any]]:
        """Fetch all badges in the catalog."""
        try:
            response = self.client.table("badges").select("*").execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to query badges catalog: %s", e)
            raise BadgesRepositoryError(f"Error fetching badges: {e}") from e

    def get_student_badges(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch all badges earned by a student with joined badge details."""
        try:
            response = (
                self.client.table("student_badges")
                .select("*, badges(*)")
                .eq("student_id", student_id)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query student badges for %s: %s", student_id, e)
            raise BadgesRepositoryError(f"Error fetching student badges: {e}") from e

    def award_badge_to_student(self, student_id: str, badge_id: str) -> Optional[Dict[str, Any]]:
        """Award a badge to a student. Safe against duplicate inserts."""
        payload = {
            "student_id": student_id,
            "badge_id": badge_id,
        }
        try:
            response = self.client.table("student_badges").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                logger.info("Badge %s already earned by student %s", badge_id, student_id)
                return None
            logger.error("Failed to award badge %s to student %s: %s", badge_id, student_id, e)
            raise BadgesRepositoryError(f"Error awarding badge: {e}") from e


def get_badges_repository() -> BadgesRepository:
    return BadgesRepository()
