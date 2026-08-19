"""Mystery surprise service managing spontaneous celebration events."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from repositories.mystery_repo import MysteryRepository, get_mystery_repository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MysterySurpriseInfo:
    key: str
    name: str
    icon: str
    message: str


MYSTERY_SURPRISES: List[MysterySurpriseInfo] = [
    MysterySurpriseInfo("dancing_penguin", "Dancing Penguin", "🐧", "A cheerful penguin waddles in and does a tap dance for your speech victory!"),
    MysterySurpriseInfo("robot", "Robo-Beep", "🤖", "A friendly little robot beeps with joy at your pronunciation accuracy!"),
    MysterySurpriseInfo("panda", "Rolling Panda", "🐼", "A playful panda rolls across the screen doing happy somersaults!"),
    MysterySurpriseInfo("fireworks", "Grand Fireworks", "🎆", "A brilliant cascade of magical fireworks lights up the sky!"),
    MysterySurpriseInfo("alien", "Cosmic Starfarer", "👽", "A curious little space traveler beams down a glowing cosmic wave!"),
    MysterySurpriseInfo("baby_dragon", "Sparkle Dragon", "🐲", "A tiny baby dragon sneezes adorable golden sparkles in celebration!"),
]

SURPRISE_LOOKUP = {s.key: s for s in MYSTERY_SURPRISES}


class MysteryService:
    """Handles low-probability, delightful surprise events upon level completion."""

    def __init__(self, mystery_repo: Optional[MysteryRepository] = None):
        self._mystery_repo = mystery_repo

    @property
    def mystery_repo(self) -> MysteryRepository:
        if self._mystery_repo is not None:
            return self._mystery_repo
        return get_mystery_repository()

    def maybe_trigger_mystery(
        self,
        student_id: str,
        level_id: str,
        trigger_probability: float = 0.20
    ) -> Optional[Dict[str, Any]]:
        """
        Check or evaluate a mystery surprise event for a completed level.
        Idempotency: At most one mystery event per (student_id, level_id).
        """
        # 1. Check if already triggered
        existing = self.mystery_repo.get_mystery_event(student_id, level_id)
        if existing:
            s_key = existing.get("surprise_key", "dancing_penguin")
            info = SURPRISE_LOOKUP.get(s_key, MYSTERY_SURPRISES[0])
            return {
                "triggered": True,
                "already_triggered": True,
                "surprise_key": s_key,
                "info": info,
                "event": existing
            }

        # 2. Roll random chance (15-20%)
        roll = random.random()
        if roll > trigger_probability:
            return None

        # 3. Pick random surprise
        chosen = random.choice(MYSTERY_SURPRISES)
        event = self.mystery_repo.record_mystery_event(student_id, level_id, chosen.key)

        return {
            "triggered": True,
            "already_triggered": False,
            "surprise_key": chosen.key,
            "info": chosen,
            "event": event
        }


def get_mystery_service() -> MysteryService:
    return MysteryService()
