"""Authorized Word Override service managing instructor password verification and audit logging."""
from __future__ import annotations

import hmac
import hashlib
import logging
from typing import Any, Dict, Optional

from config.settings import get_settings
from repositories.progress_repo import ProgressRepository, get_progress_repository
from services.progression_service import ProgressionService, get_progression_service

logger = logging.getLogger(__name__)

# Default dev password hash for 'teacher123' (used if no custom hash is set in secrets/env)
DEFAULT_DEV_TEACHER_HASH = "cde383eee8ee7a4400adf7a15f716f179a2eb97646b37e089eb8d6d04e663416"


class OverrideService:
    """Provides secure instructor authorization and audit logging for word overrides."""

    def __init__(
        self,
        progress_repo: Optional[ProgressRepository] = None,
        progression_service: Optional[ProgressionService] = None
    ):
        self._progress_repo = progress_repo
        self._progression_service = progression_service

    @property
    def progress_repo(self) -> ProgressRepository:
        if self._progress_repo is not None:
            return self._progress_repo
        return get_progress_repository()

    @property
    def progression_service(self) -> ProgressionService:
        if self._progression_service is not None:
            return self._progression_service
        return get_progression_service()

    def authorize_teacher(self, password_attempt: str) -> bool:
        """
        Verify teacher/instructor authorization credential using constant-time hash comparison.
        Never stores or logs plaintext passwords.
        """
        if not password_attempt or not password_attempt.strip():
            return False

        # Compute SHA-256 of candidate password
        attempt_hash = hashlib.sha256(password_attempt.strip().encode("utf-8")).hexdigest().lower()

        # Retrieve target hash from settings or fallback
        expected_hash = DEFAULT_DEV_TEACHER_HASH.lower()
        try:
            settings = get_settings()
            if settings.teacher_override_hash:
                expected_hash = settings.teacher_override_hash.lower()
        except Exception:
            pass

        # Constant-time comparison to prevent timing side-channels
        is_authorized = hmac.compare_digest(attempt_hash, expected_hash)
        if not is_authorized:
            logger.warning("Failed teacher override authorization attempt.")
        return is_authorized

    def resolve_word_with_override(
        self,
        student_id: str,
        level_id: str,
        word_id: str,
        authorizing_user_id: str,
        reason: str = "Authorized override by instructor"
    ) -> Dict[str, Any]:
        """
        Execute authorized word override:
        1. Mark word_progress status as 'resolved_by_override'
        2. Create immutable audit log entry in override_audit_log
        3. Do NOT record any pronunciation score or reward stats
        4. Permanently remove word from active level queue
        5. Trigger level completion check if all required words are now resolved/completed
        """
        # 1. Update word progress status to 'resolved_by_override'
        existing = self.progress_repo.get_level_word_progress(student_id, level_id)
        current_row = next((r for r in existing if r["word_id"] == word_id), None)
        attempts = current_row.get("attempt_count", 0) if current_row else 0
        q_order = current_row.get("queue_order", 1) if current_row else 1

        self.progress_repo.upsert_word_progress(
            student_id=student_id,
            level_id=level_id,
            word_id=word_id,
            status="resolved_by_override",
            attempt_count=attempts,
            queue_order=q_order
        )

        # 2. Write audit log entry
        audit_record = self.progress_repo.record_override_audit(
            student_id=student_id,
            level_id=level_id,
            word_id=word_id,
            authorized_by=authorizing_user_id,
            reason=reason
        )

        # 3. Re-check level completion status
        queue_state = self.progression_service.get_or_init_level_queue(student_id, level_id)
        level_completion_result = None
        if queue_state["is_level_completed"]:
            level_completion_result = self.progression_service.complete_level(student_id, level_id)

        return {
            "success": True,
            "word_id": word_id,
            "status": "resolved_by_override",
            "audit_id": audit_record.get("id"),
            "is_level_completed": queue_state["is_level_completed"],
            "level_completion": level_completion_result
        }


def get_override_service() -> OverrideService:
    """Helper factory for OverrideService."""
    return OverrideService()
