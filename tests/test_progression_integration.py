"""End-to-end integration test simulating student level progression, skip/retry, authorized override, and world unlocking."""
from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock
from pathlib import Path

from services.progression_service import ProgressionService
from services.override_service import OverrideService
from repositories.content_repo import ContentRepository
from repositories.progress_repo import ProgressRepository
from scripts.validate_content import DEFAULT_CONTENT_PATH


class TestProgressionFullWorkflow(unittest.TestCase):
    """Simulates a student advancing through World 1 Levels 1-3 to unlock World 2."""

    def setUp(self):
        # In-memory storage simulating Supabase database
        self.db_student_progress: dict[tuple[str, str], dict] = {}
        self.db_world_progress: dict[tuple[str, str], dict] = {}
        self.db_word_progress: dict[tuple[str, str, str], dict] = {}
        self.db_audit_log: list[dict] = []

        # Load real 42-word curriculum dataset for realistic world/level IDs
        with open(DEFAULT_CONTENT_PATH, "r", encoding="utf-8") as f:
            self.curriculum = json.load(f)

        self.mock_client = MagicMock()

        # Build mock table query responses for content and progress
        self.worlds_data = [
            {"id": "w-1", "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": "w-2", "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ]
        self.levels_data = [
            {"id": "l-1", "world_id": "w-1", "order_index": 1, "difficulty_band": "easy"},
            {"id": "l-2", "world_id": "w-1", "order_index": 2, "difficulty_band": "medium"},
            {"id": "l-3", "world_id": "w-1", "order_index": 3, "difficulty_band": "hard"},
            {"id": "l-4", "world_id": "w-2", "order_index": 1, "difficulty_band": "easy"},
            {"id": "l-5", "world_id": "w-2", "order_index": 2, "difficulty_band": "medium"},
            {"id": "l-6", "world_id": "w-2", "order_index": 3, "difficulty_band": "hard"},
        ]

        def mock_table(name: str):
            q = MagicMock()
            if name == "worlds":
                q.select.return_value.order.return_value.execute.return_value = MagicMock(data=self.worlds_data)
                def mock_eq(col, val):
                    m = [w for w in self.worlds_data if w.get(col) == val]
                    return MagicMock(execute=MagicMock(return_value=MagicMock(data=m)))
                q.select.return_value.eq = mock_eq

            elif name == "levels":
                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq(col, val):
                        if col == "id":
                            m = [l for l in self.levels_data if l["id"] == val]
                            return MagicMock(execute=MagicMock(return_value=MagicMock(data=m)))
                        elif col == "world_id":
                            m = [l for l in self.levels_data if l["world_id"] == val]
                            return MagicMock(order=MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock(data=m)))))
                        return MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
                    sq.eq = mock_eq
                    return sq
                q.select = mock_select

            elif name == "level_words":
                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq(col, val):
                        # Generate 7 mock words for requested level
                        words_in_lvl = [
                            {
                                "order_index": i,
                                "is_required": True,
                                "words": {
                                    "id": f"word-{val}-{i}",
                                    "text": f"word_{val}_{i}",
                                    "meaning": "Educational meaning",
                                    "pronunciation_hint": "HINT"
                                }
                            }
                            for i in range(1, 8)
                        ]
                        sq2 = MagicMock()
                        sq2.order.return_value.execute.return_value = MagicMock(data=words_in_lvl)
                        sq2.eq.return_value = sq2
                        return sq2
                    sq.eq = mock_eq
                    return sq
                q.select = mock_select

            elif name == "student_progress":
                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq1(c1, v1):
                        sq2 = MagicMock()
                        def mock_eq2(c2, v2):
                            rec = self.db_student_progress.get((v1, v2))
                            return MagicMock(execute=MagicMock(return_value=MagicMock(data=[rec] if rec else [])))
                        sq2.eq = mock_eq2
                        recs = [r for r in self.db_student_progress.values() if r["student_id"] == v1]
                        sq2.execute.return_value = MagicMock(data=recs)
                        return sq2
                    sq.eq = mock_eq1
                    return sq
                def mock_upsert(payload, on_conflict=None):
                    key = (payload["student_id"], payload["level_id"])
                    self.db_student_progress[key] = dict(payload)
                    return MagicMock(execute=MagicMock(return_value=MagicMock(data=[payload])))
                q.select = mock_select
                q.upsert = mock_upsert

            elif name == "world_progress":
                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq1(c1, v1):
                        sq2 = MagicMock()
                        def mock_eq2(c2, v2):
                            rec = self.db_world_progress.get((v1, v2))
                            return MagicMock(execute=MagicMock(return_value=MagicMock(data=[rec] if rec else [])))
                        sq2.eq = mock_eq2
                        recs = [r for r in self.db_world_progress.values() if r["student_id"] == v1]
                        sq2.execute.return_value = MagicMock(data=recs)
                        return sq2
                    sq.eq = mock_eq1
                    return sq
                def mock_upsert(payload, on_conflict=None):
                    key = (payload["student_id"], payload["world_id"])
                    self.db_world_progress[key] = dict(payload)
                    return MagicMock(execute=MagicMock(return_value=MagicMock(data=[payload])))
                q.select = mock_select
                q.upsert = mock_upsert

            elif name == "word_progress":
                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq1(c1, v1):
                        sq2 = MagicMock()
                        def mock_eq2(c2, v2):
                            matches = [
                                r for r in self.db_word_progress.values()
                                if r["student_id"] == v1 and r["level_id"] == v2
                            ]
                            sq3 = MagicMock()
                            sq3.execute.return_value = MagicMock(data=matches)
                            sq3.order.return_value.execute.return_value = MagicMock(data=matches)
                            return sq3
                        sq2.eq = mock_eq2
                        return sq2
                    sq.eq = mock_eq1
                    return sq
                def mock_upsert(payload, on_conflict=None):
                    key = (payload["student_id"], payload["level_id"], payload["word_id"])
                    self.db_word_progress[key] = dict(payload)
                    return MagicMock(execute=MagicMock(return_value=MagicMock(data=[payload])))
                q.select = mock_select
                q.upsert = mock_upsert

            elif name == "override_audit_log":
                def mock_insert(payload):
                    record = dict(payload, id=f"audit-{len(self.db_audit_log)+1}")
                    self.db_audit_log.append(record)
                    return MagicMock(execute=MagicMock(return_value=MagicMock(data=[record])))
                q.insert = mock_insert

            return q

        self.mock_client.table = mock_table

        self.content_repo = ContentRepository(client=self.mock_client)
        self.progress_repo = ProgressRepository(client=self.mock_client)
        self.progression_svc = ProgressionService(
            content_repo=self.content_repo,
            progress_repo=self.progress_repo
        )
        self.override_svc = OverrideService(
            progress_repo=self.progress_repo,
            progression_service=self.progression_svc
        )

    def test_complete_student_progression_adventure(self):
        student_id = "student-hero-001"

        # 1. Initialize starting progression
        self.progression_svc.init_student_initial_progress(student_id)
        self.assertTrue(self.progression_svc.can_access_level(student_id, "l-1"))
        self.assertFalse(self.progression_svc.can_access_level(student_id, "l-2"))
        self.assertFalse(self.progression_svc.can_access_level(student_id, "l-4"))  # World 2 Level 1

        # 2. Start Level 1 Queue (7 words)
        q1 = self.progression_svc.get_or_init_level_queue(student_id, "l-1")
        self.assertEqual(len(q1["active_queue"]), 7)

        # Complete 6 words
        for i in range(1, 7):
            w_id = f"word-l-1-{i}"
            self.progression_svc.complete_word(student_id, "l-1", w_id)

        # Skip word 7
        skip_res = self.progression_svc.skip_word(student_id, "l-1", "word-l-1-7")
        self.assertEqual(skip_res["status"], "skipped")

        # Verify Level 1 is NOT completed yet because word 7 is skipped
        q1_after_skip = self.progression_svc.get_or_init_level_queue(student_id, "l-1")
        self.assertFalse(q1_after_skip["is_level_completed"])
        self.assertEqual(len(q1_after_skip["active_queue"]), 1)
        self.assertEqual(q1_after_skip["active_queue"][0]["id"], "word-l-1-7")

        # Now complete word 7 -> triggers Level 1 completion and unlocks Level 2
        comp_res = self.progression_svc.complete_word(student_id, "l-1", "word-l-1-7")
        self.assertTrue(comp_res["is_level_completed"])
        self.assertTrue(self.progression_svc.can_access_level(student_id, "l-2"))

        # 3. Play Level 2: Complete 6 words, resolve 1 word with Authorized Override
        q2 = self.progression_svc.get_or_init_level_queue(student_id, "l-2")
        for i in range(1, 7):
            self.progression_svc.complete_word(student_id, "l-2", f"word-l-2-{i}")

        # Teacher authorization for word 7
        is_auth = self.override_svc.authorize_teacher("teacher123")
        self.assertTrue(is_auth)

        # Resolve word with override
        override_res = self.override_svc.resolve_word_with_override(
            student_id=student_id,
            level_id="l-2",
            word_id="word-l-2-7",
            authorizing_user_id="teacher-admin-uuid",
            reason="Microphone input failure"
        )
        self.assertTrue(override_res["is_level_completed"])
        self.assertEqual(len(self.db_audit_log), 1)
        self.assertEqual(self.db_audit_log[0]["word_id"], "word-l-2-7")

        # Confirm Level 3 is now unlocked
        self.assertTrue(self.progression_svc.can_access_level(student_id, "l-3"))

        # 4. Play Level 3 (Final level of World 1)
        q3 = self.progression_svc.get_or_init_level_queue(student_id, "l-3")
        for i in range(1, 8):
            self.progression_svc.complete_word(student_id, "l-3", f"word-l-3-{i}")

        # Verify World 1 completed and World 2 Level 1 is now UNLOCKED!
        self.assertEqual(self.db_world_progress.get((student_id, "w-1"))["status"], "completed")
        self.assertEqual(self.db_world_progress.get((student_id, "w-2"))["status"], "unlocked")
        self.assertTrue(self.progression_svc.can_access_level(student_id, "l-4"))


if __name__ == "__main__":
    unittest.main()
