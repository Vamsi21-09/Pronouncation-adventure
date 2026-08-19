"""Unit and integration tests for Phase 8: Journey Map, World Themes, and World Unlock Transitions."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from config.world_themes import get_world_theme, WORLD_THEMES, DEFAULT_THEME
from services.progression_service import ProgressionService
from repositories.content_repo import ContentRepository
from repositories.progress_repo import ProgressRepository
from repositories.level_results_repo import LevelResultsRepository


class TestPhase8WorldThemesAndJourneyMap(unittest.TestCase):
    """Test suite for world themes, journey map progression, and unlock cascades."""

    def test_world_themes_token_resolution(self):
        """Verify token resolution for known and fallback world themes."""
        # 1. Village Theme
        village_theme = get_world_theme("village")
        self.assertEqual(village_theme.key, "village")
        self.assertEqual(village_theme.icon, "🏡")
        self.assertEqual(village_theme.accent_color, "#38BDF8")
        self.assertIn("Village", village_theme.name)

        # 2. Forest Theme
        forest_theme = get_world_theme("forest")
        self.assertEqual(forest_theme.key, "forest")
        self.assertEqual(forest_theme.icon, "🌲")
        self.assertEqual(forest_theme.accent_color, "#4ADE80")
        self.assertIn("Forest", forest_theme.name)

        # 3. Case Insensitive & Trimmed
        forest_upper = get_world_theme("  FOREST  ")
        self.assertEqual(forest_upper.key, "forest")

        # 4. Fallback for Unknown / None
        fallback_none = get_world_theme(None)
        self.assertEqual(fallback_none.key, DEFAULT_THEME.key)

        fallback_unknown = get_world_theme("nebula_realm")
        self.assertEqual(fallback_unknown.key, DEFAULT_THEME.key)

    def test_journey_map_progression_node_states(self):
        """Verify that world and level node states match Phase 3 rules."""
        mock_content = MagicMock(spec=ContentRepository)
        mock_progress = MagicMock(spec=ProgressRepository)
        service = ProgressionService(content_repo=mock_content, progress_repo=mock_progress)

        student_id = "test-student-888"
        w1_id = "world-1-village"
        w2_id = "world-2-forest"

        w1_l1_id = "w1-l1-easy"
        w1_l2_id = "w1-l2-medium"
        w1_l3_id = "w1-l3-hard"

        mock_content.get_all_worlds.return_value = [
            {"id": w1_id, "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": w2_id, "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ]
        mock_content.get_levels_for_world.side_effect = lambda wid: (
            [
                {"id": w1_l1_id, "world_id": w1_id, "order_index": 1, "difficulty_band": "easy"},
                {"id": w1_l2_id, "world_id": w1_id, "order_index": 2, "difficulty_band": "medium"},
                {"id": w1_l3_id, "world_id": w1_id, "order_index": 3, "difficulty_band": "hard"},
            ] if wid == w1_id else [
                {"id": "w2-l1", "world_id": w2_id, "order_index": 1, "difficulty_band": "easy"},
                {"id": "w2-l2", "world_id": w2_id, "order_index": 2, "difficulty_band": "medium"},
                {"id": "w2-l3", "world_id": w2_id, "order_index": 3, "difficulty_band": "hard"},
            ]
        )

        # Initial state: W1 is unlocked, W2 is locked
        mock_progress.get_student_world_progress.side_effect = lambda sid, wid: (
            {"status": "unlocked"} if wid == w1_id else {"status": "locked"}
        )
        mock_progress.get_student_level_progress.side_effect = lambda sid, lid: (
            {"status": "unlocked"} if lid == w1_l1_id else {"status": "locked"}
        )

        # Verify level access queries for levels
        mock_client = MagicMock()
        mock_content.client = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = lambda: MagicMock(
            data=[{"id": w1_l1_id, "world_id": w1_id, "order_index": 1}]
        )

        self.assertTrue(service.can_access_level(student_id, w1_l1_id))

    def test_world_completion_triggers_world_unlock_transition(self):
        """Completing World 1 Level 3 triggers complete_world and unlocks World 2 & Level 1."""
        mock_content = MagicMock(spec=ContentRepository)
        mock_progress = MagicMock(spec=ProgressRepository)
        service = ProgressionService(content_repo=mock_content, progress_repo=mock_progress)

        student_id = "test-student-999"
        w1_id = "world-1-village"
        w2_id = "world-2-forest"
        w2_l1_id = "w2-l1-easy"

        mock_content.get_all_worlds.return_value = [
            {"id": w1_id, "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": w2_id, "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ]
        mock_content.get_levels_for_world.return_value = [
            {"id": w2_l1_id, "world_id": w2_id, "order_index": 1, "difficulty_band": "easy"}
        ]

        result = service.complete_world(student_id, w1_id)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["next_world_unlocked"])
        self.assertEqual(result["next_world_id"], w2_id)
        self.assertEqual(result["next_world_name"], "Forest")

        # Verify upsert calls to progress repository
        mock_progress.upsert_student_world_progress.assert_any_call(
            student_id=student_id,
            world_id=w1_id,
            status="completed",
            completed_at=unittest.mock.ANY
        )
        mock_progress.upsert_student_world_progress.assert_any_call(
            student_id=student_id,
            world_id=w2_id,
            status="unlocked",
            unlocked_at=unittest.mock.ANY
        )
        mock_progress.upsert_student_level_progress.assert_called_with(
            student_id=student_id,
            level_id=w2_l1_id,
            status="unlocked"
        )


if __name__ == "__main__":
    unittest.main()
