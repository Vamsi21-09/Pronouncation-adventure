"""Unit and integration tests for Phase 7: Score, Streak, Stars, and Level Results."""
from __future__ import annotations

import threading
import unittest
from unittest.mock import MagicMock

from services.scoring_service import award_points, ScoringService
from services.speech_service import SpeechService
from services.game_progress_service import calculate_stars, GameProgressService
from repositories.profiles_repo import ProfilesRepository
from repositories.progress_repo import ProgressRepository
from repositories.level_results_repo import LevelResultsRepository
from repositories.attempts_repo import AttemptsRepository
from services.progression_service import ProgressionService


class TestPhase7ScoringAndResults(unittest.TestCase):
    """Test suite for Phase 7 score awards, streak progression, star calculation, and level completion idempotency."""

    def test_award_points_deterministic_mapping(self):
        """Verify award_points maps scores accurately and deterministically."""
        self.assertEqual(award_points(100), 100)
        self.assertEqual(award_points(95), 100)
        self.assertEqual(award_points(94), 85)
        self.assertEqual(award_points(85), 85)
        self.assertEqual(award_points(84), 70)
        self.assertEqual(award_points(75), 70)
        self.assertEqual(award_points(74), 0)
        self.assertEqual(award_points(50), 0)
        self.assertEqual(award_points(0), 0)

    def test_calculate_stars_thresholds(self):
        """Verify star calculation rules against accuracy, mistakes, and overrides."""
        # 3 Stars: Accuracy >= 85%, 0 mistakes, 0 overrides
        self.assertEqual(calculate_stars(accuracy=100.0, mistakes=0, skipped_resolved_count=0), 3)
        self.assertEqual(calculate_stars(accuracy=85.0, mistakes=0, skipped_resolved_count=0), 3)

        # 2 Stars: Accuracy >= 70% or few mistakes / overrides
        self.assertEqual(calculate_stars(accuracy=85.0, mistakes=1, skipped_resolved_count=0), 2)
        self.assertEqual(calculate_stars(accuracy=80.0, mistakes=0, skipped_resolved_count=1), 2)
        self.assertEqual(calculate_stars(accuracy=75.0, mistakes=2, skipped_resolved_count=1), 2)
        self.assertEqual(calculate_stars(accuracy=70.0, mistakes=2, skipped_resolved_count=0), 2)

        # 1 Star: Lower accuracy or higher mistakes/overrides
        self.assertEqual(calculate_stars(accuracy=65.0, mistakes=3, skipped_resolved_count=1), 1)
        self.assertEqual(calculate_stars(accuracy=50.0, mistakes=5, skipped_resolved_count=3), 1)

    def test_streak_progression_and_milestones(self):
        """Verify streak increments, resets on genuine fail, and flags 3-in-a-row milestones."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        mock_progress_repo = MagicMock(spec=ProgressRepository)
        mock_level_results_repo = MagicMock(spec=LevelResultsRepository)
        mock_attempts_repo = MagicMock(spec=AttemptsRepository)
        mock_prog_svc = MagicMock(spec=ProgressionService)

        service = GameProgressService(
            profiles_repo=mock_profiles_repo,
            progress_repo=mock_progress_repo,
            level_results_repo=mock_level_results_repo,
            attempts_repo=mock_attempts_repo,
            progression_svc=mock_prog_svc
        )

        student_id = "stu_123"

        # Mock initial profile with streak 2
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 200,
            "current_streak": 2,
            "best_streak": 2
        }

        # Passing streak -> reaches streak 3 (milestone)
        res = service.update_streak(student_id, passed=True)
        self.assertEqual(res["current_streak"], 3)
        self.assertEqual(res["best_streak"], 3)
        self.assertTrue(res["is_milestone"])

        # Another pass -> streak 4 (not a milestone)
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 200,
            "current_streak": 3,
            "best_streak": 3
        }
        res2 = service.update_streak(student_id, passed=True)
        self.assertEqual(res2["current_streak"], 4)
        self.assertFalse(res2["is_milestone"])

        # Genuine failure -> streak resets to 0, best_streak preserved
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 200,
            "current_streak": 4,
            "best_streak": 4
        }
        res_fail = service.update_streak(student_id, passed=False)
        self.assertEqual(res_fail["current_streak"], 0)
        self.assertEqual(res_fail["best_streak"], 4)
        self.assertFalse(res_fail["is_milestone"])

    def test_speech_error_does_not_corrupt_or_reset_streak(self):
        """Verify that speech recognition errors do not invoke streak reset."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        service = GameProgressService(profiles_repo=mock_profiles_repo)

        speech_res = SpeechService.transcribe(error="network")
        self.assertFalse(speech_res.is_usable())

        # When speech is not usable, update_streak is NOT called
        mock_profiles_repo.reset_streak.assert_not_called()
        mock_profiles_repo.update_stats.assert_not_called()

    def test_record_word_success_idempotency(self):
        """Verify that re-awarding a word already completed does not duplicate points or streak."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        mock_progress_repo = MagicMock(spec=ProgressRepository)
        mock_level_results_repo = MagicMock(spec=LevelResultsRepository)
        mock_attempts_repo = MagicMock(spec=AttemptsRepository)
        mock_prog_svc = MagicMock(spec=ProgressionService)

        service = GameProgressService(
            profiles_repo=mock_profiles_repo,
            progress_repo=mock_progress_repo,
            level_results_repo=mock_level_results_repo,
            attempts_repo=mock_attempts_repo,
            progression_svc=mock_prog_svc
        )

        student_id = "stu_123"
        word_id = "word_abc"
        level_id = "lvl_1"

        # 1. First-time completion
        mock_progress_repo.get_level_word_progress.return_value = [
            {"word_id": word_id, "status": "pending", "attempt_count": 1}
        ]
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 100,
            "current_streak": 1,
            "best_streak": 1
        }
        mock_prog_svc.complete_word.return_value = {"is_level_completed": False}

        res1 = service.record_word_success(student_id, word_id, level_id, pronunciation_score=95)
        self.assertTrue(res1["success"])
        self.assertFalse(res1["already_completed"])
        self.assertEqual(res1["points_awarded"], 100)
        self.assertEqual(res1["total_score"], 200)
        self.assertEqual(res1["current_streak"], 2)
        mock_profiles_repo.update_stats.assert_called_once()

        # 2. Duplicate call (e.g. page refresh / double click)
        mock_profiles_repo.update_stats.reset_mock()
        mock_progress_repo.get_level_word_progress.return_value = [
            {"word_id": word_id, "status": "completed", "attempt_count": 1}
        ]
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 200,
            "current_streak": 2,
            "best_streak": 2
        }

        res2 = service.record_word_success(student_id, word_id, level_id, pronunciation_score=95)
        self.assertTrue(res2["success"])
        self.assertTrue(res2["already_completed"])
        self.assertEqual(res2["points_awarded"], 0)
        self.assertEqual(res2["total_score"], 200)
        self.assertEqual(res2["current_streak"], 2)
        mock_profiles_repo.update_stats.assert_not_called()

    def test_concurrent_record_word_success_never_duplicates_points(self):
        """Simulate two concurrent threads attempting to award the same word simultaneously."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        mock_progress_repo = MagicMock(spec=ProgressRepository)
        mock_level_results_repo = MagicMock(spec=LevelResultsRepository)
        mock_attempts_repo = MagicMock(spec=AttemptsRepository)
        mock_prog_svc = MagicMock(spec=ProgressionService)

        service = GameProgressService(
            profiles_repo=mock_profiles_repo,
            progress_repo=mock_progress_repo,
            level_results_repo=mock_level_results_repo,
            attempts_repo=mock_attempts_repo,
            progression_svc=mock_prog_svc
        )

        student_id = "stu_concurrent"
        word_id = "word_test"
        level_id = "lvl_test"

        # Shared state
        state = {"status": "pending", "score": 0, "streak": 0}

        def get_word_progress_side_effect(s_id, l_id):
            return [{"word_id": word_id, "status": state["status"]}]

        def complete_word_side_effect(s_id, l_id, w_id):
            state["status"] = "completed"
            return {"is_level_completed": False}

        def update_stats_side_effect(user_id, score_delta, new_current_streak, new_best_streak):
            state["score"] += score_delta
            state["streak"] = new_current_streak
            return {"total_score": state["score"], "current_streak": state["streak"]}

        def get_profile_side_effect(u_id):
            return {"id": u_id, "total_score": state["score"], "current_streak": state["streak"], "best_streak": state["streak"]}

        mock_progress_repo.get_level_word_progress.side_effect = get_word_progress_side_effect
        mock_prog_svc.complete_word.side_effect = complete_word_side_effect
        mock_profiles_repo.update_stats.side_effect = update_stats_side_effect
        mock_profiles_repo.get_profile.side_effect = get_profile_side_effect

        results = []

        def worker():
            res = service.record_word_success(student_id, word_id, level_id, pronunciation_score=100)
            results.append(res)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(results), 2)
        total_points_awarded = sum(r["points_awarded"] for r in results)
        # Exactly one thread got points (100 pts), the other got already_completed (0 pts)
        self.assertEqual(total_points_awarded, 100)
        self.assertEqual(state["score"], 100)
        self.assertEqual(state["streak"], 1)
        first_time_count = sum(1 for r in results if not r["already_completed"])
        duplicate_count = sum(1 for r in results if r["already_completed"])
        self.assertEqual(first_time_count, 1)
        self.assertEqual(duplicate_count, 1)

    def test_save_level_result_race_condition_handling(self):
        """Verify that LevelResultsRepository catches unique constraint errors and returns existing record."""
        mock_client = MagicMock()
        repo = LevelResultsRepository(client=mock_client)

        student_id = "stu_race"
        level_id = "lvl_race"
        persisted_row = {
            "id": "res_123",
            "student_id": student_id,
            "level_id": level_id,
            "score": 700,
            "accuracy": 100.0,
            "words_completed": 7,
            "mistakes": 0,
            "streak_at_completion": 7,
            "stars": 3
        }

        # Step 1: Initial get_level_result returns None (before insert)
        # Step 2: insert throws unique constraint error (simulating concurrent insert from another worker)
        # Step 3: subsequent get_level_result returns the persisted row
        get_calls = [None, persisted_row]
        def select_side_effect(*args, **kwargs):
            query = MagicMock()
            query.eq.return_value = query
            def execute():
                val = get_calls.pop(0) if get_calls else persisted_row
                return MagicMock(data=[val] if val else [])
            query.execute = execute
            return query

        def insert_side_effect(*args, **kwargs):
            query = MagicMock()
            def execute():
                raise Exception("duplicate key value violates unique constraint 'level_results_student_level_key' (SQLSTATE 23505)")
            query.execute = execute
            return query

        table_mock = MagicMock()
        table_mock.select.side_effect = select_side_effect
        table_mock.insert.side_effect = insert_side_effect
        mock_client.table.return_value = table_mock

        result = repo.save_level_result(
            student_id=student_id,
            level_id=level_id,
            score=700,
            accuracy=100.0,
            words_completed=7,
            mistakes=0,
            streak_at_completion=7,
            stars=3
        )
        self.assertEqual(result["id"], "res_123")
        self.assertEqual(result["stars"], 3)

    def test_complete_level_with_results_idempotency_and_persistence(self):
        """Verify level completion calculations and idempotent handling."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        mock_progress_repo = MagicMock(spec=ProgressRepository)
        mock_level_results_repo = MagicMock(spec=LevelResultsRepository)
        mock_attempts_repo = MagicMock(spec=AttemptsRepository)
        mock_prog_svc = MagicMock(spec=ProgressionService)

        service = GameProgressService(
            profiles_repo=mock_profiles_repo,
            progress_repo=mock_progress_repo,
            level_results_repo=mock_level_results_repo,
            attempts_repo=mock_attempts_repo,
            progression_svc=mock_prog_svc
        )

        student_id = "stu_123"
        level_id = "lvl_1"

        # Case 1: No previous result -> Compute and persist
        mock_level_results_repo.get_level_result.return_value = None
        mock_progress_repo.get_level_word_progress.return_value = [
            {"word_id": f"w_{i}", "status": "completed"} for i in range(7)
        ]
        mock_attempts_repo.get_attempts_for_level.return_value = [
            {"passed": True, "score": 95} for _ in range(7)
        ]
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 700,
            "current_streak": 7,
            "best_streak": 7
        }
        mock_level_results_repo.save_level_result.return_value = {
            "student_id": student_id,
            "level_id": level_id,
            "score": 700,
            "accuracy": 100.0,
            "words_completed": 7,
            "mistakes": 0,
            "streak_at_completion": 7,
            "stars": 3
        }

        res = service.complete_level_with_results(student_id, level_id)
        self.assertEqual(res["stars"], 3)
        self.assertEqual(res["accuracy"], 100.0)
        self.assertEqual(res["words_completed"], 7)
        self.assertEqual(res["mistakes"], 0)
        mock_level_results_repo.save_level_result.assert_called_once()
        mock_prog_svc.complete_level.assert_called_once_with(student_id, level_id)

        # Case 2: Subsequent call (idempotent return)
        mock_level_results_repo.save_level_result.reset_mock()
        mock_prog_svc.complete_level.reset_mock()
        mock_level_results_repo.get_level_result.return_value = res

        res_repeat = service.complete_level_with_results(student_id, level_id)
        self.assertEqual(res_repeat, res)
        mock_level_results_repo.save_level_result.assert_not_called()

    def test_complete_level_with_overrides_and_mistakes_calculates_two_stars(self):
        """Verify that teacher overrides and mistakes properly reduce stars."""
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        mock_progress_repo = MagicMock(spec=ProgressRepository)
        mock_level_results_repo = MagicMock(spec=LevelResultsRepository)
        mock_attempts_repo = MagicMock(spec=AttemptsRepository)
        mock_prog_svc = MagicMock(spec=ProgressionService)

        service = GameProgressService(
            profiles_repo=mock_profiles_repo,
            progress_repo=mock_progress_repo,
            level_results_repo=mock_level_results_repo,
            attempts_repo=mock_attempts_repo,
            progression_svc=mock_prog_svc
        )

        student_id = "stu_123"
        level_id = "lvl_1"

        mock_level_results_repo.get_level_result.return_value = None
        # 6 words completed, 1 resolved by override
        mock_progress_repo.get_level_word_progress.return_value = [
            {"word_id": f"w_{i}", "status": "completed"} for i in range(6)
        ] + [{"word_id": "w_override", "status": "resolved_by_override"}]

        # 6 passed attempts, 2 failed attempts
        mock_attempts_repo.get_attempts_for_level.return_value = [
            {"passed": True, "score": 90} for _ in range(6)
        ] + [
            {"passed": False, "score": 40},
            {"passed": False, "score": 45}
        ]

        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 510,
            "current_streak": 3,
            "best_streak": 5
        }

        def save_side_effect(**kwargs):
            return kwargs
        mock_level_results_repo.save_level_result.side_effect = save_side_effect

        res = service.complete_level_with_results(student_id, level_id)
        # Accuracy: 6 passed out of 8 total = 75.0%
        # Mistakes: 2
        # Overrides: 1
        # Star rule: 2 stars (accuracy >= 70% and mistakes <= 2 and overrides <= 1)
        self.assertEqual(res["stars"], 2)
        self.assertEqual(res["accuracy"], 75.0)
        self.assertEqual(res["words_completed"], 6)
        self.assertEqual(res["mistakes"], 2)


if __name__ == "__main__":
    unittest.main()
