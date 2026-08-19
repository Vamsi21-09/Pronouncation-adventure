"""Unit and integration tests for Phase 9: Companion Evolution, Treasure Rewards, Badges, and Mystery Surprises."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from services.companion_service import CompanionService, COMPANION_STAGES
from services.treasure_service import TreasureService
from services.badge_service import BadgeService
from services.mystery_service import MysteryService
from repositories.companion_repo import CompanionRepository
from repositories.rewards_repo import RewardsRepository
from repositories.treasure_repo import TreasureRepository
from repositories.badges_repo import BadgesRepository
from repositories.mystery_repo import MysteryRepository


class TestPhase9CompanionService(unittest.TestCase):
    """Test companion evolution thresholds, reactions, and persistent idempotency."""

    def setUp(self):
        self.mock_repo = MagicMock(spec=CompanionRepository)
        self.service = CompanionService(companion_repo=self.mock_repo)

    def test_companion_evolution_thresholds(self):
        """Verify companion stage evolution calculation based on cumulative XP."""
        self.assertEqual(CompanionService.calculate_stage(0).stage_key, "egg")
        self.assertEqual(CompanionService.calculate_stage(99).stage_key, "egg")
        self.assertEqual(CompanionService.calculate_stage(100).stage_key, "baby_bird")
        self.assertEqual(CompanionService.calculate_stage(299).stage_key, "baby_bird")
        self.assertEqual(CompanionService.calculate_stage(300).stage_key, "blue_bird")
        self.assertEqual(CompanionService.calculate_stage(599).stage_key, "blue_bird")
        self.assertEqual(CompanionService.calculate_stage(600).stage_key, "eagle")
        self.assertEqual(CompanionService.calculate_stage(999).stage_key, "eagle")
        self.assertEqual(CompanionService.calculate_stage(1000).stage_key, "phoenix")
        self.assertEqual(CompanionService.calculate_stage(1499).stage_key, "phoenix")
        self.assertEqual(CompanionService.calculate_stage(1500).stage_key, "golden_phoenix")
        self.assertEqual(CompanionService.calculate_stage(5000).stage_key, "golden_phoenix")

    def test_add_xp_evolution_transition(self):
        """XP award correctly triggers evolution from egg to baby_bird."""
        student_id = "test-student-1"
        self.mock_repo.has_xp_event.return_value = False
        self.mock_repo.get_companion.return_value = {"student_id": student_id, "stage": "egg", "xp": 50}
        self.mock_repo.record_xp_event.return_value = True

        result = self.service.add_xp(student_id, 75, "level_result:lvl-1")

        self.assertTrue(result["success"])
        self.assertFalse(result["already_awarded"])
        self.assertEqual(result["xp_awarded"], 75)
        self.assertTrue(result["evolved"])
        self.assertEqual(result["previous_stage"], "egg")
        self.mock_repo.upsert_companion.assert_called_with(student_id, "baby_bird", 125)

    def test_add_xp_strict_idempotency(self):
        """Same event_key cannot award XP twice."""
        student_id = "test-student-2"
        self.mock_repo.has_xp_event.return_value = True
        self.mock_repo.get_companion.return_value = {"student_id": student_id, "stage": "egg", "xp": 100}

        result = self.service.add_xp(student_id, 50, "level_result:lvl-1")

        self.assertTrue(result["success"])
        self.assertTrue(result["already_awarded"])
        self.assertEqual(result["xp_awarded"], 0)
        self.assertFalse(result["evolved"])
        self.mock_repo.record_xp_event.assert_not_called()


class TestPhase9TreasureService(unittest.TestCase):
    """Test treasure chest rewards and single-open idempotency."""

    def setUp(self):
        self.mock_rewards_repo = MagicMock(spec=RewardsRepository)
        self.mock_treasure_repo = MagicMock(spec=TreasureRepository)
        self.service = TreasureService(
            rewards_repo=self.mock_rewards_repo,
            treasure_repo=self.mock_treasure_repo
        )

    def test_open_treasure_first_time(self):
        """Opening a chest for the first time picks an unowned reward and saves event."""
        student_id = "test-student-3"
        level_id = "lvl-w1-l1"

        self.mock_treasure_repo.get_treasure_event.return_value = None
        self.mock_rewards_repo.get_all_rewards.return_value = [
            {"id": "r1", "name": "Gold Cap", "rarity": "rare", "type": "avatar"},
            {"id": "r2", "name": "Headphones", "rarity": "epic", "type": "avatar"},
        ]
        self.mock_rewards_repo.get_student_rewards.return_value = [{"reward_id": "r1"}]

        result = self.service.open_treasure(student_id, level_id)

        self.assertTrue(result["success"])
        self.assertFalse(result["already_opened"])
        self.assertEqual(result["reward"]["id"], "r2")
        self.mock_rewards_repo.award_reward_to_student.assert_called_with(student_id, "r2", source="treasure")
        self.mock_treasure_repo.record_treasure_event.assert_called_with(student_id, level_id, "r2")

    def test_open_treasure_idempotency(self):
        """Subsequent chest open calls return existing reward without re-awarding."""
        student_id = "test-student-4"
        level_id = "lvl-w1-l1"

        existing = {
            "id": "t-1",
            "student_id": student_id,
            "level_id": level_id,
            "reward_id": "r1",
            "rewards": {"id": "r1", "name": "Gold Cap", "rarity": "rare"}
        }
        self.mock_treasure_repo.get_treasure_event.return_value = existing

        result = self.service.open_treasure(student_id, level_id)

        self.assertTrue(result["success"])
        self.assertTrue(result["already_opened"])
        self.assertEqual(result["reward"]["name"], "Gold Cap")
        self.mock_rewards_repo.award_reward_to_student.assert_not_called()


class TestPhase9BadgeService(unittest.TestCase):
    """Test badge eligibility evaluation and idempotency."""

    def setUp(self):
        self.mock_badges_repo = MagicMock(spec=BadgesRepository)
        self.mock_profiles_repo = MagicMock()
        self.mock_progress_repo = MagicMock()
        self.mock_results_repo = MagicMock()
        self.service = BadgeService(
            badges_repo=self.mock_badges_repo,
            profiles_repo=self.mock_profiles_repo,
            progress_repo=self.mock_progress_repo,
            level_results_repo=self.mock_results_repo
        )

    def test_check_and_award_first_words_badge(self):
        """Student with 1 completed level earns first_words badge."""
        student_id = "test-student-5"
        self.mock_badges_repo.get_all_badges.return_value = [
            {"id": "b1", "key": "first_words", "name": "First Words", "criteria_type": "total_words", "criteria_value": 1},
            {"id": "b2", "key": "streak_5", "name": "5-Day Streak", "criteria_type": "streak", "criteria_value": 5},
        ]
        self.mock_badges_repo.get_student_badges.return_value = []
        self.mock_profiles_repo.get_profile.return_value = {"best_streak": 2, "current_streak": 2}
        self.mock_results_repo.get_all_student_results.return_value = [{"words_completed": 7, "stars": 3}]
        self.mock_badges_repo.award_badge_to_student.return_value = {"badge_id": "b1"}

        newly_awarded = self.service.check_and_award_badges(student_id)

        self.assertEqual(len(newly_awarded), 1)
        self.assertEqual(newly_awarded[0]["key"], "first_words")
        self.mock_badges_repo.award_badge_to_student.assert_called_with(student_id, "b1")

    def test_badge_never_awarded_twice(self):
        """Student who already owns a badge does not receive duplicate awards."""
        student_id = "test-student-6"
        self.mock_badges_repo.get_all_badges.return_value = [
            {"id": "b1", "key": "first_words", "name": "First Words", "criteria_type": "total_words", "criteria_value": 1}
        ]
        self.mock_badges_repo.get_student_badges.return_value = [{"badge_id": "b1"}]
        self.mock_profiles_repo.get_profile.return_value = {"best_streak": 5}
        self.mock_results_repo.get_all_student_results.return_value = [{"words_completed": 7}]

        newly_awarded = self.service.check_and_award_badges(student_id)

        self.assertEqual(len(newly_awarded), 0)
        self.mock_badges_repo.award_badge_to_student.assert_not_called()


class TestPhase9MysteryService(unittest.TestCase):
    """Test mystery surprise probability check and idempotency."""

    def setUp(self):
        self.mock_mystery_repo = MagicMock(spec=MysteryRepository)
        self.service = MysteryService(mystery_repo=self.mock_mystery_repo)

    def test_maybe_trigger_mystery_guaranteed_roll(self):
        """When probability is 1.0, mystery surprise triggers."""
        student_id = "test-student-7"
        level_id = "lvl-w1-l1"

        self.mock_mystery_repo.get_mystery_event.return_value = None
        self.mock_mystery_repo.record_mystery_event.return_value = {"surprise_key": "dancing_penguin"}

        result = self.service.maybe_trigger_mystery(student_id, level_id, trigger_probability=1.0)

        self.assertIsNotNone(result)
        self.assertTrue(result["triggered"])
        self.assertFalse(result["already_triggered"])
        self.assertIn("info", result)

    def test_mystery_already_triggered_idempotency(self):
        """Existing mystery surprise returns recorded event without rolling new one."""
        student_id = "test-student-8"
        level_id = "lvl-w1-l1"

        self.mock_mystery_repo.get_mystery_event.return_value = {"surprise_key": "robot"}

        result = self.service.maybe_trigger_mystery(student_id, level_id, trigger_probability=1.0)

        self.assertIsNotNone(result)
        self.assertTrue(result["triggered"])
        self.assertTrue(result["already_triggered"])
        self.assertEqual(result["surprise_key"], "robot")
        self.mock_mystery_repo.record_mystery_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
