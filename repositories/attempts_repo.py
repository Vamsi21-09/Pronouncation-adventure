"""Repository for recording and querying student word pronunciation attempts."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from supabase import Client

from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AttemptsRepository:
    """Data access layer for student pronunciation attempts (public.word_attempts)."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def record_attempt(
        self,
        student_id: str,
        word_id: str,
        level_id: str,
        transcribed_text: str,
        score: int,
        passed: bool
    ) -> Dict[str, Any]:
        """
        Records a pronunciation attempt.
        Prefers the atomic Postgres RPC 'record_word_attempt' for race-condition safety,
        with a graceful fallback for environments where RPC is not yet registered.
        """
        params = {
            "p_student_id": student_id,
            "p_word_id": word_id,
            "p_level_id": level_id,
            "p_transcribed_text": transcribed_text,
            "p_score": int(score),
            "p_passed": bool(passed)
        }

        # 1. Try atomic RPC
        try:
            rpc_res = self.client.rpc("record_word_attempt", params).execute()
            if rpc_res and rpc_res.data:
                logger.info(
                    "Recorded attempt via RPC for student %s, word %s: score=%s passed=%s",
                    student_id, word_id, score, passed
                )
                return rpc_res.data
        except Exception as rpc_err:
            logger.debug("RPC record_word_attempt fallback triggered: %s", rpc_err)

        # 2. Fallback: Query max attempt and insert directly
        try:
            existing = (
                self.client.table("word_attempts")
                .select("attempt_number")
                .eq("student_id", student_id)
                .eq("word_id", word_id)
                .order("attempt_number", desc=True)
                .limit(1)
                .execute()
            )
            next_num = 1
            if existing.data and len(existing.data) > 0:
                next_num = int(existing.data[0].get("attempt_number", 0)) + 1

            insert_payload = {
                "student_id": student_id,
                "word_id": word_id,
                "level_id": level_id,
                "transcribed_text": transcribed_text,
                "score": int(score),
                "passed": bool(passed),
                "attempt_number": next_num
            }

            res = self.client.table("word_attempts").insert(insert_payload).execute()
            return res.data[0] if res.data else insert_payload
        except Exception as e:
            logger.error("Failed to record word attempt for student %s: %s", student_id, e)
            raise

    def get_attempts_for_word(self, student_id: str, word_id: str) -> List[Dict[str, Any]]:
        """Retrieve all pronunciation attempts for a given word by student."""
        try:
            res = (
                self.client.table("word_attempts")
                .select("*")
                .eq("student_id", student_id)
                .eq("word_id", word_id)
                .order("attempt_number", desc=False)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error("Failed to fetch word attempts: %s", e)
            return []

    def get_attempts_for_level(self, student_id: str, level_id: str) -> List[Dict[str, Any]]:
        """Retrieve all pronunciation attempts for a given level by student."""
        try:
            res = (
                self.client.table("word_attempts")
                .select("*")
                .eq("student_id", student_id)
                .eq("level_id", level_id)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error("Failed to fetch level attempts: %s", e)
            return []

    def get_student_attempt_stats(self, student_id: str) -> Dict[str, Any]:
        """Aggregate summary statistics of student practice attempts."""
        try:
            res = (
                self.client.table("word_attempts")
                .select("score, passed")
                .eq("student_id", student_id)
                .execute()
            )
            data = res.data or []
            if not data:
                return {"total_attempts": 0, "passed_count": 0, "pass_rate": 0.0, "avg_score": 0.0}

            total = len(data)
            passed = sum(1 for d in data if d.get("passed"))
            avg_score = sum(d.get("score", 0) for d in data) / float(total)

            return {
                "total_attempts": total,
                "passed_count": passed,
                "pass_rate": round((passed / total) * 100.0, 1),
                "avg_score": round(avg_score, 1)
            }
        except Exception as e:
            logger.error("Failed to calculate attempt stats: %s", e)
            return {"total_attempts": 0, "passed_count": 0, "pass_rate": 0.0, "avg_score": 0.0}


def get_attempts_repository(client: Optional[Client] = None) -> AttemptsRepository:
    """Helper factory returning AttemptsRepository instance."""
    return AttemptsRepository(client=client or get_supabase_client())
