"""Unit tests for ProgressionService logic."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from services.progression_service import ProgressionService


class TestProgressionService(unittest.TestCase):
    """Test suite for ProgressionService business rules."""

    def setUp(self):
        self.mock_content_repo = MagicMock()
        self.mock_progress_repo = MagicMock()
        self.service = ProgressionService(
            content_repo=self.mock_content_repo,
            progress_repo=self.mock_progress_repo
        )

        # Mock sample worlds
        self.worlds = [
            {"id": "w-1", "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": "w-2", "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ]
        self.mock_content_repo.get_all_worlds.return_value = self.worlds

        # Mock sample levels for World 1
        self.levels_w1 = [
            {"id": "l-1", "world_id": "w-1", "order_index": 1, "difficulty_band": "easy"},
            {"id": "l-2", "world_id": "w-1", "order_index": 2, "difficulty_band": "medium"},
            {"id": "l-3", "world_id": "w-1", "order_index": 3, "difficulty_band": "hard"},
        ]
        self.mock_content_repo.get_levels_for_world.side_effect = lambda wid: self.levels_w1 if wid == "w-1" else [
            {"id": "l-4", "world_id": "w-2", "order_index": 1, "difficulty_band": "easy"},
            {"id": "l-5", "world_id": "w-2", "order_index": 2, "difficulty_band": "medium"},
            {"id": "l-6", "world_id": "w-2", "order_index": 3, "difficulty_band": "hard"},
        ]

    def test_init_student_initial_progress(self):
        self.service.init_student_initial_progress("student-123")
        self.mock_progress_repo.upsert_student_world_progress.assert_called_with(
            student_id="student-123",
            world_id="w-1",
            status="unlocked"
        )
        self.mock_progress_repo.upsert_student_level_progress.assert_called_with(
            student_id="student-123",
            level_id="l-1",
            status="unlocked"
        )

    def test_can_access_level_w1_l1_allowed(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "l-1", "world_id": "w-1", "order_index": 1}]
        )
        self.mock_content_repo.client = mock_client
        self.mock_progress_repo.get_student_world_progress.return_value = {"status": "unlocked"}
        self.mock_progress_repo.get_student_level_progress.return_value = {"status": "unlocked"}

        has_access = self.service.can_access_level("student-123", "l-1")
        self.assertTrue(has_access)

    def test_can_access_level_w1_l2_locked_initially(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "l-2", "world_id": "w-1", "order_index": 2}]
        )
        self.mock_content_repo.client = mock_client
        self.mock_progress_repo.get_student_world_progress.return_value = {"status": "unlocked"}
        # Level 2 is locked and preceding level 1 is NOT completed
        self.mock_progress_repo.get_student_level_progress.side_effect = lambda sid, lid: (
            {"status": "unlocked"} if lid == "l-1" else {"status": "locked"}
        )

        has_access = self.service.can_access_level("student-123", "l-2")
        self.assertFalse(has_access)

    def test_can_access_level_w2_l1_locked_when_world_2_locked(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "l-4", "world_id": "w-2", "order_index": 1}]
        )
        self.mock_content_repo.client = mock_client
        # World 2 is locked
        self.mock_progress_repo.get_student_world_progress.return_value = {"status": "locked"}

        has_access = self.service.can_access_level("student-123", "l-4")
        self.assertFalse(has_access)

    def test_get_or_init_level_queue_initializes_7_words(self):
        mock_words = [
            {"id": f"word-{i}", "text": f"word{i}", "order_index_in_level": i}
            for i in range(1, 8)
        ]
        self.mock_content_repo.get_words_for_level.return_value = mock_words
        self.mock_progress_repo.get_level_word_progress.return_value = []
        self.mock_progress_repo.upsert_word_progress.side_effect = lambda **kwargs: kwargs

        queue_state = self.service.get_or_init_level_queue("student-123", "l-1")
        self.assertEqual(len(queue_state["active_queue"]), 7)
        self.assertFalse(queue_state["is_level_completed"])
        self.assertEqual(self.mock_progress_repo.upsert_word_progress.call_count, 7)

    def test_skip_word_moves_to_back_of_queue(self):
        existing_rows = [
            {"word_id": "word-1", "status": "pending", "attempt_count": 0, "queue_order": 1},
            {"word_id": "word-2", "status": "pending", "attempt_count": 0, "queue_order": 2},
            {"word_id": "word-3", "status": "pending", "attempt_count": 0, "queue_order": 3},
        ]
        self.mock_progress_repo.get_level_word_progress.return_value = existing_rows
        self.mock_content_repo.get_words_for_level.return_value = [
            {"id": f"word-{i}", "text": f"word{i}", "order_index_in_level": i}
            for i in range(1, 4)
        ]

        res = self.service.skip_word("student-123", "l-1", "word-1")
        self.assertTrue(res["success"])
        # Expect new queue order to be max(1,2,3) + 1 = 4
        self.assertEqual(res["new_queue_order"], 4)
        self.mock_progress_repo.upsert_word_progress.assert_called_with(
            student_id="student-123",
            level_id="l-1",
            word_id="word-1",
            status="skipped",
            attempt_count=1,
            queue_order=4
        )

    def test_complete_level_unlocks_next_level_in_same_world(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "l-1", "world_id": "w-1", "order_index": 1}]
        )
        self.mock_content_repo.client = mock_client

        res = self.service.complete_level("student-123", "l-1")
        self.assertTrue(res["next_level_unlocked"])
        self.assertEqual(res["next_level_id"], "l-2")
        self.assertFalse(res["world_completed"])

    def test_complete_level_3_triggers_world_completion_and_unlocks_w2(self):
        mock_client = MagicMock()
        # Level 3 is the last level of World 1
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "l-3", "world_id": "w-1", "order_index": 3}]
        )
        self.mock_content_repo.client = mock_client

        res = self.service.complete_level("student-123", "l-3")
        self.assertTrue(res["world_completed"])
        # Confirms World 2 unlocked
        self.mock_progress_repo.upsert_student_world_progress.assert_called_with(
            student_id="student-123",
            world_id="w-2",
            status="unlocked",
            unlocked_at=unittest.mock.ANY
        )


if __name__ == "__main__":
    unittest.main()
