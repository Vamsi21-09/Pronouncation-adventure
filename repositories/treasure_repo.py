"""Repository for level treasure chest events."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class TreasureRepositoryError(Exception):
    """Base exception for treasure operations."""
    pass


class TreasureRepository:
    """Manages level treasure chest event logs in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_treasure_event(self, student_id: str, level_id: str) -> Optional[Dict[str, Any]]:
        """Fetch existing treasure event for student and level."""
        try:
            response = (
                self.client.table("treasure_events")
                .select("*, rewards(*)")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query treasure_event for %s level %s: %s", student_id, level_id, e)
            raise TreasureRepositoryError(f"Error fetching treasure event: {e}") from e

    def record_treasure_event(
        self,
        student_id: str,
        level_id: str,
        reward_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Record a opened treasure event with persistent unique constraint."""
        payload = {
            "student_id": student_id,
            "level_id": level_id,
            "reward_id": reward_id,
        }
        try:
            response = self.client.table("treasure_events").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                logger.info("Treasure for level %s already recorded for %s", level_id, student_id)
                return None
            logger.error("Failed to insert treasure event: %s", e)
            raise TreasureRepositoryError(f"Error saving treasure event: {e}") from e


def get_treasure_repository() -> TreasureRepository:
    return TreasureRepository()
