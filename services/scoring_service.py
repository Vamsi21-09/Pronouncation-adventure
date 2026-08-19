"""Pronunciation scoring, sequence alignment, mistake pattern detection, and feedback service."""
from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import rapidfuzz.fuzz as fuzz

from config.pronunciation_rules import lookup_pattern_rule, PRONUNCIATION_RULES
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiffSegment:
    """Represents a character segment in word alignment."""
    segment: str
    is_match: bool
    target_part: str = ""
    transcript_part: str = ""


@dataclass(frozen=True)
class ScoreResult:
    """Standardized result of pronunciation evaluation."""
    score: int
    passed: bool
    alignment: List[DiffSegment] = field(default_factory=list)
    bracketed_diff: str = ""
    feedback: str = ""
    detected_mistake: Optional[str] = None


def normalize(text: str) -> str:
    """
    Lowercase, strip punctuation, and collapse whitespace.
    """
    if not text:
        return ""
    # Remove all punctuation and symbols, keep only alphanumeric and single spaces
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def award_points(pronunciation_score: int) -> int:
    """
    Deterministic point mapping from 0-100 pronunciation score to adventure score points.
    - Score 95 - 100 -> 100 points
    - Score 85 - 94  -> 85 points
    - Score 75 - 84  -> 70 points
    - Score < 75     -> 0 points
    """
    s = int(pronunciation_score)
    if s >= 95:
        return 100
    if s >= 85:
        return 85
    if s >= 75:
        return 70
    return 0


def is_substantially_different(target: str, transcript: str) -> bool:
    """
    Determines if two words are too dissimilar for letter-by-letter character alignment.
    Used to prevent fabricating character diffs or phoneme diagnoses for unrelated words (e.g. CLOCK vs BRAIN).
    """
    t_norm = normalize(target)
    tr_norm = normalize(transcript)
    if not t_norm or not tr_norm:
        return True

    matcher = difflib.SequenceMatcher(None, t_norm, tr_norm)
    ratio = matcher.ratio()

    len_diff = abs(len(t_norm) - len(tr_norm))
    max_len = max(len(t_norm), len(tr_norm))

    # Low similarity ratio or large length mismatch on words
    if ratio < 0.45 or (max_len > 3 and ratio < 0.50 and len_diff >= 3):
        return True

    return False


def align_words(target: str, transcript: str) -> Tuple[List[DiffSegment], str]:
    """
    Align target word with spoken transcript using SequenceMatcher.
    Produces a list of DiffSegments and a bracketed diff string (e.g. S[CH]OOL).
    For substantially different words, avoids fabricating character diffs.
    """
    target_norm = normalize(target)
    transcript_norm = normalize(transcript)

    if not target_norm:
        return [], ""

    if not transcript_norm:
        seg = DiffSegment(segment=target_norm, is_match=False, target_part=target_norm, transcript_part="")
        return [seg], f"[{target_norm.upper()}]"

    # If words are substantially different, do not fabricate character diff
    if is_substantially_different(target_norm, transcript_norm):
        seg = DiffSegment(segment=target_norm, is_match=False, target_part=target_norm, transcript_part=transcript_norm)
        return [seg], ""

    matcher = difflib.SequenceMatcher(None, target_norm, transcript_norm)
    segments: List[DiffSegment] = []
    diff_chars: List[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        target_chunk = target_norm[i1:i2]
        trans_chunk = transcript_norm[j1:j2]

        if tag == "equal":
            segments.append(DiffSegment(
                segment=target_chunk,
                is_match=True,
                target_part=target_chunk,
                transcript_part=trans_chunk
            ))
            diff_chars.append(target_chunk.upper())
        elif tag == "replace":
            segments.append(DiffSegment(
                segment=target_chunk,
                is_match=False,
                target_part=target_chunk,
                transcript_part=trans_chunk
            ))
            diff_chars.append(f"[{target_chunk.upper()}]")
        elif tag == "delete":
            # Chars missing from spoken transcript
            segments.append(DiffSegment(
                segment=target_chunk,
                is_match=False,
                target_part=target_chunk,
                transcript_part=""
            ))
            diff_chars.append(f"[{target_chunk.upper()}]")
        elif tag == "insert":
            # Extra sounds/chars spoken that are not in target word
            segments.append(DiffSegment(
                segment=trans_chunk,
                is_match=False,
                target_part="",
                transcript_part=trans_chunk
            ))

    bracketed_diff = "".join(diff_chars)
    return segments, bracketed_diff


def detect_common_mistake(
    target: str,
    transcript: str,
    alignment: List[DiffSegment],
    fallback_mistake: Optional[str] = None
) -> Optional[str]:
    """
    Detects if mismatched segments correspond to common phonetic / spelling patterns.
    Only uses curated mistake hints when supported by the actual transcript/alignment.
    Never invents or fabricates mistakes for unrelated words.
    """
    target_norm = normalize(target)
    transcript_norm = normalize(transcript)

    if not transcript_norm or target_norm == transcript_norm:
        return None

    # 1. If words are substantially different, do not fabricate mistake diagnoses
    if is_substantially_different(target_norm, transcript_norm):
        return None

    # 2. Check mismatched segments against known pattern rules
    mismatched_target_parts = [seg.target_part for seg in alignment if not seg.is_match and seg.target_part]

    for part in mismatched_target_parts:
        rule_hint = lookup_pattern_rule(part)
        if rule_hint:
            return f"You may have missed the '{part}' sound. {rule_hint}"

    # 3. Check if target word contains a digraph/pattern where letters were omitted or altered
    for pattern, explanation in PRONUNCIATION_RULES.items():
        if pattern in target_norm:
            if pattern not in transcript_norm or any(ch in mismatched_target_parts for ch in pattern):
                return f"You may have missed the '{pattern}' sound. {explanation}"

    # 4. Fallback to curated word metadata ONLY when the actual transcript supports it
    if fallback_mistake and fallback_mistake.strip():
        fb_clean = fallback_mistake.strip()
        fb_lower = fb_clean.lower()

        # Extract quoted words/letters from the mistake metadata
        quoted_items = re.findall(r"['\"]([a-zA-Z0-9_-]+)['\"]", fb_clean)
        
        if quoted_items:
            # Trigger if student actually said a named word (e.g. said 'cock')
            if any(normalize(q) == transcript_norm for q in quoted_items):
                return fb_clean
            # Or if student specifically missed a named sound (e.g. missed 'l')
            if any(normalize(q) in mismatched_target_parts for q in quoted_items):
                return fb_clean
        else:
            # If no quotes, check if any mismatched part is mentioned in the mistake hint
            if any(part in fb_lower for part in mismatched_target_parts):
                return fb_clean

    return None


class ScoringService:
    """Encapsulates pronunciation scoring and feedback generation."""

    @classmethod
    def score_pronunciation(
        cls,
        target: str,
        transcript: str,
        pass_threshold: Optional[int] = None,
        short_word_threshold: Optional[int] = None,
        fallback_mistake: Optional[str] = None
    ) -> ScoreResult:
        """
        Evaluates student speech against target word.
        - Exact match -> 100, Passed
        - Short words (<= 3 chars) -> Strict branch (single letter difference fails)
        - Longer words (> 3 chars) -> RapidFuzz blended ratio with non-linear curve
        """
        target_norm = normalize(target)
        transcript_norm = normalize(transcript)

        # Resolve thresholds
        settings = get_settings()
        effective_threshold = pass_threshold if pass_threshold is not None else settings.pronunciation_pass_threshold
        effective_short_threshold = short_word_threshold if short_word_threshold is not None else settings.short_word_pass_threshold

        # Alignment and mistake detection
        alignment, bracketed_diff = align_words(target_norm, transcript_norm)
        detected_mistake = detect_common_mistake(target_norm, transcript_norm, alignment, fallback_mistake)

        # 1. Empty transcript handling
        if not transcript_norm:
            return ScoreResult(
                score=0,
                passed=False,
                alignment=alignment,
                bracketed_diff=bracketed_diff,
                feedback="No speech was detected. Please check your microphone and try speaking again!",
                detected_mistake=None
            )

        # 2. Exact match (case & punctuation insensitive)
        if target_norm == transcript_norm:
            return ScoreResult(
                score=100,
                passed=True,
                alignment=alignment,
                bracketed_diff=target_norm.upper(),
                feedback="🌟 Outstanding! Perfect pronunciation!",
                detected_mistake=None
            )

        # 3. Explicit Short-Word Branch (length <= 3 chars, e.g. 'cat', 'sun', 'dog', 'fox')
        if len(target_norm) <= 3:
            matcher = difflib.SequenceMatcher(None, target_norm, transcript_norm)
            ratio = matcher.ratio()

            if len(transcript_norm) == len(target_norm):
                # Substitution: e.g. cat vs hat (1 char difference out of 3)
                score = int(round(ratio * 70.0))
            else:
                # Length mismatch: e.g. cat vs cats
                score = int(round(ratio * 75.0))

            score = max(0, min(100, score))
            passed = score >= effective_short_threshold

            feedback = cls._generate_feedback(target, transcript, score, passed, detected_mistake)
            return ScoreResult(
                score=score,
                passed=passed,
                alignment=alignment,
                bracketed_diff=bracketed_diff,
                feedback=feedback,
                detected_mistake=detected_mistake
            )

        # 4. Standard Word Branch (> 3 chars)
        ratio = fuzz.ratio(target_norm, transcript_norm)
        partial = fuzz.partial_ratio(target_norm, transcript_norm)

        # Length completeness weighting: prevents truncated prefixes (e.g. 'cobble' for 'cobblestone') from passing
        len_ratio = min(len(target_norm), len(transcript_norm)) / max(len(target_norm), len(transcript_norm))
        effective_partial = partial * len_ratio

        # Blend: 85% whole-word Levenshtein ratio + 15% length-weighted partial ratio
        blended = (0.85 * ratio) + (0.15 * effective_partial)

        # Non-linear curve
        scaled = (blended / 100.0) ** 1.05 * 100.0
        score = int(round(max(0.0, min(100.0, scaled))))
        passed = score >= effective_threshold

        feedback = cls._generate_feedback(target, transcript, score, passed, detected_mistake)

        return ScoreResult(
            score=score,
            passed=passed,
            alignment=alignment,
            bracketed_diff=bracketed_diff,
            feedback=feedback,
            detected_mistake=detected_mistake
        )

    @staticmethod
    def award_points(pronunciation_score: int) -> int:
        """Helper pointing to pure award_points function."""
        return award_points(pronunciation_score)

    @classmethod
    def _generate_feedback(
        cls,
        target: str,
        transcript: str,
        score: int,
        passed: bool,
        detected_mistake: Optional[str] = None
    ) -> str:
        """
        Builds encouraging child-friendly feedback without harsh or fabricated language.
        """
        target_norm = normalize(target)
        transcript_norm = normalize(transcript)

        if not transcript_norm:
            return "No speech was detected. Please check your microphone and try speaking again!"

        if target_norm == transcript_norm:
            return "🌟 Outstanding! Perfect pronunciation!"

        # Hierarchy 1: Substantially different words
        if is_substantially_different(target_norm, transcript_norm):
            return (
                f"Nice try! You said '{transcript.strip()}', but the target word is '{target.strip()}'. "
                f"Try saying '{target.strip()}' slowly."
            )

        # Hierarchy 2: Similar words with passing score
        if passed:
            if score >= 95:
                base_msg = "🌟 Outstanding! Perfect pronunciation!"
            elif score >= 85:
                base_msg = "🎉 Excellent job! You pronounced the word very clearly."
            else:
                base_msg = "👍 Great effort! You successfully passed this word."
        else:
            # Hierarchy 3: Similar words with failing score
            if score >= 55:
                base_msg = "💪 Good try! Take a look at the highlighted letters and give it another shot."
            else:
                base_msg = "🌱 Keep practicing! Speak slowly and listen to each part of the word."

        if detected_mistake and score < 95:
            return f"{base_msg}\n\n💡 **Here's what we noticed:** {detected_mistake}"

        return base_msg


def get_scoring_service() -> ScoringService:
    """Helper factory for ScoringService."""
    return ScoringService()
