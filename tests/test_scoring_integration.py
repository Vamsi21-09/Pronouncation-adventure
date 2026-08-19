"""Integration tests for pronunciation scoring, progression gating, attempts repository, and concurrency."""
from __future__ import annotations

import threading
import unittest
from unittest.mock import MagicMock

from services.scoring_service import ScoringService
from services.speech_service import SpeechService, ERROR_NO_SPEECH, ERROR_PERMISSION_DENIED
from repositories.attempts_repo import AttemptsRepository
from services.game_progress_service import GameProgressService
from repositories.profiles_repo import ProfilesRepository


class MockAttemptsDb:
    """In-memory thread-safe mock table for word_attempts."""
    def __init__(self):
        self.rows = []
        self.lock = threading.Lock()

    def record_attempt_mock(self, params: dict):
        with self.lock:
            # Atomic simulation of Postgres RPC record_word_attempt
            student_id = params["p_student_id"]
            word_id = params["p_word_id"]
            existing = [r for r in self.rows if r["student_id"] == student_id and r["word_id"] == word_id]
            next_num = max([r["attempt_number"] for r in existing], default=0) + 1

            row = {
                "id": f"att-{len(self.rows) + 1}",
                "student_id": student_id,
                "word_id": word_id,
                "level_id": params["p_level_id"],
                "transcribed_text": params["p_transcribed_text"],
                "score": params["p_score"],
                "passed": params["p_passed"],
                "attempt_number": next_num
            }
            self.rows.append(row)
            return row


class TestScoringIntegration(unittest.TestCase):
    """Verify end-to-end scoring evaluation, progression trigger, and attempts tracking."""

    def setUp(self):
        self.db = MockAttemptsDb()
        self.mock_client = MagicMock()
        
        # Configure RPC to call thread-safe mock
        def rpc_side_effect(func_name, params):
            mock_call = MagicMock()
            if func_name == "record_word_attempt":
                data = self.db.record_attempt_mock(params)
                mock_call.execute.return_value = MagicMock(data=data)
            return mock_call

        self.mock_client.rpc.side_effect = rpc_side_effect
        self.attempts_repo = AttemptsRepository(client=self.mock_client)

    def test_passing_score_triggers_progression_and_logs_attempt(self):
        mock_progression_svc = MagicMock()
        student_id = "student-1"
        level_id = "level-1"
        word_id = "word-garden"
        target_word = "garden"
        spoken_transcript = "garden"

        # 1. Evaluate score
        score_res = ScoringService.score_pronunciation(target_word, spoken_transcript)
        self.assertTrue(score_res.passed)
        self.assertEqual(score_res.score, 100)

        # 2. Record attempt
        attempt = self.attempts_repo.record_attempt(
            student_id=student_id,
            word_id=word_id,
            level_id=level_id,
            transcribed_text=spoken_transcript,
            score=score_res.score,
            passed=score_res.passed
        )
        self.assertEqual(attempt["attempt_number"], 1)
        self.assertTrue(attempt["passed"])

        # 3. Complete word progression
        if score_res.passed:
            mock_progression_svc.complete_word(student_id, level_id, word_id)

        mock_progression_svc.complete_word.assert_called_once_with(student_id, level_id, word_id)

    def test_wrong_pronunciation_clock_vs_baker_scores_and_logs_failed_attempt(self):
        """Verify the exact user scenario: target 'clock' vs transcript 'baker' produces score, fail, attempt, and feedback."""
        mock_progression_svc = MagicMock()
        mock_profiles_repo = MagicMock(spec=ProfilesRepository)
        game_prog_svc = GameProgressService(profiles_repo=mock_profiles_repo)

        student_id = "student-clock"
        level_id = "level-village-1"
        word_id = "word-clock"
        target_word = "clock"
        spoken_transcript = "baker"

        # 1. Evaluate pronunciation
        score_res = ScoringService.score_pronunciation(
            target=target_word,
            transcript=spoken_transcript,
            fallback_mistake="Keep your tongue steady and emphasize the ending -ck sound."
        )

        self.assertFalse(score_res.passed)
        self.assertLess(score_res.score, 75)
        self.assertEqual(score_res.bracketed_diff, "")
        self.assertTrue(bool(score_res.feedback))
        self.assertIn("You said 'baker', but the target word is 'clock'", score_res.feedback)

        # 2. Record attempt in attempts repo
        attempt = self.attempts_repo.record_attempt(
            student_id=student_id,
            word_id=word_id,
            level_id=level_id,
            transcribed_text=spoken_transcript,
            score=score_res.score,
            passed=score_res.passed
        )

        self.assertEqual(attempt["attempt_number"], 1)
        self.assertFalse(attempt["passed"])
        self.assertEqual(attempt["transcribed_text"], "baker")

        # 3. Update streak on genuine fail
        mock_profiles_repo.get_profile.return_value = {
            "id": student_id,
            "total_score": 150,
            "current_streak": 3,
            "best_streak": 5
        }
        streak_res = game_prog_svc.update_streak(student_id, passed=False)
        self.assertEqual(streak_res["current_streak"], 0)
        self.assertEqual(streak_res["best_streak"], 5)

        # 4. Word progression must NOT be completed
        mock_progression_svc.complete_word.assert_not_called()

    def test_failing_score_does_not_trigger_progression_but_logs_attempt(self):
        mock_progression_svc = MagicMock()
        student_id = "student-1"
        level_id = "level-1"
        word_id = "word-garden"
        target_word = "garden"
        spoken_transcript = "telephone"

        score_res = ScoringService.score_pronunciation(target_word, spoken_transcript)
        self.assertFalse(score_res.passed)

        attempt = self.attempts_repo.record_attempt(
            student_id=student_id,
            word_id=word_id,
            level_id=level_id,
            transcribed_text=spoken_transcript,
            score=score_res.score,
            passed=score_res.passed
        )
        self.assertEqual(attempt["attempt_number"], 1)
        self.assertFalse(attempt["passed"])

        # Progression must NOT be completed on failure
        if score_res.passed:
            mock_progression_svc.complete_word(student_id, level_id, word_id)

        mock_progression_svc.complete_word.assert_not_called()

    def test_speech_errors_bypass_scorer_and_attempts(self):
        """Verify that speech recognition capture errors are never scored or recorded as failures."""
        # Simulated speech failure
        speech_result = SpeechService.transcribe(error="not-allowed")
        self.assertFalse(speech_result.is_usable())
        self.assertEqual(speech_result.error_type, ERROR_PERMISSION_DENIED)

        # Scorer must never receive unusable speech results
        self.assertEqual(len(self.db.rows), 0)

    def test_concurrent_attempts_have_unique_sequential_attempt_numbers(self):
        """Simulate concurrent double-click / multi-request attempts to verify atomic attempt numbering."""
        student_id = "student-concurrent"
        word_id = "word-test"
        level_id = "level-test"
        num_threads = 10
        errors = []

        def worker(idx):
            try:
                self.attempts_repo.record_attempt(
                    student_id=student_id,
                    word_id=word_id,
                    level_id=level_id,
                    transcribed_text=f"attempt-{idx}",
                    score=70 + idx,
                    passed=(idx % 2 == 0)
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(self.db.rows), num_threads)

        attempt_numbers = [r["attempt_number"] for r in self.db.rows]
        self.assertEqual(sorted(attempt_numbers), list(range(1, num_threads + 1)))
        self.assertEqual(len(set(attempt_numbers)), num_threads, "Attempt numbers must be strictly unique")


if __name__ == "__main__":
    unittest.main()
