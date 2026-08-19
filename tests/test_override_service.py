"""Unit tests for OverrideService authorization, resolution, and audit trail."""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import MagicMock
from services.override_service import OverrideService, DEFAULT_DEV_TEACHER_HASH


class TestOverrideService(unittest.TestCase):
    """Test suite for teacher password authorization and override resolution."""

    def setUp(self):
        self.mock_progress_repo = MagicMock()
        self.mock_progression_svc = MagicMock()
        self.override_service = OverrideService(
            progress_repo=self.mock_progress_repo,
            progression_service=self.mock_progression_svc
        )

    def test_authorize_teacher_valid_default_password(self):
        # 'teacher123' matches DEFAULT_DEV_TEACHER_HASH
        is_valid = self.override_service.authorize_teacher("teacher123")
        self.assertTrue(is_valid)

    def test_authorize_teacher_invalid_password_rejected(self):
        is_valid = self.override_service.authorize_teacher("wrong_guess")
        self.assertFalse(is_valid)

    def test_authorize_teacher_empty_password_rejected(self):
        is_valid = self.override_service.authorize_teacher("   ")
        self.assertFalse(is_valid)

    def test_resolve_word_with_override_updates_status_and_audit(self):
        self.mock_progress_repo.get_level_word_progress.return_value = [
            {"word_id": "word-1", "status": "pending", "attempt_count": 3, "queue_order": 1}
        ]
        self.mock_progress_repo.record_override_audit.return_value = {"id": "audit-uuid-123"}
        self.mock_progression_svc.get_or_init_level_queue.return_value = {
            "is_level_completed": False,
            "active_queue": []
        }

        res = self.override_service.resolve_word_with_override(
            student_id="student-1",
            level_id="level-1",
            word_id="word-1",
            authorizing_user_id="teacher-uuid",
            reason="Hardware microphone failure"
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "resolved_by_override")
        self.assertEqual(res["audit_id"], "audit-uuid-123")

        # Verify progress updated with resolved_by_override
        self.mock_progress_repo.upsert_word_progress.assert_called_with(
            student_id="student-1",
            level_id="level-1",
            word_id="word-1",
            status="resolved_by_override",
            attempt_count=3,
            queue_order=1
        )

        # Verify audit log was recorded
        self.mock_progress_repo.record_override_audit.assert_called_with(
            student_id="student-1",
            level_id="level-1",
            word_id="word-1",
            authorized_by="teacher-uuid",
            reason="Hardware microphone failure"
        )

    def test_override_triggers_level_completion_when_last_word_resolved(self):
        self.mock_progress_repo.get_level_word_progress.return_value = []
        self.mock_progress_repo.record_override_audit.return_value = {"id": "audit-uuid-456"}
        self.mock_progression_svc.get_or_init_level_queue.return_value = {
            "is_level_completed": True,
            "active_queue": []
        }
        self.mock_progression_svc.complete_level.return_value = {
            "level_id": "level-1",
            "status": "completed",
            "next_level_unlocked": True
        }

        res = self.override_service.resolve_word_with_override(
            student_id="student-1",
            level_id="level-1",
            word_id="word-7",
            authorizing_user_id="teacher-uuid"
        )

        self.assertTrue(res["is_level_completed"])
        self.mock_progression_svc.complete_level.assert_called_once_with("student-1", "level-1")


if __name__ == "__main__":
    unittest.main()
