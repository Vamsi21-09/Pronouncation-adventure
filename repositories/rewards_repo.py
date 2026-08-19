"""Repository for rewards catalog and student owned cosmetic items."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class RewardsRepositoryError(Exception):
    """Base exception for rewards operations."""
    pass


class RewardsRepository:
    """Manages reward items catalog and student inventory in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_all_rewards(self) -> List[Dict[str, Any]]:
        """Fetch all available rewards in catalog."""
        try:
            response = self.client.table("rewards").select("*").execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to query rewards catalog: %s", e)
            raise RewardsRepositoryError(f"Error fetching rewards: {e}") from e

    def get_reward_by_id(self, reward_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific reward by UUID."""
        try:
            response = self.client.table("rewards").select("*").eq("id", reward_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to fetch reward %s: %s", reward_id, e)
            raise RewardsRepositoryError(f"Error fetching reward: {e}") from e

    def get_student_rewards(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch all rewards owned by a student with joined reward details."""
        try:
            response = (
                self.client.table("student_rewards")
                .select("*, rewards(*)")
                .eq("student_id", student_id)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query student rewards for %s: %s", student_id, e)
            raise RewardsRepositoryError(f"Error fetching student rewards: {e}") from e

    def award_reward_to_student(
        self,
        student_id: str,
        reward_id: str,
        source: str = "treasure"
    ) -> Optional[Dict[str, Any]]:
        """Award a reward item to a student. Safe against duplicate inserts."""
        payload = {
            "student_id": student_id,
            "reward_id": reward_id,
            "source": source,
            "equipped": False,
        }
        try:
            response = self.client.table("student_rewards").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                logger.info("Student %s already owns reward %s", student_id, reward_id)
                return None
            logger.error("Failed to award reward %s to student %s: %s", reward_id, student_id, e)
            raise RewardsRepositoryError(f"Error awarding reward: {e}") from e

    def set_reward_equipped(self, student_id: str, reward_id: str, equipped: bool) -> bool:
        """Update equipped status for a student reward."""
        try:
            response = (
                self.client.table("student_rewards")
                .update({"equipped": equipped})
                .eq("student_id", student_id)
                .eq("reward_id", reward_id)
                .execute()
            )
            return bool(response.data and len(response.data) > 0)
        except Exception as e:
            logger.error("Failed to equip reward: %s", e)
            raise RewardsRepositoryError(f"Error updating equipped reward: {e}") from e


def get_rewards_repository() -> RewardsRepository:
    return RewardsRepository()
