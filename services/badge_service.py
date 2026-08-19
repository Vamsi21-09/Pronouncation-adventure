"""Badge achievement evaluation service evaluating student metrics against badge criteria."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from repositories.badges_repo import BadgesRepository, get_badges_repository
from repositories.profiles_repo import ProfilesRepository, get_profiles_repository
from repositories.progress_repo import ProgressRepository, get_progress_repository
from repositories.level_results_repo import LevelResultsRepository, get_level_results_repo

logger = logging.getLogger(__name__)


class BadgeService:
    """Evaluates student progress statistics against badge rules and awards newly unlocked achievements."""

    def __init__(
        self,
        badges_repo: Optional[BadgesRepository] = None,
        profiles_repo: Optional[ProfilesRepository] = None,
        progress_repo: Optional[ProgressRepository] = None,
        level_results_repo: Optional[LevelResultsRepository] = None
    ):
        self._badges_repo = badges_repo
        self._profiles_repo = profiles_repo
        self._progress_repo = progress_repo
        self._level_results_repo = level_results_repo

    @property
    def badges_repo(self) -> BadgesRepository:
        if self._badges_repo is not None:
            return self._badges_repo
        return get_badges_repository()

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

    def check_and_award_badges(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Evaluate student stats against all badge criteria and award unearned badges.
        Returns list of newly awarded badges.
        """
        all_badges = self.badges_repo.get_all_badges()
        if not all_badges:
            return []

        # 1. Fetch student's currently earned badges
        earned_rows = self.badges_repo.get_student_badges(student_id)
        earned_badge_ids = {r.get("badge_id") or (r.get("badges") or {}).get("id") for r in earned_rows}

        # 2. Gather student statistics from existing repositories
        profile = self.profiles_repo.get_profile(student_id) or {}
        best_streak = int(profile.get("best_streak", 0) or 0)
        current_streak = int(profile.get("current_streak", 0) or 0)
        max_streak = max(best_streak, current_streak)

        # Query level results
        results = self.level_results_repo.get_all_student_results(student_id) if hasattr(self.level_results_repo, "get_all_student_results") else []
        if not results:
            try:
                res_data = self.level_results_repo.client.table("level_results").select("*").eq("student_id", student_id).execute().data
                results = res_data or []
            except Exception:
                results = []

        total_words_completed = sum(int(r.get("words_completed", 0)) for r in results)
        has_perfect_score = any(float(r.get("accuracy", 0.0)) >= 100.0 or int(r.get("score", 0)) >= 700 for r in results)
        has_three_star_level = any(int(r.get("stars", 1)) == 3 for r in results)
        has_completed_levels = len(results) > 0

        # Check world completion
        has_completed_world = False
        try:
            w_prog = self.progress_repo.client.table("world_progress").select("*").eq("student_id", student_id).eq("status", "completed").execute()
            has_completed_world = bool(w_prog.data and len(w_prog.data) > 0)
        except Exception:
            pass

        # 3. Evaluate each unearned badge
        newly_awarded: List[Dict[str, Any]] = []

        for badge in all_badges:
            b_id = badge["id"]
            if b_id in earned_badge_ids:
                continue

            b_key = badge.get("key", "")
            crit_type = badge.get("criteria_type", "")
            crit_val = badge.get("criteria_value", 1)

            qualifies = False

            if b_key == "first_words" or crit_type == "first_word":
                qualifies = (total_words_completed >= 1 or has_completed_levels)
            elif b_key == "perfect_pronunciation" or crit_type == "perfect_score":
                qualifies = has_perfect_score
            elif b_key == "words_50":
                qualifies = (total_words_completed >= 50)
            elif b_key == "words_100":
                qualifies = (total_words_completed >= 100)
            elif b_key == "streak_5" or crit_type == "streak":
                qualifies = (max_streak >= crit_val)
            elif b_key == "fast_speaker" or crit_type == "speed":
                qualifies = has_completed_levels
            elif b_key == "word_master" or crit_type == "mastery":
                qualifies = has_three_star_level
            elif b_key == "language_explorer" or crit_type == "world_complete":
                qualifies = has_completed_world

            if qualifies:
                awarded = self.badges_repo.award_badge_to_student(student_id, b_id)
                if awarded:
                    newly_awarded.append(badge)

        return newly_awarded


def get_badge_service() -> BadgeService:
    return BadgeService()
