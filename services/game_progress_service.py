"""Game progress service orchestrating scores, streaks, stars, and level results."""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

from config.settings import get_settings
from repositories.profiles_repo import ProfilesRepository, get_profiles_repository
from repositories.progress_repo import ProgressRepository, get_progress_repository
from repositories.level_results_repo import LevelResultsRepository, get_level_results_repo
from repositories.attempts_repo import AttemptsRepository, get_attempts_repository
from services.scoring_service import award_points
from services.progression_service import ProgressionService, get_progression_service
from services.companion_service import CompanionService, get_companion_service
from services.treasure_service import TreasureService, get_treasure_service
from services.badge_service import BadgeService, get_badge_service
from services.mystery_service import MysteryService, get_mystery_service

logger = logging.getLogger(__name__)

# Process-level thread lock for atomic point/streak mutations
_PROGRESS_LOCK = threading.Lock()


def calculate_stars(accuracy: float, mistakes: int, skipped_resolved_count: int) -> int:
    """
    Pure calculation of 1 to 3 stars based on configurable thresholds in Settings.
    - 3 Stars: High accuracy, 0 mistakes, 0 skips/overrides.
    - 2 Stars: Moderate accuracy, few mistakes/overrides.
    - 1 Star: Completed with lower accuracy or multiple mistakes/overrides.
    Speed does not factor in.
    """
    settings = get_settings()
    acc = float(accuracy)
    m = int(mistakes)
    so = int(skipped_resolved_count)

    # 3 Stars Check
    if (
        acc >= settings.star_3_min_accuracy
        and m <= settings.star_3_max_mistakes
        and so <= settings.star_3_max_skips_overrides
    ):
        return 3

    # 2 Stars Check
    if (
        acc >= settings.star_2_min_accuracy
        and m <= settings.star_2_max_mistakes
        and so <= settings.star_2_max_skips_overrides
    ):
        return 2

    return 1


class GameProgressService:
    """Encapsulates score updates, streak mechanics, star ratings, and level results."""

    def __init__(
        self,
        profiles_repo: Optional[ProfilesRepository] = None,
        progress_repo: Optional[ProgressRepository] = None,
        level_results_repo: Optional[LevelResultsRepository] = None,
        attempts_repo: Optional[AttemptsRepository] = None,
        progression_svc: Optional[ProgressionService] = None,
    ):
        self._profiles_repo = profiles_repo
        self._progress_repo = progress_repo
        self._level_results_repo = level_results_repo
        self._attempts_repo = attempts_repo
        self._progression_svc = progression_svc

    @property
    def profiles_repo(self) -> ProfilesRepository:
        if self._profiles_repo is not None:
            return self._profiles_repo
        return get_profiles_repository()

    @property
    def progress_repo(self) -> ProgressRepository:
        if self._progress_repo is not None:
            return self._progress_repo
        return get_progress_repository()

    @property
    def level_results_repo(self) -> LevelResultsRepository:
        if self._level_results_repo is not None:
            return self._level_results_repo
        return get_level_results_repo()

    @property
    def attempts_repo(self) -> AttemptsRepository:
        if self._attempts_repo is not None:
            return self._attempts_repo
        return get_attempts_repository()

    @property
    def progression_svc(self) -> ProgressionService:
        if self._progression_svc is not None:
            return self._progression_svc
        return get_progression_service()

    def record_word_success(
        self,
        student_id: str,
        word_id: str,
        level_id: str,
        pronunciation_score: int
    ) -> Dict[str, Any]:
        """
        Awards score points, increments streak, checks milestones, and completes the word.
        
        STRICT IDEMPOTENCY & CONCURRENCY GUARD:
        Guarded by _PROGRESS_LOCK and word_progress verification.
        If this word is already 'completed' or 'resolved_by_override' in word_progress,
        does NOT duplicate points or streak increment; returns the current state immediately.
        """
        with _PROGRESS_LOCK:
            # 1. Idempotency check against word_progress table
            existing_word_progress = self.progress_repo.get_level_word_progress(student_id, level_id)
            matching_row = next((r for r in existing_word_progress if r.get("word_id") == word_id), None)

            profile = self.profiles_repo.get_profile(student_id) or {}
            curr_score = profile.get("total_score", 0) or 0
            curr_streak = profile.get("current_streak", 0) or 0
            curr_best = profile.get("best_streak", 0) or 0

            if matching_row and matching_row.get("status") in ("completed", "resolved_by_override"):
                logger.info("Word %s already completed for student %s. Bypassing duplicate award.", word_id, student_id)
                queue_state = self.progression_svc.get_or_init_level_queue(student_id, level_id)
                return {
                    "success": True,
                    "already_completed": True,
                    "points_awarded": 0,
                    "total_score": curr_score,
                    "current_streak": curr_streak,
                    "best_streak": curr_best,
                    "is_milestone": False,
                    "is_level_completed": queue_state["is_level_completed"]
                }

            # 2. Calculate points from pronunciation score
            pts = award_points(pronunciation_score)

            # 3. Advance streak & milestone
            new_streak = curr_streak + 1
            new_best = max(curr_best, new_streak)
            new_score = curr_score + pts
            is_milestone = (new_streak % 3 == 0 and new_streak > 0)

            # 4. Update profile in database
            self.profiles_repo.update_stats(
                user_id=student_id,
                score_delta=pts,
                new_current_streak=new_streak,
                new_best_streak=new_best
            )

            # 5. Mark word completed in progress repository & queue
            comp_res = self.progression_svc.complete_word(student_id, level_id, word_id)

            return {
                "success": True,
                "already_completed": False,
                "points_awarded": pts,
                "total_score": new_score,
                "current_streak": new_streak,
                "best_streak": new_best,
                "is_milestone": is_milestone,
                "is_level_completed": comp_res.get("is_level_completed", False),
                "level_completion": comp_res.get("level_completion")
            }

    def update_streak(self, student_id: str, passed: bool) -> Dict[str, Any]:
        """
        Updates streak:
        - passed=True -> increments current_streak, updates best_streak.
        - passed=False -> resets current_streak to 0 (only called on genuine pronunciation fails).
        Never called on speech/mic errors.
        """
        with _PROGRESS_LOCK:
            profile = self.profiles_repo.get_profile(student_id) or {}
            curr_streak = profile.get("current_streak", 0) or 0
            curr_best = profile.get("best_streak", 0) or 0

            if passed:
                new_streak = curr_streak + 1
                new_best = max(curr_best, new_streak)
                is_milestone = (new_streak % 3 == 0 and new_streak > 0)
                updated = self.profiles_repo.update_stats(
                    user_id=student_id,
                    score_delta=0,
                    new_current_streak=new_streak,
                    new_best_streak=new_best
                )
                return {
                    "current_streak": new_streak,
                    "best_streak": new_best,
                    "is_milestone": is_milestone
                }
            else:
                updated = self.profiles_repo.reset_streak(student_id)
                return {
                    "current_streak": 0,
                    "best_streak": curr_best,
                    "is_milestone": False
                }

    def calculate_stars_for_level(
        self,
        accuracy: float,
        mistakes: int,
        skipped_resolved_count: int
    ) -> int:
        """Calculate stars using the module helper."""
        return calculate_stars(accuracy, mistakes, skipped_resolved_count)

    def complete_level_with_results(self, student_id: str, level_id: str) -> Dict[str, Any]:
        """
        Called only after Phase 3 confirms all required words are completed/resolved.
        Persists level results row to database (idempotent via unique constraint).
        """
        # 1. Idempotency Check: if result already exists, return it with persisted reward data
        existing_result = self.level_results_repo.get_level_result(student_id, level_id)
        if existing_result:
            logger.info("Level result for student %s level %s already exists. Returning persisted record.", student_id, level_id)
            result_payload = dict(existing_result)
            try:
                treasure_svc = get_treasure_service()
                result_payload["treasure"] = treasure_svc.open_treasure(student_id=student_id, level_id=level_id)
                mystery_svc = get_mystery_service()
                result_payload["mystery"] = mystery_svc.maybe_trigger_mystery(student_id=student_id, level_id=level_id)
            except Exception as e:
                logger.warning("Could not attach historical rewards payload: %s", e)
            return result_payload

        # 2. Gather level word progress details
        words_progress = self.progress_repo.get_level_word_progress(student_id, level_id)
        completed_words = sum(1 for w in words_progress if w.get("status") == "completed")
        resolved_words = sum(1 for w in words_progress if w.get("status") == "resolved_by_override")

        # 3. Gather level attempt statistics
        attempts = self.attempts_repo.get_attempts_for_level(student_id, level_id)
        total_attempts = len(attempts)
        passed_attempts = sum(1 for a in attempts if a.get("passed"))
        mistakes = sum(1 for a in attempts if not a.get("passed"))

        if total_attempts > 0:
            accuracy = round((passed_attempts / total_attempts) * 100.0, 2)
            level_score = sum(award_points(a.get("score", 0)) for a in attempts if a.get("passed"))
        else:
            accuracy = 100.0 if completed_words > 0 else 0.0
            level_score = completed_words * 100

        # 4. Get current student streak
        profile = self.profiles_repo.get_profile(student_id) or {}
        streak_at_comp = profile.get("current_streak", 0) or 0

        # 5. Compute stars (overrides count against stars)
        stars = calculate_stars(
            accuracy=accuracy,
            mistakes=mistakes,
            skipped_resolved_count=resolved_words
        )

        # 6. Save level result row (check-first then insert-once with unique constraint catch)
        saved_result = self.level_results_repo.save_level_result(
            student_id=student_id,
            level_id=level_id,
            score=level_score,
            accuracy=accuracy,
            words_completed=completed_words,
            mistakes=mistakes,
            streak_at_completion=streak_at_comp,
            stars=stars
        )

        # 7. Trigger progression level complete (unlocks next level/world in progression cascade)
        self.progression_svc.complete_level(student_id, level_id)

        # 8. Phase 9 Reward Cascade (Idempotent per level result)
        result_payload = dict(saved_result)
        try:
            # 8a. Companion XP Award (Base 50 XP + 25 XP per star)
            companion_svc = get_companion_service()
            xp_amount = 50 + (int(stars) * 25)
            xp_res = companion_svc.add_xp(
                student_id=student_id,
                amount=xp_amount,
                event_key=f"level_result:{level_id}"
            )
            result_payload["companion_xp"] = xp_res

            # 8b. Open Treasure Chest
            treasure_svc = get_treasure_service()
            result_payload["treasure"] = treasure_svc.open_treasure(student_id=student_id, level_id=level_id)

            # 8c. Check & Award Badges
            badge_svc = get_badge_service()
            result_payload["new_badges"] = badge_svc.check_and_award_badges(student_id=student_id)

            # 8d. Maybe Trigger Mystery Surprise
            mystery_svc = get_mystery_service()
            result_payload["mystery"] = mystery_svc.maybe_trigger_mystery(student_id=student_id, level_id=level_id)
            # Invalidate cached companion in UI session state
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    st.session_state.pop("cached_companion", None)
            except Exception:
                pass
        except Exception as e:
            logger.warning("Phase 9 reward cascade error for student %s level %s: %s", student_id, level_id, e)

        return result_payload


def get_game_progress_service() -> GameProgressService:
    """Helper factory for GameProgressService."""
    return GameProgressService()
