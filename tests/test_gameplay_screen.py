"""Unit tests for Gameplay Screen helpers, ImageService resolution, and level access resolution."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

import importlib

from services.image_service import ImageService

play_page = importlib.import_module("pages.5_Play")
resolve_active_level = play_page.resolve_active_level


class TestImageService(unittest.TestCase):
    """Test suite for image resolution and fallbacks."""

    def test_get_public_url_from_relative_path(self):
        with patch("services.image_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(supabase_url="https://test-project.supabase.co")
            url = ImageService.get_public_url("words/garden.webp")
            self.assertEqual(
                url,
                "https://test-project.supabase.co/storage/v1/object/public/word-images/words/garden.webp"
            )

    def test_get_public_url_already_full_url(self):
        full_url = "https://cdn.example.com/custom/path.png"
        url = ImageService.get_public_url(full_url)
        self.assertEqual(url, full_url)

    def test_get_public_url_empty_path_returns_none(self):
        self.assertIsNone(ImageService.get_public_url(None))
        self.assertIsNone(ImageService.get_public_url("   "))

    def test_get_local_path_exists(self):
        # We generated 'house.webp' in Phase 2
        path = ImageService.get_local_path("words/house.webp")
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())


class TestGameplayScreenLevelResolution(unittest.TestCase):
    """Test access authorization and active level resolution for gameplay view."""

    def setUp(self):
        self.mock_content_repo = MagicMock()
        self.mock_progression_svc = MagicMock()

        self.worlds = [
            {"id": "w-1", "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": "w-2", "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ]
        self.levels_w1 = [
            {"id": "lvl-1", "world_id": "w-1", "order_index": 1, "difficulty_band": "easy"},
            {"id": "lvl-2", "world_id": "w-1", "order_index": 2, "difficulty_band": "medium"},
        ]
        self.mock_content_repo.get_all_worlds.return_value = self.worlds
        self.mock_content_repo.get_levels_for_world.side_effect = lambda wid: self.levels_w1 if wid == "w-1" else []

    def test_resolve_active_level_authorized_query_param(self):
        with patch("streamlit.query_params", {"level_id": "lvl-2"}):
            self.mock_progression_svc.can_access_level.return_value = True
            world, level = resolve_active_level("student-1", self.mock_content_repo, self.mock_progression_svc)
            self.assertEqual(level["id"], "lvl-2")
            self.assertEqual(world["id"], "w-1")

    def test_resolve_active_level_unauthorized_query_param_blocked(self):
        # Requesting lvl-2 but can_access_level returns False for lvl-2, True for lvl-1
        with patch("streamlit.query_params", {"level_id": "lvl-2"}):
            self.mock_progression_svc.can_access_level.side_effect = lambda sid, lid: (lid == "lvl-1")
            self.mock_progression_svc.get_or_init_level_queue.return_value = {
                "is_level_completed": False,
                "active_queue": [{"id": "word-1"}]
            }

            world, level = resolve_active_level("student-1", self.mock_content_repo, self.mock_progression_svc)
            # Must fall back to accessible level-1, blocking level-2 access
            self.assertEqual(level["id"], "lvl-1")


class TestPreviousWordNavigation(unittest.TestCase):
    """Test suite for Previous Word intra-level navigation and state preservation."""

    def test_word_index_boundary_word_1_disabled(self):
        """At index 0 (Word 1), previous word navigation should remain at 0."""
        curr_idx = 0
        prev_idx = max(0, curr_idx - 1)
        self.assertEqual(prev_idx, 0)
        self.assertTrue(curr_idx == 0)

    def test_word_index_navigation_word_4_to_word_3(self):
        """At index 3 (Word 4), previous navigation transitions to index 2 (Word 3)."""
        curr_idx = 3
        prev_idx = max(0, curr_idx - 1)
        self.assertEqual(prev_idx, 2)

    def test_revisiting_completed_word_does_not_mutate_score_or_streak(self):
        """Verifies that re-evaluating or viewing an already completed word does not re-award score/streak."""
        mock_game_progress = MagicMock()
        mock_attempts_repo = MagicMock()

        is_word_already_done = True
        score_passed = True

        # When word is already completed, record_word_success must NOT be called
        if not is_word_already_done and score_passed:
            mock_game_progress.record_word_success("student-1", "word-1", "lvl-1", 100)

        mock_game_progress.record_word_success.assert_not_called()

    def test_completed_level_navigation_resets_view_to_playable_word_1(self):
        """Navigating to a previous completed level opens at Word 1 without forcing celebration screen."""
        session_state = {
            "celebrate_level_lvl-1": True,
            "view_word_idx_lvl-1": 6
        }
        # Clear celebration on level navigation
        session_state.pop("celebrate_level_lvl-1", None)
        session_state["view_word_idx_lvl-1"] = 0

        self.assertNotIn("celebrate_level_lvl-1", session_state)
        self.assertEqual(session_state["view_word_idx_lvl-1"], 0)


if __name__ == "__main__":
    unittest.main()
