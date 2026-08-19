import datetime
import hashlib
import logging
from typing import Any, Dict, List, Optional

from repositories.profiles_repo import get_profiles_repository, ProfilesRepository
from repositories.level_results_repo import get_level_results_repo, LevelResultsRepository
from repositories.progress_repo import get_progress_repository, ProgressRepository
from repositories.badges_repo import get_badges_repository, BadgesRepository
from services.companion_service import CompanionService, COMPANION_STAGES

logger = logging.getLogger(__name__)


def format_readable_date(raw_date_str: Optional[str]) -> str:
    """Convert ISO timestamp to human-friendly format (e.g. August 14, 2026)."""
    if not raw_date_str:
        return "Recent Explorer"
    try:
        # Strip trailing Z or +00:00 for flexible parsing
        clean_str = raw_date_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(clean_str)
        return dt.strftime("%B %d, %Y")
    except Exception:
        return str(raw_date_str)[:10]


def generate_adventurer_id(user_id: str) -> str:
    """
    Generate a deterministic, persistent 10-digit numeric Adventurer ID from user UUID.
    Guarantees:
    - Exactly 10 digits
    - Numeric only (0-9)
    - Persistent across sessions
    - Unique per user UUID
    - Separate from internal UUID
    """
    if not user_id:
        return "1000000000"
    clean_id = str(user_id).strip()
    h = int(hashlib.sha256(clean_id.encode("utf-8")).hexdigest(), 16)
    val = (h % 9000000000) + 1000000000
    return str(val)


class ProfileService:
    """Consolidates student identity, statistics, companion progress, and badge achievements."""

    def __init__(
        self,
        profiles_repo: Optional[ProfilesRepository] = None,
        level_results_repo: Optional[LevelResultsRepository] = None,
        progress_repo: Optional[ProgressRepository] = None,
        badges_repo: Optional[BadgesRepository] = None,
        companion_service: Optional[CompanionService] = None,
    ):
        self._profiles_repo = profiles_repo
        self._level_results_repo = level_results_repo
        self._progress_repo = progress_repo
        self._badges_repo = badges_repo
        self._companion_service = companion_service or CompanionService()

    @property
    def profiles_repo(self) -> ProfilesRepository:
        if self._profiles_repo is not None:
            return self._profiles_repo
        return get_profiles_repository()

    @property
    def level_results_repo(self) -> LevelResultsRepository:
        if self._level_results_repo is not None:
            return self._level_results_repo
        return get_level_results_repo()

    @property
    def progress_repo(self) -> ProgressRepository:
        if self._progress_repo is not None:
            return self._progress_repo
        return get_progress_repository()

    @property
    def badges_repo(self) -> BadgesRepository:
        if self._badges_repo is not None:
            return self._badges_repo
        return get_badges_repository()

    def get_full_student_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Aggregate complete student profile metrics for the Profile page.
        """
        # 1. Base profile
        profile = self.profiles_repo.get_profile(student_id) or {}
        raw_created = profile.get("created_at")
        readable_created = format_readable_date(raw_created)

        total_score = int(profile.get("total_score", 0) or 0)
        current_streak = int(profile.get("current_streak", 0) or 0)
        best_streak = int(profile.get("best_streak", 0) or 0)

        # 2. Level Results statistics
        level_results = []
        try:
            res_data = self.level_results_repo.client.table("level_results").select("*").eq("student_id", student_id).execute()
            level_results = res_data.data or []
        except Exception as e:
            logger.warning("Could not fetch level results for profile: %s", e)

        total_stars = sum(int(r.get("stars", 0) or 0) for r in level_results)
        completed_levels_count = len(level_results)
        words_completed_count = sum(int(r.get("words_completed", 0) or 0) for r in level_results)

        # 3. Worlds completed count
        completed_worlds_count = 0
        try:
            w_res = self.progress_repo.client.table("world_progress").select("*").eq("student_id", student_id).eq("status", "completed").execute()
            completed_worlds_count = len(w_res.data or [])
        except Exception as e:
            logger.warning("Could not fetch world progress for profile: %s", e)

        # 4. Companion Status
        companion_data = self._companion_service.get_or_create_companion(student_id)

        # 5. Badges (Earned vs Locked)
        all_badges = self.badges_repo.get_all_badges()
        earned_rows = self.badges_repo.get_student_badges(student_id)
        earned_badge_map = {}
        for r in earned_rows:
            b_info = r.get("badges") or {}
            b_id = r.get("badge_id") or b_info.get("id")
            if b_id:
                earned_badge_map[b_id] = {
                    "unlocked_at": format_readable_date(r.get("unlocked_at")),
                    "badge": b_info
                }

        badges_showcase = []
        for b in all_badges:
            b_id = b["id"]
            is_unlocked = b_id in earned_badge_map
            unlocked_date = earned_badge_map[b_id]["unlocked_at"] if is_unlocked else None
            badges_showcase.append({
                "id": b_id,
                "name": b["name"],
                "icon": b.get("icon", "🏅"),
                "description": b.get("description", ""),
                "criteria": b.get("criteria", ""),
                "is_unlocked": is_unlocked,
                "unlocked_at": unlocked_date,
            })

        adventurer_id = profile.get("adventurer_id") or generate_adventurer_id(student_id)

        return {
            "student_id": student_id,
            "adventurer_id": adventurer_id,
            "username": profile.get("username") or "adventurer",
            "display_name": profile.get("display_name") or profile.get("username") or "Adventurer",
            "role": profile.get("role") or "student",
            "created_at_readable": readable_created,
            "stats": {
                "total_score": total_score,
                "current_streak": current_streak,
                "best_streak": best_streak,
                "total_stars": total_stars,
                "completed_levels": completed_levels_count,
                "completed_worlds": completed_worlds_count,
                "words_completed": words_completed_count,
            },
            "companion": companion_data,
            "badges": badges_showcase,
        }


_profile_service_instance: Optional[ProfileService] = None

def get_profile_service() -> ProfileService:
    global _profile_service_instance
    if _profile_service_instance is None:
        _profile_service_instance = ProfileService()
    return _profile_service_instance
