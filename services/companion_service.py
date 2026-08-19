"""Companion evolution service managing XP awards, evolution stages, and reactive dialogue."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from repositories.companion_repo import CompanionRepository, get_companion_repository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompanionStageInfo:
    stage_key: str
    name: str
    icon: str
    description: str
    min_xp: int
    max_xp: Optional[int]


COMPANION_STAGES: List[CompanionStageInfo] = [
    CompanionStageInfo("egg", "Mystic Egg", "🥚", "A glowing egg filled with sound magic.", 0, 99),
    CompanionStageInfo("baby_bird", "Baby Chick", "🐣", "A cheerful hatchling learning its first words!", 100, 299),
    CompanionStageInfo("blue_bird", "Blue Songbird", "🐦", "A melodious bird that chirps with crystal clarity.", 300, 599),
    CompanionStageInfo("eagle", "Sky Eagle", "🦅", "A soaring eagle with razor-sharp speech articulation.", 600, 999),
    CompanionStageInfo("phoenix", "Flame Phoenix", "🔥", "A blazing phoenix rising with pronunciation triumphs.", 1000, 1499),
    CompanionStageInfo("golden_phoenix", "Golden Phoenix", "👑", "The legendary master companion of spoken English!", 1500, None),
]

STAGE_LOOKUP: Dict[str, CompanionStageInfo] = {s.stage_key: s for s in COMPANION_STAGES}


class CompanionService:
    """Business logic for companion evolution, XP progression, and lightweight reactions."""

    def __init__(self, companion_repo: Optional[CompanionRepository] = None):
        self._repo = companion_repo

    @property
    def repo(self) -> CompanionRepository:
        if self._repo is not None:
            return self._repo
        return get_companion_repository()

    @staticmethod
    def calculate_stage(xp: int) -> CompanionStageInfo:
        """Determine companion stage from total cumulative XP."""
        safe_xp = max(0, xp)
        for stage_info in reversed(COMPANION_STAGES):
            if safe_xp >= stage_info.min_xp:
                return stage_info
        return COMPANION_STAGES[0]

    def get_or_create_companion(self, student_id: str) -> Dict[str, Any]:
        """Fetch or initialize student companion with graceful fallback on network/RLS transient errors."""
        row = None
        try:
            row = self.repo.get_companion(student_id)
            if not row:
                row = self.repo.upsert_companion(student_id=student_id, stage="egg", xp=0)
        except Exception as e:
            logger.warning("Could not load companion from database for student %s: %s (using local fallback)", student_id, e)
            row = {"student_id": student_id, "stage": "egg", "xp": 0}

        current_xp = int(row.get("xp", 0))
        current_stage = self.calculate_stage(current_xp)

        # Auto-heal stage if out of sync
        if row.get("stage") != current_stage.stage_key:
            try:
                row = self.repo.upsert_companion(student_id=student_id, stage=current_stage.stage_key, xp=current_xp)
            except Exception as e:
                logger.debug("Could not auto-heal companion stage: %s", e)

        next_stage_info = None
        for s in COMPANION_STAGES:
            if s.min_xp > current_xp:
                next_stage_info = s
                break

        xp_to_next = (next_stage_info.min_xp - current_xp) if next_stage_info else 0
        progress_pct = 100.0 if not next_stage_info else min(
            100.0,
            max(0.0, ((current_xp - current_stage.min_xp) / (next_stage_info.min_xp - current_stage.min_xp)) * 100.0)
        )

        return {
            "student_id": student_id,
            "stage": current_stage.stage_key,
            "xp": current_xp,
            "stage_info": current_stage,
            "next_stage": next_stage_info,
            "xp_to_next": xp_to_next,
            "progress_pct": progress_pct,
        }

    def add_xp(self, student_id: str, amount: int, event_key: str) -> Dict[str, Any]:
        """
        Idempotently award XP to a companion.
        Uses persistent companion_xp_events table to guarantee single execution.
        """
        if amount <= 0:
            current = self.get_or_create_companion(student_id)
            return {"success": True, "already_awarded": True, "xp_awarded": 0, "companion": current, "evolved": False}

        # Check idempotency guard
        if self.repo.has_xp_event(student_id, event_key):
            current = self.get_or_create_companion(student_id)
            return {"success": True, "already_awarded": True, "xp_awarded": 0, "companion": current, "evolved": False}

        # Fetch current companion
        current = self.get_or_create_companion(student_id)
        old_stage = current["stage"]
        new_xp = current["xp"] + amount
        new_stage_info = self.calculate_stage(new_xp)
        evolved = (new_stage_info.stage_key != old_stage)

        # Record XP event first for DB idempotency
        inserted = self.repo.record_xp_event(student_id, event_key, amount)
        if not inserted:
            # Race condition won by another concurrent request
            updated = self.get_or_create_companion(student_id)
            return {"success": True, "already_awarded": True, "xp_awarded": 0, "companion": updated, "evolved": False}

        # Update companion state
        self.repo.upsert_companion(student_id, new_stage_info.stage_key, new_xp)
        updated_companion = self.get_or_create_companion(student_id)

        return {
            "success": True,
            "already_awarded": False,
            "xp_awarded": amount,
            "evolved": evolved,
            "previous_stage": old_stage,
            "companion": updated_companion,
        }

    @staticmethod
    def get_reaction(trigger_type: str, stage_key: str = "egg") -> str:
        """Return lightweight, encouraging companion speech bubbles."""
        icon = STAGE_LOOKUP.get(stage_key, COMPANION_STAGES[0]).icon
        reactions = {
            "success": f"{icon} *\"Chirp! Wonderful sound articulation!\"*",
            "streak_milestone": f"{icon} *\"Whoa! Look at that blazing streak! Keep soaring!\"*",
            "level_complete": f"{icon} *\"Level conquered! We're gaining so much energy!\"*",
            "world_unlock": f"{icon} *\"A whole new realm! I can feel our power growing!\"*",
            "retry": f"{icon} *\"You've got this! Listen closely and try once more!\"*",
        }
        return reactions.get(trigger_type, f"{icon} *\"Ready for adventure!\"*")


def get_companion_service() -> CompanionService:
    return CompanionService()
