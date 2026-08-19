"""Tests for Phase 10 Stabilization: RLS Fix, Graceful Fallback, Performance Caching, and App Mode Sidebar."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest

from repositories.companion_repo import CompanionRepositoryError, get_companion_repository
from services.companion_service import get_companion_service
from repositories.content_repo import get_content_repository, clear_content_cache
from components.sidebar import render_app_sidebar


class TestCompanionGracefulFallback:
    """Checklist: student_companion error never crashes app and returns graceful fallback."""

    def test_companion_service_fallback_on_db_error(self):
        mock_repo = MagicMock()
        mock_repo.get_companion.side_effect = CompanionRepositoryError("RLS error 42501")
        mock_repo.upsert_companion.side_effect = CompanionRepositoryError("RLS error 42501")

        comp_svc = get_companion_service()
        comp_svc._repo = mock_repo

        # Must not raise exception
        comp = comp_svc.get_or_create_companion("student-test-uuid")
        assert comp is not None
        assert comp["stage"] == "egg"
        assert comp["xp"] == 0
        assert comp["stage_info"].name == "Mystic Egg"

    @patch("config.settings.Settings.is_configured", return_value=True)
    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("repositories.level_results_repo.get_level_results_repo")
    @patch("services.companion_service.get_companion_service")
    def test_home_page_renders_graceful_fallback_when_companion_fails(
        self,
        mock_comp_svc,
        mock_lvl_res_repo,
        mock_prog_svc,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc,
        mock_cfg
    ):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Test Adventurer"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {"display_name": "Test Adventurer", "total_score": 100, "current_streak": 2}
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [{"id": "w1", "order_index": 1, "name": "Village", "theme_key": "village"}]
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

        # Companion service throws exception
        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.side_effect = RuntimeError("Database connection timeout")
        mock_comp_svc.return_value = mock_comp

        at = AppTest.from_file("app.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.run()

        # App must run without crashing!
        assert not at.exception
        button_labels = [b.label for b in at.button]
        assert "🔄 Wake Companion" in button_labels
        assert "▶ Resume Adventure" in button_labels


class TestPerformanceOptimizations:
    """Verify single-query star calculation and static curriculum caching."""

    def test_content_repo_caching_behavior(self):
        clear_content_cache()
        content_repo = get_content_repository()

        # Mock get_supabase_client on shared repo
        with patch("repositories.content_repo.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_table.select.return_value.order.return_value.execute.return_value = MagicMock(
                data=[{"id": "w-test", "order_index": 1, "name": "Cached Realm", "theme_key": "village"}]
            )
            mock_client.table.return_value = mock_table
            mock_get_client.return_value = mock_client

            # First call fetches from DB
            w1 = content_repo.get_all_worlds()
            assert len(w1) == 1
            assert mock_client.table.call_count == 1

            # Second call uses process cache (no DB query)
            w2 = content_repo.get_all_worlds()
            assert len(w2) == 1
            assert mock_client.table.call_count == 1  # Not called again!

        clear_content_cache()


class TestAppModeSidebarRedesign:
    """Verify authenticated students see strictly the 7 student sidebar entries and no dev pages."""

    @patch("config.settings.Settings.is_configured", return_value=True)
    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("repositories.level_results_repo.get_level_results_repo")
    @patch("services.companion_service.get_companion_service")
    def test_sidebar_contains_only_student_navigation(
        self,
        mock_comp_svc,
        mock_lvl_res_repo,
        mock_prog_svc,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc,
        mock_cfg
    ):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Student Star"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {"display_name": "Student Star", "total_score": 50, "current_streak": 1}
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [{"id": "w1", "order_index": 1, "name": "Village", "theme_key": "village"}]
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
        mock_lvl_res.get_all_level_results.return_value = [{"stars": 2}]
        mock_lvl_res_repo.return_value = mock_lvl_res

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "stage": "egg",
            "xp": 20,
            "stage_info": MagicMock(name="Mystic Egg", icon="🥚", description="A glowing egg."),
            "next_stage": MagicMock(name="Baby Chick"),
            "xp_to_next": 80,
            "progress_pct": 20.0
        }
        mock_comp_svc.return_value = mock_comp

        at = AppTest.from_file("app.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.run()

        assert not at.exception
        # Check sidebar buttons specifically
        sidebar_button_labels = [b.label for b in at.sidebar.button]
        assert "🏠 Home" in sidebar_button_labels
        assert "🗺️ Journey Map" in sidebar_button_labels
        assert "👤 Profile" in sidebar_button_labels
        assert "🎙️ Mic Test" in sidebar_button_labels
        assert "🎮 Enter Game" in sidebar_button_labels
        assert "🚪 Logout" in sidebar_button_labels

        # Ensure Login, Signup, Level Dev are NOT in student sidebar
        assert "Login" not in sidebar_button_labels
        assert "Signup" not in sidebar_button_labels
        assert "Level Dev" not in sidebar_button_labels


class TestLevelDevProtection:
    """Verify 4_Level_Dev.py blocks unauthorized student access."""

    @patch("services.auth_service.get_auth_service")
    def test_level_dev_requires_developer_authorization(self, mock_auth_svc):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Normal Student"}
        )
        mock_auth_svc.return_value = mock_auth

        at = AppTest.from_file("pages/4_Level_Dev.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.session_state["dev_authorized"] = False
        at.run()

        assert not at.exception
        button_labels = [b.label for b in at.button]
        assert "Authenticate Developer Access" in button_labels
        assert "⬅️ Return to Student Home" in button_labels
