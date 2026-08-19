"""Tests validating Profile page rendering and Sidebar navigation components."""
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest


class TestProfilePageAndNavigation(unittest.TestCase):
    """Test suite verifying Profile page restoration and navigation stability."""

    @patch("services.profile_service.get_profile_service")
    @patch("repositories.profiles_repo.ProfilesRepository")
    @patch("services.auth_service.get_auth_service")
    def test_profile_page_renders_cleanly(self, mock_auth_svc, mock_profiles_repo, mock_profile_svc):
        mock_auth = MagicMock()
        mock_session = MagicMock()
        mock_session.success = True
        mock_session.user = {"id": "00000000-0000-0000-0000-000000000001", "email": "test@student.com"}
        mock_auth.get_current_session.return_value = mock_session
        mock_auth_svc.return_value = mock_auth

        mock_ps = MagicMock()
        mock_ps.get_full_student_profile.return_value = {
            "display_name": "Sound Explorer",
            "username": "sound_exp",
            "role": "student",
            "created_at_readable": "August 2026",
            "adventurer_id": "ADV-1234567890",
            "stats": {
                "total_score": 450,
                "total_stars": 12,
                "current_streak": 5,
                "best_streak": 8,
                "completed_levels": 6,
                "completed_worlds": 1,
            },
            "companion": {
                "stage": "blue_bird",
                "xp": 450,
                "stage_info": MagicMock(name="Blue Songbird", icon="🐦", description="A cheerful melody guide."),
                "next_stage": MagicMock(name="Sky Eagle", icon="🦅"),
                "xp_to_next": 150,
                "progress_pct": 75.0,
            },
            "badges": [
                {
                    "badge_key": "first_word",
                    "name": "First Sound",
                    "description": "Completed first word",
                    "icon": "🎉",
                    "criteria": "Complete 1 word",
                    "is_unlocked": True,
                    "unlocked_at": "2026-08-18",
                }
            ],
        }
        mock_profile_svc.return_value = mock_ps

        at = AppTest.from_file("pages/3_Profile.py", default_timeout=15)
        at.session_state["authenticated"] = True
        at.session_state["user"] = {"id": "00000000-0000-0000-0000-000000000001", "email": "test@student.com"}
        at.run()

        self.assertFalse(at.exception, f"Profile page raised exception: {at.exception}")


if __name__ == "__main__":
    unittest.main()
