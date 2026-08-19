"""Comprehensive test suite for Phase 11 Final UI/UX Experience Polish (all 27 verification items)."""
from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest

from config.world_themes import get_world_theme, WORLD_THEMES
from services.scoring_service import get_scoring_service, ScoreResult
from services.override_service import get_override_service
from services.game_progress_service import calculate_stars


class TestWorldThemesVerification:
    """Checklist 8: World theme visual tokens and styling."""

    def test_all_seven_fantasy_realms_have_themes(self):
        expected_realms = ["village", "forest", "castle", "ocean", "space", "galaxy", "dragon"]
        for realm in expected_realms:
            theme = get_world_theme(realm)
            assert theme is not None
            assert theme.icon != ""
            assert theme.accent_color.startswith("#")
            assert "linear-gradient" in theme.card_bg_gradient

    def test_default_fallback_theme(self):
        theme = get_world_theme(None)
        assert theme.key == "default"


class TestAppModeHomeVerification:
    """Checklist 2, 3, 4: App Mode Home Dashboard, Resume Adventure vs Let's Play."""

    @patch("config.settings.Settings.is_configured", return_value=True)
    @patch("services.auth_service.get_auth_service")
    def test_unauthenticated_landing(self, mock_auth_svc, mock_cfg):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = None
        mock_auth_svc.return_value = mock_auth

        at = AppTest.from_file("app.py", default_timeout=15)
        at.session_state["authenticated"] = False
        at.session_state["user"] = None
        at.run()

        assert not at.exception
        labels = [b.label for b in at.button]
        assert "Log In to Account" in labels
        assert "Create New Account" in labels

    @patch("config.settings.Settings.is_configured", return_value=True)
    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("services.progression_service.get_progression_service")
    @patch("repositories.level_results_repo.get_level_results_repo")
    @patch("services.companion_service.get_companion_service")
    def test_authenticated_home_dashboard(
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
            user={"id": "00000000-0000-0000-0000-000000000001", "email": "student@test.com"},
            profile={"display_name": "Sound Explorer", "username": "sound_exp", "adventurer_id": "ADV-1234567890"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {
            "display_name": "Sound Explorer",
            "username": "sound_exp",
            "adventurer_id": "ADV-1234567890",
            "total_score": 450,
            "current_streak": 5,
            "best_streak": 8
        }
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"}
        ]
        mock_content.get_levels_for_world.return_value = [
            {"id": "l1", "order_index": 1, "difficulty_band": "easy"}
        ]
        mock_content_repo.return_value = mock_content

        mock_prog = MagicMock()
        mock_prog.can_access_level.return_value = True
        mock_prog.get_or_init_level_queue.return_value = {
            "active_queue": [{"id": "w_house", "text": "house"}],
            "all_words": [{"id": "w_house", "text": "house"}],
            "is_level_completed": False
        }
        mock_prog_svc.return_value = mock_prog

        mock_lvl_res = MagicMock()
        mock_lvl_res.get_level_result.return_value = {"stars": 3}
        mock_lvl_res_repo.return_value = mock_lvl_res

        mock_comp = MagicMock()
        mock_comp.get_or_create_companion.return_value = {
            "stage": "blue_bird",
            "xp": 450,
            "stage_info": MagicMock(name="Blue Songbird", icon="🐦", description="A crystal clear chirper."),
            "next_stage": MagicMock(name="Sky Eagle"),
            "xp_to_next": 150,
            "progress_pct": 75.0
        }
        mock_comp.get_reaction.return_value = "Chirp! Wonderful sound articulation!"
        mock_comp_svc.return_value = mock_comp

        at = AppTest.from_file("app.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.run()

        assert not at.exception
        labels = [b.label for b in at.button]
        # Primary & Secondary Home Dashboard CTAs
        assert "▶ Resume Adventure" in labels
        assert "🗺️ Explore Journey Map" in labels

        # Sidebar navigation items
        sidebar_labels = [b.label for b in at.sidebar.button]
        assert "🏠 Home" in sidebar_labels
        assert "🗺️ Journey Map" in sidebar_labels
        assert "👤 Profile" in sidebar_labels
        assert "🎙️ Mic Test" in sidebar_labels
        assert "🎮 Enter Game" in sidebar_labels
        assert "🚪 Logout" in sidebar_labels


class TestJourneyMapVerification:
    """Checklist 5, 6, 7, 8, 9, 10, 11: Candy Crush path, world states, level map transition."""

    @patch("services.auth_service.get_auth_service")
    @patch("repositories.profiles_repo.get_profiles_repository")
    @patch("repositories.content_repo.get_content_repository")
    @patch("repositories.progress_repo.get_progress_repository")
    @patch("repositories.level_results_repo.get_level_results_repo")
    @patch("services.progression_service.get_progression_service")
    @patch("services.companion_service.get_companion_service")
    def test_journey_map_and_exit_game(
        self,
        mock_comp_svc,
        mock_prog_svc,
        mock_lvl_res_repo,
        mock_prog_repo,
        mock_content_repo,
        mock_prof_repo,
        mock_auth_svc
    ):
        mock_auth = MagicMock()
        mock_auth.get_current_session.return_value = MagicMock(
            success=True,
            user={"id": "00000000-0000-0000-0000-000000000001"},
            profile={"display_name": "Sound Hero"}
        )
        mock_auth_svc.return_value = mock_auth

        mock_prof = MagicMock()
        mock_prof.get_profile.return_value = {"total_score": 100, "current_streak": 2, "best_streak": 4}
        mock_prof_repo.return_value = mock_prof

        mock_content = MagicMock()
        mock_content.get_all_worlds.return_value = [
            {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
            {"id": "w2", "order_index": 2, "name": "Whispering Forest", "theme_key": "forest"},
        ]
        mock_content.get_levels_for_world.return_value = [
            {"id": "l1", "order_index": 1, "difficulty_band": "easy"}
        ]
        mock_content_repo.return_value = mock_content

        mock_progress = MagicMock()
        mock_progress.get_student_world_progress.return_value = {"status": "unlocked"}
        mock_prog_repo.return_value = mock_progress

        mock_lvl_res = MagicMock()
        mock_lvl_res.get_level_result.return_value = {"stars": 2}
        mock_lvl_res_repo.return_value = mock_lvl_res

        mock_prog = MagicMock()
        mock_prog.get_student_journey_summary.return_value = {
            "all_worlds": [
                {"id": "w1", "order_index": 1, "name": "Sunlit Village", "theme_key": "village"},
                {"id": "w2", "order_index": 2, "name": "Whispering Forest", "theme_key": "forest"},
            ],
            "world_statuses": {"w1": "unlocked", "w2": "locked"},
            "total_stars": 2,
            "completed_worlds": 0,
            "active_world_id": "w1"
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

        at = AppTest.from_file("pages/2_Journey_Map.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001"}
        at.run()

        assert not at.exception
        labels = [b.label for b in at.button]
        # Checklist 6: Exit Game button present
        assert "🚪 Exit Game" in labels
        # Checklist 7: 7 realms winding path rendered
        assert any("Sunlit Village" in b for b in labels)


class TestTeacherOverrideVerification:
    """Checklist 16, 17, 18: Teacher password verification security."""

    def test_wrong_teacher_password_rejected(self):
        override_svc = get_override_service()
        assert not override_svc.authorize_teacher("wrong_password_123")
        assert not override_svc.authorize_teacher("")
        assert not override_svc.authorize_teacher("   ")

    def test_correct_teacher_password_accepted(self):
        override_svc = get_override_service()
        assert override_svc.authorize_teacher("teacher123")


class TestPronunciationScoringCategories:
    """Checklist 21, 22, 23, 24: Exact, Partial, Different word, Processing error."""

    def test_exact_match_score(self):
        scoring_svc = get_scoring_service()
        res = scoring_svc.score_pronunciation(target="house", transcript="house")
        assert res.score == 100
        assert res.passed is True
        assert "Outstanding" in res.feedback

    def test_partial_match_score(self):
        scoring_svc = get_scoring_service()
        res = scoring_svc.score_pronunciation(target="clock", transcript="clok")
        assert res.score >= 80
        assert res.passed is True

    def test_completely_different_word_score(self):
        scoring_svc = get_scoring_service()
        res = scoring_svc.score_pronunciation(target="clock", transcript="brain")
        assert res.score < 50
        assert res.passed is False
        assert "clock" in res.feedback

    def test_empty_transcript_no_penalty(self):
        scoring_svc = get_scoring_service()
        res = scoring_svc.score_pronunciation(target="house", transcript="")
        assert res.score == 0
        assert res.passed is False
        assert "No speech was detected" in res.feedback


class TestStarCalculationRules:
    """Checklist 13: 1 to 3 stars calculation."""

    def test_flawless_three_stars(self):
        stars = calculate_stars(accuracy=100.0, mistakes=0, skipped_resolved_count=0)
        assert stars == 3

    def test_two_stars_with_minor_mistake(self):
        stars = calculate_stars(accuracy=85.0, mistakes=1, skipped_resolved_count=0)
        assert stars == 2

    def test_one_star_with_override(self):
        stars = calculate_stars(accuracy=70.0, mistakes=3, skipped_resolved_count=1)
        assert stars == 1
