"""Speech recognition service and standardized transcript result interface (Web Speech + Server Fallback)."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Standardized error categories
ERROR_PERMISSION_DENIED = "permission_denied"
ERROR_NO_SPEECH = "no_speech"
ERROR_AUDIO_TIMEOUT = "audio_timeout"
ERROR_UNSUPPORTED_BROWSER = "unsupported_browser"
ERROR_NETWORK = "network_error"
ERROR_API_FAILURE = "api_error"

PROVIDER_WHISPER = "whisper_tiny_en"
PROVIDER_WEB_SPEECH = "whisper_tiny_en"  # Aliased for backward compatibility
PROVIDER_SERVER_FALLBACK = "fallback_speech_recognition"

FRIENDLY_ERROR_MESSAGES = {
    ERROR_PERMISSION_DENIED: (
        "Microphone access was blocked. Please click the lock icon 🔒 in your browser address bar "
        "and select 'Allow' for Microphone, then refresh."
    ),
    ERROR_NO_SPEECH: (
        "I didn't hear you. Click 'Speak Now' and speak clearly when you are ready."
    ),
    ERROR_AUDIO_TIMEOUT: (
        "Listening ended. Click 'Speak Now' when you are ready to speak."
    ),
    ERROR_UNSUPPORTED_BROWSER: (
        "Speech recognition is not available in this browser. Please use Chrome or Edge."
    ),
    ERROR_NETWORK: (
        "Could not connect to speech recognition service. Please check your internet connection and try again."
    ),
    ERROR_API_FAILURE: (
        "Speech could not be processed. Please try speaking again."
    ),
}


@dataclass(frozen=True)
class TranscriptResult:
    """Standardized representation of speech recognition output."""
    text: str = ""
    confidence: float = 1.0
    provider_used: str = PROVIDER_WHISPER
    is_success: bool = True
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[int] = None
    attempt_id: Optional[int] = None

    def is_usable(self) -> bool:
        """True if speech was successfully captured and transcribed without errors."""
        return self.is_success and bool(self.text.strip()) and self.error is None


class SpeechService:
    """Encapsulates speech recognition result formatting and error normalization."""

    @staticmethod
    def map_web_speech_error(raw_error: str) -> tuple[str, str]:
        """
        Map speech capture and recognition error codes to standard error_type and friendly student guidance.
        """
        err_lower = (raw_error or "").strip().lower()
        if "not-allowed" in err_lower or "permission" in err_lower or "denied" in err_lower:
            err_type = ERROR_PERMISSION_DENIED
        elif "no-speech" in err_lower or "empty" in err_lower:
            err_type = ERROR_NO_SPEECH
        elif "timeout" in err_lower:
            err_type = ERROR_AUDIO_TIMEOUT
        elif "network" in err_lower:
            err_type = ERROR_NETWORK
        elif "unsupported" in err_lower or "not-supported" in err_lower:
            err_type = ERROR_UNSUPPORTED_BROWSER
        else:
            err_type = ERROR_API_FAILURE

        friendly_msg = FRIENDLY_ERROR_MESSAGES.get(err_type, FRIENDLY_ERROR_MESSAGES[ERROR_API_FAILURE])
        return err_type, friendly_msg

    @staticmethod
    def get_phonetic_skeleton(word: str) -> str:
        """
        Extract consonant-vowel skeleton grouping phonetically similar consonants
        (e.g., dental /t/ and /d/, labials /p/ and /b/, velars /k/ and /g/).
        """
        import re
        w = re.sub(r"[^a-zA-Z]", "", word or "").lower()
        if not w:
            return ""

        skeleton = []
        for ch in w:
            if ch in "aeiouy":
                skeleton.append(ch)
            elif ch in "bpfv":
                skeleton.append("1")
            elif ch in "cgjkqsxz":
                skeleton.append("2")
            elif ch in "dt":
                skeleton.append("3")
            elif ch == "l":
                skeleton.append("4")
            elif ch in "mn":
                skeleton.append("5")
            elif ch == "r":
                skeleton.append("6")
            else:
                skeleton.append(ch)
        
        skel_str = "".join(skeleton)
        return re.sub(r"([1-6])\1+", r"\1", skel_str)

    @classmethod
    def extract_vocabulary_candidate(cls, raw_text: str, target_word: str) -> tuple[str, str, bool]:
        """
        If target_word is a single vocabulary word, extracts the best candidate token from
        a potentially hallucinated or multi-word transcript.
        If target_word is a sentence, preserves the full transcript.
        
        Returns:
            (candidate_word, reason_string, is_hallucination)
        """
        import re
        from rapidfuzz.distance import Levenshtein

        clean_target = re.sub(r"[^a-zA-Z0-9]", "", target_word or "").lower()
        target_tokens = (target_word or "").strip().split()
        
        # Sentence Mode: preserve full transcript
        if len(target_tokens) > 1:
            clean_full = re.sub(r"[^a-zA-Z0-9\s]", "", raw_text or "").lower().strip()
            clean_full = re.sub(r"\s+", " ", clean_full)
            return clean_full, "Sentence mode: preserved full transcript", False

        # Single Word Mode
        tokens = re.sub(r"[^a-zA-Z0-9\s]", "", raw_text or "").lower().strip().split()
        if not tokens:
            return "", "Empty transcript", False
        if len(tokens) == 1:
            return tokens[0], "Single word exact output", False

        # Article filtering (e.g., "the bat" -> "bat", "a bad" -> "bad")
        if len(tokens) == 2 and tokens[0] in ("a", "an", "the", "to"):
            return tokens[1], "Leading article stripped", False

        target_skel = cls.get_phonetic_skeleton(clean_target)

        # Multi-word transcript for single-word target: Rank candidates against clean_target
        scored_tokens = []
        for tok in tokens:
            if tok in ("a", "an", "the", "is", "it"):
                continue
            dist_lex = Levenshtein.distance(clean_target, tok)
            max_len_lex = max(len(clean_target), len(tok))
            sim_lex = (1.0 - (dist_lex / max_len_lex)) if max_len_lex > 0 else 0.0

            tok_skel = cls.get_phonetic_skeleton(tok)
            dist_phon = Levenshtein.distance(target_skel, tok_skel)
            max_len_phon = max(len(target_skel), len(tok_skel))
            sim_phon = (1.0 - (dist_phon / max_len_phon)) if max_len_phon > 0 else 0.0

            combined = (sim_lex * 0.5) + (sim_phon * 0.5)
            scored_tokens.append((combined, sim_lex, sim_phon, tok))

        if not scored_tokens:
            return "", "No valid tokens", True

        scored_tokens.sort(key=lambda x: x[0], reverse=True)
        best_combined, best_lex, best_phon, best_tok = scored_tokens[0]

        # If short phrase (2-3 words) and candidate meets threshold
        if len(tokens) <= 3 and best_combined >= 0.35:
            return best_tok, f"Best candidate '{best_tok}' (lex: {int(best_lex*100)}%, phon: {int(best_phon*100)}%)", False

        # If long multi-word sentence (4+ words), only accept if high similarity
        if len(tokens) > 3 and (best_lex >= 0.80 or (len(clean_target) <= 4 and best_lex >= 0.66 and best_phon >= 0.80)):
            return best_tok, f"Candidate extracted from phrase '{best_tok}'", False

        # Otherwise ungrounded hallucination
        return "", f"Ungrounded hallucination filtered (best match '{best_tok}' score: {int(best_combined*100)}%)", True

    @classmethod
    def process_web_speech_result(
        cls,
        raw_text: Optional[str],
        confidence: Optional[float] = None,
        raw_error: Optional[str] = None,
        provider: str = PROVIDER_WHISPER,
        timestamp: Optional[int] = None,
        attempt_id: Optional[Any] = None,
        target_word: Optional[str] = None
    ) -> TranscriptResult:
        """
        Process output from client-side Whisper AI bridge into a TranscriptResult.
        """
        if raw_error:
            err_type, friendly_msg = cls.map_web_speech_error(raw_error)
            logger.info("[WHISPER_TRACE] python_received error: attempt_id=%s, error_type=%s, raw_error=%s", attempt_id, err_type, raw_error)
            return TranscriptResult(
                text="",
                confidence=0.0,
                provider_used=provider,
                is_success=False,
                error=friendly_msg,
                error_type=err_type,
                timestamp=timestamp,
                attempt_id=attempt_id
            )

        clean_text = (raw_text or "").strip().lower()
        if not clean_text:
            logger.info("[WHISPER_TRACE] python_received empty text: attempt_id=%s", attempt_id)
            return TranscriptResult(
                text="",
                confidence=0.0,
                provider_used=provider,
                is_success=False,
                error=FRIENDLY_ERROR_MESSAGES[ERROR_NO_SPEECH],
                error_type=ERROR_NO_SPEECH,
                timestamp=timestamp,
                attempt_id=attempt_id
            )

        # Apply target-aware candidate extraction if target_word is provided
        if target_word:
            candidate, reason, is_hallucination = cls.extract_vocabulary_candidate(clean_text, target_word)
            logger.info("[WHISPER_TRACE] candidate_extracted: raw='%s', candidate='%s', reason='%s'", clean_text, candidate, reason)
            if is_hallucination or not candidate:
                return TranscriptResult(
                    text="",
                    confidence=0.0,
                    provider_used=provider,
                    is_success=False,
                    error="I couldn't clearly recognize the word. Please try speaking again.",
                    error_type=ERROR_NO_SPEECH,
                    timestamp=timestamp,
                    attempt_id=attempt_id
                )
            clean_text = candidate

        # Normalize confidence to [0.0, 1.0]
        conf = 1.0
        if confidence is not None:
            try:
                conf = max(0.0, min(1.0, float(confidence)))
            except (ValueError, TypeError):
                conf = 1.0

        logger.info("[WHISPER_TRACE] python_received success: attempt_id=%s, transcript='%s', conf=%.2f", attempt_id, clean_text, conf)
        return TranscriptResult(
            text=clean_text,
            confidence=conf,
            provider_used=provider,
            is_success=True,
            error=None,
            error_type=None,
            timestamp=timestamp,
            attempt_id=attempt_id
        )

    @classmethod
    def process_whisper_result(
        cls,
        raw_text: Optional[str],
        confidence: Optional[float] = None,
        raw_error: Optional[str] = None,
        provider: str = PROVIDER_WHISPER,
        timestamp: Optional[int] = None,
        attempt_id: Optional[int] = None
    ) -> TranscriptResult:
        """Alias for process_web_speech_result with explicit Whisper naming."""
        return cls.process_web_speech_result(
            raw_text=raw_text,
            confidence=confidence,
            raw_error=raw_error,
            provider=provider,
            timestamp=timestamp,
            attempt_id=attempt_id
        )

    @classmethod
    def transcribe(
        cls,
        raw_text: Optional[str] = None,
        text: Optional[str] = None,
        confidence: Optional[float] = None,
        error: Optional[str] = None,
        raw_error: Optional[str] = None,
        provider: str = PROVIDER_WEB_SPEECH,
        timestamp: Optional[int] = None
    ) -> TranscriptResult:
        """
        Direct convenience helper mapping speech recognition inputs to TranscriptResult.
        """
        actual_text = raw_text if raw_text is not None else text
        actual_error = raw_error if raw_error is not None else error
        return cls.process_web_speech_result(
            raw_text=actual_text,
            confidence=confidence,
            raw_error=actual_error,
            provider=provider,
            timestamp=timestamp
        )

    @classmethod
    def transcribe_audio_bytes(
        cls,
        audio_bytes: Optional[bytes],
        language: str = "en-US",
        recognizer: Optional[Any] = None
    ) -> TranscriptResult:
        """
        Transcribe raw audio bytes using SpeechRecognition fallback provider (Stage B).
        Wrapped in comprehensive try/except to never crash or hang the UI.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return TranscriptResult(
                text="",
                confidence=0.0,
                provider_used=PROVIDER_SERVER_FALLBACK,
                is_success=False,
                error=FRIENDLY_ERROR_MESSAGES[ERROR_NO_SPEECH],
                error_type=ERROR_NO_SPEECH
            )

        try:
            import speech_recognition as sr

            rec = recognizer or sr.Recognizer()
            audio_file = io.BytesIO(audio_bytes)

            with sr.AudioFile(audio_file) as source:
                audio_data = rec.record(source)

            transcribed_text = rec.recognize_google(audio_data, language=language)
            clean_text = (transcribed_text or "").strip().lower()

            if not clean_text:
                return TranscriptResult(
                    text="",
                    confidence=0.0,
                    provider_used=PROVIDER_SERVER_FALLBACK,
                    is_success=False,
                    error=FRIENDLY_ERROR_MESSAGES[ERROR_NO_SPEECH],
                    error_type=ERROR_NO_SPEECH
                )

            return TranscriptResult(
                text=clean_text,
                confidence=1.0,
                provider_used=PROVIDER_SERVER_FALLBACK,
                is_success=True,
                error=None,
                error_type=None
            )

        except Exception as e:
            err_str = str(e).lower()
            logger.warning("Fallback speech recognition exception: %s", e)
            if "unknownvalueerror" in type(e).__name__.lower() or "not understand" in err_str:
                return TranscriptResult(
                    text="",
                    confidence=0.0,
                    provider_used=PROVIDER_SERVER_FALLBACK,
                    is_success=False,
                    error=FRIENDLY_ERROR_MESSAGES[ERROR_NO_SPEECH],
                    error_type=ERROR_NO_SPEECH
                )
            elif "requesterror" in type(e).__name__.lower() or "connection" in err_str:
                return TranscriptResult(
                    text="",
                    confidence=0.0,
                    provider_used=PROVIDER_SERVER_FALLBACK,
                    is_success=False,
                    error=FRIENDLY_ERROR_MESSAGES[ERROR_NETWORK],
                    error_type=ERROR_NETWORK
                )
            else:
                return TranscriptResult(
                    text="",
                    confidence=0.0,
                    provider_used=PROVIDER_SERVER_FALLBACK,
                    is_success=False,
                    error=FRIENDLY_ERROR_MESSAGES[ERROR_API_FAILURE],
                    error_type=ERROR_API_FAILURE
                )


def get_speech_service() -> SpeechService:
    """Helper factory for SpeechService."""
    return SpeechService()
