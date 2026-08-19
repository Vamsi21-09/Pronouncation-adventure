"""Unit tests for ProfileService aggregation and formatters."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from services.profile_service import ProfileService, format_readable_date, generate_adventurer_id


class TestProfileServiceUnit:
    """Test unit behavior of ProfileService aggregation."""

    def test_generate_adventurer_id_format_and_persistence(self):
        # Must be exactly 10 digits, numeric only
        id1 = generate_adventurer_id("f619719b-7a30-4e96-81bb-602ddca7ceb2")
        assert len(id1) == 10
        assert id1.isdigit()

        # Must be deterministic (persistent)
        id2 = generate_adventurer_id("f619719b-7a30-4e96-81bb-602ddca7ceb2")
        assert id1 == id2

        # Must vary by UUID
        id3 = generate_adventurer_id("a1111111-2222-3333-4444-555555555555")
        assert len(id3) == 10
        assert id3.isdigit()
        assert id1 != id3

    def test_format_readable_date(self):
        assert format_readable_date("2026-08-14T12:00:00Z") == "August 14, 2026"
        assert format_readable_date("2026-01-01T00:00:00+00:00") == "January 01, 2026"
        assert format_readable_date(None) == "Recent Explorer"

    def test_get_full_student_profile_aggregation(self):
        mock_profiles_repo = MagicMock()
        mock_profiles_repo.get_profile.return_value = {
            "id": "std-123",
            "username": "superstar",
            "display_name": "Super Star",
            "role": "student",
            "created_at": "2026-08-14T10:00:00Z",
            "total_score": 1250,
            "current_streak": 5,
            "best_streak": 12,
        }

        mock_level_results_repo = MagicMock()
        mock_level_results_repo.client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"stars": 3, "score": 700, "words_completed": 7},
                {"stars": 2, "score": 500, "words_completed": 7},
            ]
        )

        mock_progress_repo = MagicMock()
        mock_progress_repo.client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"world_id": "w1", "status": "completed"}]
        )

        mock_badges_repo = MagicMock()
        mock_badges_repo.get_all_badges.return_value = [
            {"id": "b1", "name": "First Words", "icon": "🌟", "description": "Done", "criteria": "Complete L1"},
            {"id": "b2", "name": "Streak Master", "icon": "🔥", "description": "Streak", "criteria": "Streak 5"},
        ]
        mock_badges_repo.get_student_badges.return_value = [
            {"badge_id": "b1", "unlocked_at": "2026-08-14T11:00:00Z", "badges": {"id": "b1", "name": "First Words"}}
        ]

        mock_comp_service = MagicMock()
        mock_comp_service.get_or_create_companion.return_value = {
            "stage": "baby_bird",
            "xp": 150,
            "stage_info": MagicMock(name="Baby Chick", icon="🐣", description="Hatchling"),
            "next_stage": MagicMock(name="Blue Songbird", icon="🐦"),
            "xp_to_next": 150,
            "progress_pct": 25.0,
        }

        service = ProfileService(
            profiles_repo=mock_profiles_repo,
            level_results_repo=mock_level_results_repo,
            progress_repo=mock_progress_repo,
            badges_repo=mock_badges_repo,
            companion_service=mock_comp_service
        )

        full = service.get_full_student_profile("std-123")

        assert full["username"] == "superstar"
        assert full["display_name"] == "Super Star"
        assert full["created_at_readable"] == "August 14, 2026"
        assert len(full["adventurer_id"]) == 10
        assert full["adventurer_id"].isdigit()
        assert full["stats"]["total_score"] == 1250
        assert full["stats"]["total_stars"] == 5
        assert full["stats"]["completed_levels"] == 2
        assert full["stats"]["completed_worlds"] == 1
        assert full["stats"]["words_completed"] == 14

        # Badges check
        unlocked = [b for b in full["badges"] if b["is_unlocked"]]
        locked = [b for b in full["badges"] if not b["is_unlocked"]]
        assert len(unlocked) == 1
        assert unlocked[0]["id"] == "b1"
        assert len(locked) == 1
        assert locked[0]["id"] == "b2"
