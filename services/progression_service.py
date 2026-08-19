"""Progression service managing level locks, word queues, skip/retry reordering, and world transitions."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from repositories.content_repo import ContentRepository, get_content_repository
from repositories.progress_repo import ProgressRepository, get_progress_repository

logger = logging.getLogger(__name__)


class ProgressionService:
    """Business logic for student game progression, active word queues, and unlock cascades."""

    def __init__(
        self,
        content_repo: Optional[ContentRepository] = None,
        progress_repo: Optional[ProgressRepository] = None
    ):
        self._content_repo = content_repo
        self._progress_repo = progress_repo

    @property
    def content_repo(self) -> ContentRepository:
        if self._content_repo is not None:
            return self._content_repo
        return get_content_repository()

    @property
    def progress_repo(self) -> ProgressRepository:
        if self._progress_repo is not None:
            return self._progress_repo
        return get_progress_repository()

    def init_student_initial_progress(self, student_id: str) -> None:
        """
        Initialize starting progression for a new student.
        Unlocks World 1 and World 1 Level 1 by default.
        """
        try:
            worlds = self.content_repo.get_all_worlds()
            if not worlds:
                return

            world_1 = next((w for w in worlds if w.get("order_index") == 1), worlds[0])
            world_1_id = world_1["id"]

            # Unlock World 1
            self.progress_repo.upsert_student_world_progress(
                student_id=student_id,
                world_id=world_1_id,
                status="unlocked"
            )

            # Unlock World 1 Level 1
            levels_w1 = self.content_repo.get_levels_for_world(world_1_id)
            if levels_w1:
                level_1 = next((l for l in levels_w1 if l.get("order_index") == 1), levels_w1[0])
                self.progress_repo.upsert_student_level_progress(
                    student_id=student_id,
                    level_id=level_1["id"],
                    status="unlocked"
                )
        except Exception as e:
            logger.warning("Error during initial progress seeding for %s: %s", student_id, e)

    def can_access_level(self, student_id: str, level_id: str) -> bool:
        """
        Determine whether a student is authorized to enter and play a level.
        Re-verifies directly against Supabase on every call (never trusts session_state).
        """
        try:
            # 1. Fetch level details from database
            level_resp = self.content_repo.client.table("levels").select("*").eq("id", level_id).execute()
            if not level_resp.data or len(level_resp.data) == 0:
                return False
            level = level_resp.data[0]
            world_id = level["world_id"]
            order_index = level["order_index"]

            # 2. Check world status
            world_prog = self.progress_repo.get_student_world_progress(student_id, world_id)
            world_status = world_prog.get("status") if world_prog else None

            # If student has no record, check if it's World 1
            if not world_status:
                worlds = self.content_repo.get_all_worlds()
                w1 = next((w for w in worlds if w.get("order_index") == 1), None)
                if w1 and w1["id"] == world_id:
                    self.init_student_initial_progress(student_id)
                    world_status = "unlocked"
                else:
                    return False

            if world_status not in ("unlocked", "completed"):
                return False

            # 3. Check level progress record
            level_prog = self.progress_repo.get_student_level_progress(student_id, level_id)
            if level_prog and level_prog.get("status") in ("unlocked", "completed"):
                return True

            # 4. Check if Level 1 of unlocked world
            if order_index == 1 and world_status in ("unlocked", "completed"):
                # Auto-heal level unlock
                self.progress_repo.upsert_student_level_progress(student_id, level_id, "unlocked")
                return True

            # 5. Check if preceding level in same world is completed
            all_levels = self.content_repo.get_levels_for_world(world_id)
            prev_level = next((l for l in all_levels if l.get("order_index") == order_index - 1), None)
            if prev_level:
                prev_prog = self.progress_repo.get_student_level_progress(student_id, prev_level["id"])
                if prev_prog and prev_prog.get("status") == "completed":
                    # Unlock this level
                    self.progress_repo.upsert_student_level_progress(student_id, level_id, "unlocked")
                    return True

            return False
        except Exception as e:
            logger.error("can_access_level failed for student %s level %s: %s", student_id, level_id, e)
            return False

    def get_or_init_level_queue(self, student_id: str, level_id: str) -> Dict[str, Any]:
        """
        Build or retrieve the active 7-word play queue for a level.
        Persists order_index / queue_order so skipped words remain at the back on page refresh.
        
        Returns:
            Dict with:
                - 'active_queue': List of words currently pending or skipped, ordered by queue_order
                - 'completed_words': List of successfully completed words
                - 'resolved_words': List of words resolved by authorized override
                - 'all_words': Complete list of 7 words with current status
                - 'is_level_completed': Boolean indicating whether all words are finished
        """
        # Fetch required words for this level
        required_words = self.content_repo.get_words_for_level(level_id, required_only=True)
        if not required_words:
            return {
                "active_queue": [],
                "completed_words": [],
                "resolved_words": [],
                "all_words": [],
                "is_level_completed": False
            }

        # Fetch existing word_progress rows
        existing_progress = self.progress_repo.get_level_word_progress(student_id, level_id)
        progress_by_word_id = {row["word_id"]: row for row in existing_progress}

        # Initialize missing words with graceful fallback
        for w in required_words:
            w_id = w["id"]
            if w_id not in progress_by_word_id:
                order_pos = w.get("order_index_in_level", 1)
                new_row = {
                    "student_id": student_id,
                    "level_id": level_id,
                    "word_id": w_id,
                    "status": "pending",
                    "attempt_count": 0,
                    "queue_order": order_pos,
                }
                try:
                    db_row = self.progress_repo.upsert_word_progress(
                        student_id=student_id,
                        level_id=level_id,
                        word_id=w_id,
                        status="pending",
                        attempt_count=0,
                        queue_order=order_pos
                    )
                    if db_row:
                        new_row = db_row
                except Exception as e:
                    logger.warning("Could not persist word_progress for word %s: %s (using local fallback)", w_id, e)
                progress_by_word_id[w_id] = new_row

        # Build categorized lists
        active_items: List[Dict[str, Any]] = []
        completed_items: List[Dict[str, Any]] = []
        resolved_items: List[Dict[str, Any]] = []
        all_items: List[Dict[str, Any]] = []

        for w in required_words:
            w_id = w["id"]
            p_row = progress_by_word_id.get(w_id, {})
            merged = dict(w)
            merged["progress_status"] = p_row.get("status", "pending")
            merged["attempt_count"] = p_row.get("attempt_count", 0)
            merged["queue_order"] = p_row.get("queue_order", w.get("order_index_in_level", 1))

            all_items.append(merged)
            status = merged["progress_status"]
            if status == "completed":
                completed_items.append(merged)
            elif status == "resolved_by_override":
                resolved_items.append(merged)
            else:
                active_items.append(merged)

        # Sort active queue by queue_order ascending, then original level position
        active_items.sort(key=lambda item: (item["queue_order"], item.get("order_index_in_level", 1)))

        is_level_completed = (len(active_items) == 0 and len(all_items) == len(required_words))

        return {
            "active_queue": active_items,
            "completed_words": completed_items,
            "resolved_words": resolved_items,
            "all_words": all_items,
            "is_level_completed": is_level_completed
        }

    def complete_word(self, student_id: str, level_id: str, word_id: str) -> Dict[str, Any]:
        """
        Mark a word as completed.
        If all required words for the level are now completed or resolved by override,
        automatically triggers level completion and progression cascade.
        """
        # 1. Update word progress
        existing = self.progress_repo.get_level_word_progress(student_id, level_id)
        current_row = next((r for r in existing if r["word_id"] == word_id), None)
        attempts = (current_row.get("attempt_count", 0) + 1) if current_row else 1
        q_order = current_row.get("queue_order", 1) if current_row else 1

        self.progress_repo.upsert_word_progress(
            student_id=student_id,
            level_id=level_id,
            word_id=word_id,
            status="completed",
            attempt_count=attempts,
            queue_order=q_order
        )

        # 2. Re-evaluate level queue
        queue_state = self.get_or_init_level_queue(student_id, level_id)
        level_completion_result = None

        if queue_state["is_level_completed"]:
            level_completion_result = self.complete_level(student_id, level_id)

        return {
            "success": True,
            "word_id": word_id,
            "status": "completed",
            "is_level_completed": queue_state["is_level_completed"],
            "level_completion": level_completion_result
        }

    def skip_word(self, student_id: str, level_id: str, word_id: str) -> Dict[str, Any]:
        """
        Mark a word as skipped and push it to the back of the active queue.
        Does NOT mark completed. Blocks level completion until attempted successfully.
        """
        existing = self.progress_repo.get_level_word_progress(student_id, level_id)
        current_row = next((r for r in existing if r["word_id"] == word_id), None)
        attempts = (current_row.get("attempt_count", 0) + 1) if current_row else 1

        # Calculate new queue order to place at the back
        max_q_order = max([r.get("queue_order", 1) for r in existing], default=1)
        new_q_order = max_q_order + 1

        self.progress_repo.upsert_word_progress(
            student_id=student_id,
            level_id=level_id,
            word_id=word_id,
            status="skipped",
            attempt_count=attempts,
            queue_order=new_q_order
        )

        queue_state = self.get_or_init_level_queue(student_id, level_id)
        return {
            "success": True,
            "word_id": word_id,
            "status": "skipped",
            "new_queue_order": new_q_order,
            "active_queue": queue_state["active_queue"]
        }

    def complete_level(self, student_id: str, level_id: str) -> Dict[str, Any]:
        """
        Mark a level completed in student_progress.
        Unlocks the next level in the world, or completes the world if this was the last level.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Mark current level completed
        self.progress_repo.upsert_student_level_progress(
            student_id=student_id,
            level_id=level_id,
            status="completed",
            completed_at=now_iso
        )

        # Retrieve level details to find next level
        level_resp = self.content_repo.client.table("levels").select("*").eq("id", level_id).execute()
        if not level_resp.data:
            return {"level_id": level_id, "status": "completed"}

        level = level_resp.data[0]
        world_id = level["world_id"]
        order_index = level["order_index"]

        # Check levels in current world
        world_levels = self.content_repo.get_levels_for_world(world_id)
        next_level = next((l for l in world_levels if l.get("order_index") == order_index + 1), None)

        if next_level:
            # Unlock next level in same world
            self.progress_repo.upsert_student_level_progress(
                student_id=student_id,
                level_id=next_level["id"],
                status="unlocked"
            )
            return {
                "level_id": level_id,
                "status": "completed",
                "next_level_unlocked": True,
                "next_level_id": next_level["id"],
                "world_completed": False
            }
        else:
            # Last level of world -> Complete world and unlock next world
            world_res = self.complete_world(student_id, world_id)
            return {
                "level_id": level_id,
                "status": "completed",
                "next_level_unlocked": False,
                "world_completed": True,
                "world_progression": world_res
            }

    def complete_world(self, student_id: str, world_id: str) -> Dict[str, Any]:
        """
        Mark a world completed in world_progress.
        Unlocks the next world and its Level 1 in a coordinated progression step.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Mark current world completed
        self.progress_repo.upsert_student_world_progress(
            student_id=student_id,
            world_id=world_id,
            status="completed",
            completed_at=now_iso
        )

        # Find current world order_index
        all_worlds = self.content_repo.get_all_worlds()
        current_world = next((w for w in all_worlds if w["id"] == world_id), None)
        if not current_world:
            return {"world_id": world_id, "status": "completed"}

        current_world_order = current_world["order_index"]
        next_world = next((w for w in all_worlds if w.get("order_index") == current_world_order + 1), None)

        if next_world:
            next_world_id = next_world["id"]
            # Unlock next world
            self.progress_repo.upsert_student_world_progress(
                student_id=student_id,
                world_id=next_world_id,
                status="unlocked",
                unlocked_at=now_iso
            )

            # Unlock Level 1 of next world
            next_world_levels = self.content_repo.get_levels_for_world(next_world_id)
            next_lvl_1 = next((l for l in next_world_levels if l.get("order_index") == 1), None)
            if next_lvl_1:
                self.progress_repo.upsert_student_level_progress(
                    student_id=student_id,
                    level_id=next_lvl_1["id"],
                    status="unlocked"
                )

            return {
                "world_id": world_id,
                "status": "completed",
                "next_world_unlocked": True,
                "next_world_id": next_world_id,
                "next_world_name": next_world["name"]
            }

        return {
            "world_id": world_id,
            "status": "completed",
            "next_world_unlocked": False
        }

    def get_student_journey_summary(self, student_id: str) -> Dict[str, Any]:
        """
        Batched single-pass query resolving journey progression across all 7 worlds.
        Replaces N+1 queries with 2 single queries:
        - 1 query to world_progress
        - 1 query to level_results
        Returns world status dictionary, total stars, completed worlds count, active world.
        """
        all_worlds = self.content_repo.get_all_worlds()
        if not all_worlds:
            return {"all_worlds": [], "world_statuses": {}, "total_stars": 0, "completed_worlds": 0, "active_world_id": None}

        # 1. Single query for all world progress for this student
        try:
            world_progress_rows = self.progress_repo.get_all_student_world_progress(student_id)
        except Exception as e:
            logger.warning("Could not fetch world progress for student %s: %s", student_id, e)
            world_progress_rows = []
        world_progress_by_id = {r["world_id"]: r for r in world_progress_rows}

        # 2. Single query for all level results to compute total stars
        try:
            from repositories.level_results_repo import get_level_results_repo
            lvl_results_repo = get_level_results_repo()
            all_results = lvl_results_repo.get_all_level_results(student_id)
            total_stars = sum(int(r.get("stars", 0)) for r in all_results if r.get("stars"))
        except Exception as e:
            logger.warning("Could not fetch level results for student %s: %s", student_id, e)
            total_stars = 0

        world_statuses = {}
        completed_worlds = 0
        active_world_id = None

        for w in all_worlds:
            w_id = w["id"]
            w_order = w.get("order_index", 1)
            row = world_progress_by_id.get(w_id)
            if row:
                status = row.get("status", "locked")
            else:
                # Default World 1 to unlocked if no record
                status = "unlocked" if w_order == 1 else "locked"

            world_statuses[w_id] = status
            if status == "completed":
                completed_worlds += 1
            elif status == "unlocked" and active_world_id is None:
                active_world_id = w_id

        if not active_world_id and all_worlds:
            active_world_id = all_worlds[0]["id"]

        return {
            "all_worlds": all_worlds,
            "world_statuses": world_statuses,
            "total_stars": total_stars,
            "completed_worlds": completed_worlds,
            "active_world_id": active_world_id
        }

    def get_world_progression_summary(self, student_id: str, world_id: str) -> Dict[str, Any]:
        """
        Batched single-pass query for all levels in a specific world.
        Loads ONLY metadata, statuses, and stars without initializing word queues or preloading images.
        """
        levels = self.content_repo.get_levels_for_world(world_id)
        if not levels:
            return {"levels": [], "active_level_id": None, "completed_levels_count": 0, "world_stars": 0, "world_accessible": False}

        # 1. Single query for all student level progress
        try:
            level_prog_rows = self.progress_repo.get_all_student_level_progress(student_id)
        except Exception as e:
            logger.warning("Could not fetch level progress for student %s: %s", student_id, e)
            level_prog_rows = []
        level_prog_by_id = {r["level_id"]: r for r in level_prog_rows}

        # 2. Single query for all level results
        try:
            from repositories.level_results_repo import get_level_results_repo
            lvl_results_repo = get_level_results_repo()
            all_results = lvl_results_repo.get_all_level_results(student_id)
        except Exception as e:
            logger.warning("Could not fetch level results for student %s: %s", student_id, e)
            all_results = []
        results_by_id = {r["level_id"]: r for r in all_results}

        # 3. Check world status
        try:
            world_prog_rows = self.progress_repo.get_all_student_world_progress(student_id)
        except Exception as e:
            logger.warning("Could not fetch world progress for student %s: %s", student_id, e)
            world_prog_rows = []
        world_prog_by_id = {r["world_id"]: r for r in world_prog_rows}
        world_row = world_prog_by_id.get(world_id)
        
        # Check if World 1
        all_worlds = self.content_repo.get_all_worlds()
        is_w1 = any(w["id"] == world_id and w.get("order_index") == 1 for w in all_worlds)
        world_status = world_row.get("status") if world_row else ("unlocked" if is_w1 else "locked")
        world_accessible = world_status in ("unlocked", "completed")

        processed_levels = []
        active_level_id = None
        completed_count = 0
        world_stars = 0

        # Sort levels by order_index
        sorted_levels = sorted(levels, key=lambda l: l.get("order_index", 1))

        for idx, lvl in enumerate(sorted_levels):
            lvl_id = lvl["id"]
            lvl_order = lvl.get("order_index", idx + 1)
            prog_row = level_prog_by_id.get(lvl_id)
            res_row = results_by_id.get(lvl_id)

            status = prog_row.get("status") if prog_row else "locked"
            stars = int(res_row.get("stars", 0)) if res_row and res_row.get("stars") else 0
            world_stars += stars

            is_completed = (status == "completed")
            if is_completed:
                completed_count += 1

            # Determine access
            if not world_accessible:
                is_accessible = False
            elif lvl_order == 1:
                is_accessible = True
            elif is_completed or status == "unlocked":
                is_accessible = True
            elif idx > 0 and processed_levels[idx - 1]["is_completed"]:
                is_accessible = True
            else:
                is_accessible = False

            if is_accessible and not is_completed and active_level_id is None:
                active_level_id = lvl_id

            processed_levels.append({
                "id": lvl_id,
                "world_id": world_id,
                "order_index": lvl_order,
                "difficulty_band": lvl.get("difficulty_band", "easy"),
                "status": "completed" if is_completed else ("unlocked" if is_accessible else "locked"),
                "is_completed": is_completed,
                "is_accessible": is_accessible,
                "stars": stars
            })

        if not active_level_id and processed_levels:
            # If all completed, active level is the last accessible
            accessible_levels = [l for l in processed_levels if l["is_accessible"]]
            if accessible_levels:
                active_level_id = accessible_levels[-1]["id"]

        return {
            "levels": processed_levels,
            "active_level_id": active_level_id,
            "completed_levels_count": completed_count,
            "world_stars": world_stars,
            "world_accessible": world_accessible
        }


def get_progression_service() -> ProgressionService:
    """Helper factory for ProgressionService."""
    return ProgressionService()

