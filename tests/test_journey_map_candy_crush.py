"""Tests for Candy Crush Style Winding Journey Map & Performance Optimizations."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest

from services.progression_service import ProgressionService


class TestCandyCrushJourneyMap(unittest.TestCase):
    """Test suite verifying performance batching and visual elements of Candy Crush Journey Map."""

    def test_get_student_journey_summary_batching(self):
        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
            {"id": "w2", "order_index": 2, "name": "Whispering Forest", "theme_key": "forest"},
            {"id": "w3", "order_index": 3, "name": "Royal Castle", "theme_key": "castle"},
        ]

        mock_prog_repo = MagicMock()
        mock_prog_repo.get_all_student_world_progress.return_value = [
            {"world_id": "w1", "status": "completed"},
            {"world_id": "w2", "status": "unlocked"},
        ]

        prog_svc = ProgressionService(content_repo=mock_content, progress_repo=mock_prog_repo)

        with patch("repositories.level_results_repo.get_level_results_repo") as mock_lvl_res_factory:
            mock_lvl_res = MagicMock()
            mock_lvl_res.get_all_level_results.return_value = [{"stars": 3}, {"stars": 2}]
            mock_lvl_res_factory.return_value = mock_lvl_res

            summary = prog_svc.get_student_journey_summary("test-student")

            assert summary["total_stars"] == 5
            assert summary["completed_worlds"] == 1
            assert summary["world_statuses"]["w1"] == "completed"
            assert summary["world_statuses"]["w2"] == "unlocked"
            assert summary["world_statuses"]["w3"] == "locked"
            assert summary["active_world_id"] == "w2"

            # Verify ONLY 1 call to get_all_student_world_progress and 1 call to get_all_level_results
            assert mock_prog_repo.get_all_student_world_progress.call_count == 1
            assert mock_lvl_res.get_all_level_results.call_count == 1

    def test_get_world_progression_summary_30_levels(self):
        mock_content = MagicMock()
        # Generate 30 levels structure
        thirty_levels = [
            {"id": f"l{i}", "world_id": "w1", "order_index": i, "difficulty_band": "easy" if i <= 10 else ("medium" if i <= 20 else "hard")}
            for i in range(1, 31)
        ]
        mock_content.get_levels_for_world.return_value = thirty_levels
        mock_content.get_all_worlds.return_value = [{"id": "w1", "order_index": 1, "name": "Sunlit Village"}]

        mock_prog_repo = MagicMock()
        # Student completed level 1 and 2
        mock_prog_repo.get_all_student_level_progress.return_value = [
            {"level_id": "l1", "status": "completed"},
            {"level_id": "l2", "status": "completed"},
            {"level_id": "l3", "status": "unlocked"},
        ]
        mock_prog_repo.get_all_student_world_progress.return_value = [
            {"world_id": "w1", "status": "unlocked"}
        ]

        prog_svc = ProgressionService(content_repo=mock_content, progress_repo=mock_prog_repo)

        with patch("repositories.level_results_repo.get_level_results_repo") as mock_lvl_res_factory:
            mock_lvl_res = MagicMock()
            mock_lvl_res.get_all_level_results.return_value = [
                {"level_id": "l1", "stars": 3},
                {"level_id": "l2", "stars": 2},
            ]
            mock_lvl_res_factory.return_value = mock_lvl_res

            res = prog_svc.get_world_progression_summary("test-student", "w1")

            assert len(res["levels"]) == 30
            assert res["completed_levels_count"] == 2
            assert res["world_stars"] == 5
            assert res["active_level_id"] == "l3"

            # Level 1 is completed
            assert res["levels"][0]["is_completed"] is True
            assert res["levels"][0]["stars"] == 3

            # Level 2 is completed
            assert res["levels"][1]["is_completed"] is True
            assert res["levels"][1]["stars"] == 2

            # Level 3 is unlocked & active
            assert res["levels"][2]["is_completed"] is False
            assert res["levels"][2]["is_accessible"] is True

            # Level 4 is locked (since level 3 is not finished)
            assert res["levels"][3]["is_accessible"] is False

    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("services.companion_service.get_companion_service")
    def test_journey_map_renders_world_level_winding_path(
        self,
        mock_comp_svc,
        mock_prog_svc,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc
    ):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Candy Adventurer"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {"total_score": 300, "current_streak": 5}
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
        ]
        mock_content_repo.return_value = mock_content

        mock_prog = MagicMock()
        mock_prog.get_student_journey_summary.return_value = {
            "all_worlds": [{"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"}],
            "world_statuses": {"w1": "unlocked"},
            "total_stars": 6,
            "completed_worlds": 0,
            "active_world_id": "w1"
        }
        mock_prog.get_world_progression_summary.return_value = {
            "levels": [
                {"id": "l1", "order_index": 1, "is_accessible": True, "is_completed": True, "stars": 3},
                {"id": "l2", "order_index": 2, "is_accessible": True, "is_completed": False, "stars": 0},
                {"id": "l3", "order_index": 3, "is_accessible": False, "is_completed": False, "stars": 0},
            ],
            "active_level_id": "l2",
            "completed_levels_count": 1,
            "world_stars": 3,
            "world_accessible": True
        }
        mock_prog_svc.return_value = mock_prog

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "stage": "egg",
            "xp": 50,
            "stage_info": MagicMock(name="Mystic Egg", icon="🥚"),
            "next_stage": MagicMock(name="Baby Chick"),
            "xp_to_next": 50,
            "progress_pct": 50.0
        }
        mock_comp_svc.return_value = mock_comp

        # Test Opening Village World Level Map
        at = AppTest.from_file("pages/2_Journey_Map.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.session_state["selected_world_id"] = "w1"
        at.run()

        assert not at.exception
        labels = [b.label for b in at.button]
        assert "🗺️ All Realms Map" in labels
        assert "1" in labels  # Level 1 Completed Node
        assert "2" in labels  # Level 2 Active Node
        assert "🔒" in labels  # Level 3 Locked Node
        assert "🚪 Exit Game" in labels

    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("services.companion_service.get_companion_service")
    def test_clicking_completed_and_active_level_nodes(
        self,
        mock_comp_svc,
        mock_prog_svc,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc
    ):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Node Adventurer"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {"total_score": 100, "current_streak": 2}
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
        ]
        mock_content_repo.return_value = mock_content

        mock_prog = MagicMock()
        mock_prog.get_student_journey_summary.return_value = {
            "all_worlds": [{"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"}],
            "world_statuses": {"w1": "unlocked"},
            "total_stars": 3,
            "completed_worlds": 0,
            "active_world_id": "w1"
        }
        mock_prog.get_world_progression_summary.return_value = {
            "levels": [
                {"id": "l1", "order_index": 1, "is_accessible": True, "is_completed": True, "stars": 3},
                {"id": "l2", "order_index": 2, "is_accessible": True, "is_completed": False, "stars": 0},
                {"id": "l3", "order_index": 3, "is_accessible": False, "is_completed": False, "stars": 0},
            ],
            "active_level_id": "l2",
            "completed_levels_count": 1,
            "world_stars": 3,
            "world_accessible": True
        }
        mock_prog_svc.return_value = mock_prog

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "stage": "egg",
            "xp": 50,
            "stage_info": MagicMock(name="Mystic Egg", icon="🥚"),
            "next_stage": MagicMock(name="Baby Chick"),
            "xp_to_next": 50,
            "progress_pct": 50.0
        }
        mock_comp_svc.return_value = mock_comp

        # Clicking level 1 (completed level) directly switches to play
        at = AppTest.from_file("pages/2_Journey_Map.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.session_state["selected_world_id"] = "w1"
        at.run()

        # Find button for level 1
        btn_lvl1 = next(b for b in at.button if b.key == "node_lvl_l1")
        assert btn_lvl1.disabled is False
        assert btn_lvl1.label == "1"

        # Find button for level 2 (current)
        btn_lvl2 = next(b for b in at.button if b.key == "node_lvl_l2")
        assert btn_lvl2.disabled is False
        assert btn_lvl2.label == "2"

        # Find button for level 3 (locked)
        btn_lvl3 = next(b for b in at.button if b.key == "node_lvl_l3")
        assert btn_lvl3.disabled is True
        assert btn_lvl3.label == "🔒"

