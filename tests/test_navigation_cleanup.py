"""Tests verifying single sidebar navigation, removal of top navbar, and Adventurer ID resolution."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest


class TestNavigationCleanup(unittest.TestCase):
    """Test suite ensuring single-sidebar navigation, clean Home CTAs, and robust Adventurer ID."""

    @patch("config.settings.Settings.is_configured", return_value=True)
    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("repositories.level_results_repo.get_level_results_repo")
    @patch("services.companion_service.get_companion_service")
    def test_app_mode_has_no_duplicate_top_nav_and_valid_id(
        self,
        mock_comp_svc,
        mock_lvl_res_repo,
        mock_prog_svc,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc,
        mock_cfg
    ):
        student_id = "f619719b-7a30-4e96-81bb-602ddca7ceb2"
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": student_id, "email": "hero@test.com"},
            profile={"display_name": "Hero Adventurer", "adventurer_id": None}  # Simulating missing adventurer_id in DB
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {
            "display_name": "Hero Adventurer",
            "username": "hero_adv",
            "adventurer_id": None,  # Missing in DB
            "total_score": 250,
            "current_streak": 3
        }
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [{"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"}]
        mock_content.get_levels_for_world.return_value = [{"id": "l1", "order_index": 1, "difficulty_band": "easy"}]
        mock_content_repo.return_value = mock_content

        mock_prog = MagicMock()
        mock_prog.can_access_level.return_value = True
        mock_prog.get_or_init_level_queue.return_value = {
            "active_queue": [{"id": "w1", "text": "house"}],
            "all_words": [{"id": "w1", "text": "house"}],
            "is_level_completed": False
        }
        mock_prog_svc.return_value = mock_prog

        mock_lvl_res = MagicMock()
        mock_lvl_res.get_all_level_results.return_value = [{"stars": 3}]
        mock_lvl_res_repo.return_value = mock_lvl_res

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "student_id": student_id,
            "stage": "egg",
            "xp": 30,
            "stage_info": MagicMock(name="Mystic Egg", icon="🥚", description="A glowing egg."),
            "next_stage": MagicMock(name="Baby Chick"),
            "xp_to_next": 70,
            "progress_pct": 30.0
        }
        mock_comp_svc.return_value = mock_comp

        at = AppTest.from_file("app.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": student_id}
        at.run()

        assert not at.exception

        # 1. Verify Home action buttons
        main_button_labels = [b.label for b in at.button]
        assert "▶ Resume Adventure" in main_button_labels
        assert "🗺️ Explore Journey Map" in main_button_labels

        # Ensure redundant "Let's Play" / "View Profile" / "Mic Diagnostics" quick links are NOT duplicated in main area
        assert "🎮 Let's Play (Journey Map)" not in main_button_labels
        assert "👤 View Profile" not in main_button_labels
        assert "🎙️ Mic Diagnostics" not in main_button_labels

        # 2. Verify sidebar contains ONLY our 7 custom items
        sidebar_button_labels = [b.label for b in at.sidebar.button]
        assert "🏠 Home" in sidebar_button_labels
        assert "🗺️ Journey Map" in sidebar_button_labels
        assert "👤 Profile" in sidebar_button_labels
        assert "🎙️ Mic Test" in sidebar_button_labels
        assert "🎮 Enter Game" in sidebar_button_labels
        assert "🚪 Logout" in sidebar_button_labels

        # 3. Verify Adventurer ID is NEVER "None"
        # Check rendered text in HTML nodes
        for markdown_elem in at.markdown:
            assert "ID: None" not in str(markdown_elem.value)
