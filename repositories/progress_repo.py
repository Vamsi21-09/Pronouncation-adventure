"""Repository for student progression, world locks, in-level word queue, and audit records in Supabase."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ProgressRepositoryError(Exception):
    """Base exception for progress database operations."""
    pass


class ProgressRepository:
    """Encapsulates all database interactions for level locks, world progression, and word queue state."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    # --- Student Level Progress ---

    def get_student_level_progress(self, student_id: str, level_id: str) -> Optional[Dict[str, Any]]:
        """Fetch student progress record for a single level."""
        try:
            response = (
                self.client.table("student_progress")
                .select("*")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query student_progress for student %s level %s: %s", student_id, level_id, e)
            raise ProgressRepositoryError(f"Error fetching level progress: {e}") from e

    def get_all_student_level_progress(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch all level progress records for a student."""
        try:
            response = (
                self.client.table("student_progress")
                .select("*")
                .eq("student_id", student_id)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query all student_progress for student %s: %s", student_id, e)
            raise ProgressRepositoryError(f"Error fetching all level progress: {e}") from e

    def upsert_student_level_progress(
        self,
        student_id: str,
        level_id: str,
        status: str,
        completed_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upsert student progress for a level."""
        payload: Dict[str, Any] = {
            "student_id": student_id,
            "level_id": level_id,
            "status": status,
        }
        if completed_at is not None:
            payload["completed_at"] = completed_at

        try:
            response = (
                self.client.table("student_progress")
                .upsert(payload, on_conflict="student_id,level_id")
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            logger.error("Failed to upsert student_progress for student %s level %s: %s", student_id, level_id, e)
            raise ProgressRepositoryError(f"Error saving level progress: {e}") from e

    # --- World Progress ---

    def get_student_world_progress(self, student_id: str, world_id: str) -> Optional[Dict[str, Any]]:
        """Fetch student progress record for a single world."""
        try:
            response = (
                self.client.table("world_progress")
                .select("*")
                .eq("student_id", student_id)
                .eq("world_id", world_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query world_progress for student %s world %s: %s", student_id, world_id, e)
            raise ProgressRepositoryError(f"Error fetching world progress: {e}") from e

    def get_all_student_world_progress(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch all world progress records for a student."""
        try:
            response = (
                self.client.table("world_progress")
                .select("*")
                .eq("student_id", student_id)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query all world_progress for student %s: %s", student_id, e)
            raise ProgressRepositoryError(f"Error fetching all world progress: {e}") from e

    def upsert_student_world_progress(
        self,
        student_id: str,
        world_id: str,
        status: str,
        unlocked_at: Optional[str] = None,
        completed_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upsert student progress for a world."""
        payload: Dict[str, Any] = {
            "student_id": student_id,
            "world_id": world_id,
            "status": status,
        }
        if unlocked_at is not None:
            payload["unlocked_at"] = unlocked_at
        if completed_at is not None:
            payload["completed_at"] = completed_at

        try:
            response = (
                self.client.table("world_progress")
                .upsert(payload, on_conflict="student_id,world_id")
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            logger.error("Failed to upsert world_progress for student %s world %s: %s", student_id, world_id, e)
            raise ProgressRepositoryError(f"Error saving world progress: {e}") from e

    # --- In-Level Word Progress Queue ---

    def get_level_word_progress(self, student_id: str, level_id: str) -> List[Dict[str, Any]]:
        """Fetch all word_progress records for a student in a specific level."""
        try:
            response = (
                self.client.table("word_progress")
                .select("*")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .order("queue_order")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("Failed to query word_progress for student %s level %s: %s", student_id, level_id, e)
            raise ProgressRepositoryError(f"Error fetching word progress: {e}") from e

    def upsert_word_progress(
        self,
        student_id: str,
        level_id: str,
        word_id: str,
        status: str,
        attempt_count: int,
        queue_order: int
    ) -> Dict[str, Any]:
        """Upsert a single word's in-level queue status, attempts, and position."""
        payload = {
            "student_id": student_id,
            "level_id": level_id,
            "word_id": word_id,
            "status": status,
            "attempt_count": attempt_count,
            "queue_order": queue_order,
        }
        try:
            response = (
                self.client.table("word_progress")
                .upsert(payload, on_conflict="student_id,level_id,word_id")
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            logger.error("Failed to upsert word_progress for student %s word %s: %s", student_id, word_id, e)
            raise ProgressRepositoryError(f"Error saving word progress: {e}") from e

    # --- Override Audit Log ---

    def record_override_audit(
        self,
        student_id: str,
        level_id: str,
        word_id: str,
        authorized_by: str,
        reason: str = "Authorized override by instructor"
    ) -> Dict[str, Any]:
        """Insert an audit entry recording teacher authorization of a word override."""
        payload = {
            "student_id": student_id,
            "level_id": level_id,
            "word_id": word_id,
            "authorized_by": authorized_by,
            "override_type": "authorized_override",
            "reason": reason,
        }
        try:
            response = self.client.table("override_audit_log").insert(payload).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return payload
        except Exception as e:
            logger.warning("Could not write to override_audit_log (continuing word override): %s", e)
            return payload

    def get_override_audit_logs(
        self,
        student_id: Optional[str] = None,
        level_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch audit records for monitoring/reporting."""
        try:
            query = self.client.table("override_audit_log").select("*")
            if student_id:
                query = query.eq("student_id", student_id)
            if level_id:
                query = query.eq("level_id", level_id)
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to fetch override audit logs: %s", e)
            raise ProgressRepositoryError(f"Error querying audit logs: {e}") from e


def get_progress_repository() -> ProgressRepository:
    """Helper factory for ProgressRepository."""
    return ProgressRepository()
