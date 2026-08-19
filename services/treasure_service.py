"""Treasure chest service managing level completion rewards and idempotency."""
from __future__ import annotations

import logging
import random
from typing import Any, Dict, Optional
from repositories.rewards_repo import RewardsRepository, get_rewards_repository
from repositories.treasure_repo import TreasureRepository, get_treasure_repository

logger = logging.getLogger(__name__)


class TreasureService:
    """Handles opening level treasure chests and distributing cosmetic rewards."""

    def __init__(
        self,
        rewards_repo: Optional[RewardsRepository] = None,
        treasure_repo: Optional[TreasureRepository] = None
    ):
        self._rewards_repo = rewards_repo
        self._treasure_repo = treasure_repo

    @property
    def rewards_repo(self) -> RewardsRepository:
        if self._rewards_repo is not None:
            return self._rewards_repo
        return get_rewards_repository()

    @property
    def treasure_repo(self) -> TreasureRepository:
        if self._treasure_repo is not None:
            return self._treasure_repo
        return get_treasure_repository()

    def open_treasure(self, student_id: str, level_id: str) -> Dict[str, Any]:
        """
        Open a treasure chest for a completed level.
        Idempotent: A completed level can open only one chest.
        """
        # 1. Check if treasure was already opened for this level
        existing_event = self.treasure_repo.get_treasure_event(student_id, level_id)
        if existing_event:
            return {
                "success": True,
                "already_opened": True,
                "reward": existing_event.get("rewards"),
                "event": existing_event
            }

        # 2. Query available reward catalog
        all_rewards = self.rewards_repo.get_all_rewards()
        if not all_rewards:
            # Fallback if catalog not seeded
            self.treasure_repo.record_treasure_event(student_id, level_id, reward_id=None)
            return {"success": True, "already_opened": False, "reward": None}

        # 3. Query student's owned rewards to prefer unowned items
        owned_rewards = self.rewards_repo.get_student_rewards(student_id)
        owned_ids = {r.get("reward_id") or (r.get("rewards") or {}).get("id") for r in owned_rewards}

        unowned = [r for r in all_rewards if r["id"] not in owned_ids]
        selected_reward = random.choice(unowned) if unowned else random.choice(all_rewards)

        # 4. Award cosmetic item and record treasure event
        self.rewards_repo.award_reward_to_student(student_id, selected_reward["id"], source="treasure")
        event = self.treasure_repo.record_treasure_event(student_id, level_id, selected_reward["id"])

        return {
            "success": True,
            "already_opened": False,
            "reward": selected_reward,
            "event": event
        }


def get_treasure_service() -> TreasureService:
    return TreasureService()
