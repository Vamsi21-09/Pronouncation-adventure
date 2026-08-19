"""Comprehensive End-to-End Simulation Test for Candy Crush Journey Map & Navigation Flow."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest

from services.progression_service import get_progression_service


class TestJourneyMapE2EFlow(unittest.TestCase):
    """Simulates realistic student interaction across App Mode, Journey Map, and World Level Map."""

    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("services.companion_service.get_companion_service")
    def test_complete_journey_map_flow(
        self,
        mock_comp_svc,
        mock_prog_svc,
        mock_prof_repo,
        mock_auth_svc
    ):
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": student_id, "email": "student@example.com"},
            profile={"display_name": "Sound Explorer", "username": "sound_explorer"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {
            "display_name": "Sound Explorer",
            "username": "sound_explorer",
            "total_score": 450,
            "current_streak": 4,
            "best_streak": 6
        }
        mock_prof_repo.return_value = mock_prof

        # Real 7 worlds metadata
        worlds_mock = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
            {"id": "w2", "order_index": 2, "name": "Whispering Forest", "theme_key": "forest"},
            {"id": "w3", "order_index": 3, "name": "Royal Castle", "theme_key": "castle"},
            {"id": "w4", "order_index": 4, "name": "Coral Cove", "theme_key": "ocean"},
            {"id": "w5", "order_index": 5, "name": "Cosmic Outpost", "theme_key": "space"},
            {"id": "w6", "order_index": 6, "name": "Starlight Galaxy", "theme_key": "galaxy"},
            {"id": "w7", "order_index": 7, "name": "Dragon's Peak", "theme_key": "dragon"},
        ]

        village_levels = [
            {
                "id": f"lvl_w1_{i}",
                "order_index": i,
                "is_completed": (i <= 3),
                "is_accessible": (i <= 4),
                "stars": 3 if i <= 2 else (2 if i == 3 else 0)
            }
            for i in range(1, 31)
        ]

        mock_prog = MagicMock()
        mock_prog.get_student_journey_summary.return_value = {
            "all_worlds": worlds_mock,
            "world_statuses": {"w1": "unlocked", "w2": "locked"},
            "total_stars": 8,
            "completed_worlds": 0,
            "active_world_id": "w1"
        }
        mock_prog.get_world_progression_summary.return_value = {
            "levels": village_levels,
            "active_level_id": "lvl_w1_4",
            "completed_levels_count": 3,
            "world_stars": 8,
            "world_accessible": True
        }
        mock_prog_svc.return_value = mock_prog

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "student_id": student_id,
            "stage": "nestling",
            "xp": 150,
            "stage_info": MagicMock(name="Feathered Nestling", icon="🐣"),
            "next_stage": MagicMock(name="Sky Explorer"),
            "xp_to_next": 50,
            "progress_pct": 75.0
        }
        mock_comp_svc.return_value = mock_comp

        # 1. Test Journey Map main screen (World Road)
        at = AppTest.from_file("pages/2_Journey_Map.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": student_id}
        at.session_state["profile"] = {"display_name": "Sound Explorer"}
        at.run()

        assert not at.exception
        button_labels = [b.label for b in at.button]

        # Verify Exit Game button
        assert "🚪 Exit Game" in button_labels

        # Verify Village is unlocked and accessible
        assert any("Explore Sunlit Village" in b for b in button_labels)
        # Verify Forest is locked
        assert any("Locked (Complete World 1)" in b for b in button_labels)

        # 2. Test Drilled Down Village Level Map
        at_village = AppTest.from_file("pages/2_Journey_Map.py", default_timeout=15)
        at_village.session_state["authenticated"] = True
        at_village.session_state["user"] = {"id": student_id}
        at_village.session_state["selected_world_id"] = "w1"
        at_village.run()

        assert not at_village.exception
        village_buttons = [b.label for b in at_village.button]

        # Verify All Realms button exists
        assert "🗺️ All Realms Map" in village_buttons

        # Verify completed levels 1..3 and active level 4 nodes exist
        assert "1" in village_buttons
        assert "2" in village_buttons
        assert "3" in village_buttons
        assert "4" in village_buttons
        assert "🔒" in village_buttons
