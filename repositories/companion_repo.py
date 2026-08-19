"""Repository for student companion state and idempotent companion XP events."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class CompanionRepositoryError(Exception):
    """Base exception for companion repository operations."""
    pass


class CompanionRepository:
    """Manages student companion state and idempotent XP award logs in Supabase."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_companion(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch companion for a student."""
        try:
            response = self.client.table("student_companion").select("*").eq("student_id", student_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query student_companion for student %s: %s", student_id, e)
            raise CompanionRepositoryError(f"Error fetching companion: {e}") from e

    def upsert_companion(self, student_id: str, stage: str, xp: int) -> Dict[str, Any]:
        """
        Idempotently insert or update student companion record.
        Checks for existing row first to use direct UPDATE, or INSERT with race-condition catch.
        """
        payload = {
            "student_id": student_id,
            "stage": stage,
            "xp": max(0, xp),
        }
        try:
            existing = self.get_companion(student_id)
            if existing:
                res = (
                    self.client.table("student_companion")
                    .update({"stage": stage, "xp": max(0, xp)})
                    .eq("student_id", student_id)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    return res.data[0]
                return {**existing, "stage": stage, "xp": max(0, xp)}

            # Try insert
            try:
                res = self.client.table("student_companion").insert(payload).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
                return payload
            except Exception as insert_err:
                err_str = str(insert_err).lower()
                if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                    # Race condition won by another request
                    up_res = (
                        self.client.table("student_companion")
                        .update({"stage": stage, "xp": max(0, xp)})
                        .eq("student_id", student_id)
                        .execute()
                    )
                    if up_res.data and len(up_res.data) > 0:
                        return up_res.data[0]
                raise insert_err
        except Exception as e:
            logger.error("Failed to upsert student_companion for student %s: %s", student_id, e)
            raise CompanionRepositoryError(f"Error saving companion: {e}") from e

    def has_xp_event(self, student_id: str, event_key: str) -> bool:
        """Check if an XP event has already been recorded for idempotency."""
        try:
            response = (
                self.client.table("companion_xp_events")
                .select("id")
                .eq("student_id", student_id)
                .eq("event_key", event_key)
                .execute()
            )
            return bool(response.data and len(response.data) > 0)
        except Exception as e:
            logger.error("Failed to query companion_xp_events: %s", e)
            raise CompanionRepositoryError(f"Error checking xp event: {e}") from e

    def record_xp_event(self, student_id: str, event_key: str, xp_awarded: int) -> bool:
        """
        Record an XP event. Returns True if inserted successfully, False if already exists (idempotent).
        """
        payload = {
            "student_id": student_id,
            "event_key": event_key,
            "xp_awarded": xp_awarded,
        }
        try:
            response = self.client.table("companion_xp_events").insert(payload).execute()
            return bool(response.data and len(response.data) > 0)
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate" in err_str or "unique" in err_str or "23505" in err_str:
                logger.info("XP event %s already recorded for student %s.", event_key, student_id)
                return False
            logger.error("Failed to insert companion_xp_event: %s", e)
            raise CompanionRepositoryError(f"Error recording xp event: {e}") from e


def get_companion_repository() -> CompanionRepository:
    return CompanionRepository()
