"""Repository for mystery surprise events."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class MysteryRepositoryError(Exception):
    """Base exception for mystery events."""
    pass


class MysteryRepository:
    """Manages mystery surprise event records in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_mystery_event(self, student_id: str, level_id: str) -> Optional[Dict[str, Any]]:
        """Fetch existing mystery event for student and level."""
        try:
            response = (
                self.client.table("mystery_events")
                .select("*")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query mystery_event: %s", e)
            raise MysteryRepositoryError(f"Error fetching mystery event: {e}") from e

    def record_mystery_event(self, student_id: str, level_id: str, surprise_key: str) -> Optional[Dict[str, Any]]:
        """Record mystery surprise event with unique constraint."""
        payload = {
            "student_id": student_id,
            "level_id": level_id,
            "surprise_key": surprise_key,
        }
        try:
            response = self.client.table("mystery_events").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                logger.info("Mystery event for level %s already recorded for %s", level_id, student_id)
                return None
            logger.error("Failed to insert mystery event: %s", e)
            raise MysteryRepositoryError(f"Error saving mystery event: {e}") from e


def get_mystery_repository() -> MysteryRepository:
    return MysteryRepository()
