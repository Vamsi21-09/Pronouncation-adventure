"""Unit tests for Pronunciation Scoring Service, sequence alignment, mistake detection, and short-word guardrails."""
from __future__ import annotations

import unittest
from services.scoring_service import (
    ScoringService,
    ScoreResult,
    DiffSegment,
    normalize,
    align_words,
    detect_common_mistake,
    is_substantially_different,
)


class TestScoringServiceUnit(unittest.TestCase):
    """Test pure scoring logic independent of Streamlit or database."""

    # 1. Normalization Tests
    def test_normalize_strips_punctuation_and_whitespace(self):
        self.assertEqual(normalize("  Hello, World!  "), "hello world")
        self.assertEqual(normalize("Garden..."), "garden")
        self.assertEqual(normalize("It's a cat-dog!"), "its a catdog")
        self.assertEqual(normalize(""), "")

    # 2. Sequence Alignment & Substantially Different Words
    def test_align_words_exact_match(self):
        segments, diff_str = align_words("garden", "garden")
        self.assertEqual(diff_str, "GARDEN")
        self.assertTrue(all(s.is_match for s in segments))

    def test_align_words_known_substitution(self):
        _, diff_str = align_words("school", "skool")
        self.assertIn("[CH]", diff_str)
        self.assertEqual(diff_str, "S[CH]OOL")

    def test_align_words_vowel_substitution(self):
        _, diff_str = align_words("garden", "gardin")
        self.assertEqual(diff_str, "GARD[E]N")

    def test_align_words_empty_transcript(self):
        segments, diff_str = align_words("forest", "")
        self.assertEqual(diff_str, "[FOREST]")
        self.assertFalse(segments[0].is_match)

    def test_substantially_different_words_no_fabricated_diff(self):
        """When words are completely different (CLOCK vs BRAIN), do not force a character-level diff."""
        self.assertTrue(is_substantially_different("clock", "brain"))
        segments, diff_str = align_words("clock", "brain")
        self.assertEqual(diff_str, "")

    # 3. Common Mistake Rule Table Detection & Safety Hierarchy
    def test_detect_common_mistake_digraph_rules(self):
        # Pattern 1: 'th' rule
        alignment_th, _ = align_words("three", "tree")
        tip_th = detect_common_mistake("three", "tree", alignment_th)
        self.assertIsNotNone(tip_th)
        self.assertIn("th", tip_th.lower())

        # Pattern 2: 'ch' rule (school vs sool)
        alignment_ch, _ = align_words("school", "sool")
        tip_ch = detect_common_mistake("school", "sool", alignment_ch)
        self.assertIsNotNone(tip_ch)
        self.assertIn("ch", tip_ch.lower())

        # Pattern 3: 'sh' rule
        alignment_sh, _ = align_words("shadow", "sadow")
        tip_sh = detect_common_mistake("shadow", "sadow", alignment_sh)
        self.assertIsNotNone(tip_sh)
        self.assertIn("sh", tip_sh.lower())

        # Pattern 4: 'wr' silent letter rule
        alignment_wr, _ = align_words("write", "rite")
        tip_wr = detect_common_mistake("write", "rite", alignment_wr)
        self.assertIsNotNone(tip_wr)
        self.assertIn("wr", tip_wr.lower())

    def test_detect_common_mistake_never_claims_unsupported_mistake(self):
        """When student says 'brain' for 'clock', never blindly claim 'cock' or missing 'l'."""
        alignment, _ = align_words("clock", "brain")
        tip = detect_common_mistake(
            target="clock",
            transcript="brain",
            alignment=alignment,
            fallback_mistake="Missing the 'l' blend and saying 'cock'."
        )
        self.assertIsNone(tip)

    def test_detect_common_mistake_uses_curated_when_actually_supported(self):
        """When student actually says 'cock' for 'clock', the curated hint is triggered legitimately."""
        alignment, _ = align_words("clock", "cock")
        tip = detect_common_mistake(
            target="clock",
            transcript="cock",
            alignment=alignment,
            fallback_mistake="Missing the 'l' blend and saying 'cock'."
        )
        self.assertIsNotNone(tip)
        self.assertIn("cock", tip)

    # 4. End-to-End Scoring & Feedback Evaluation
    def test_clock_vs_brain_generic_comparison_feedback(self):
        """Target CLOCK vs Transcript BRAIN: low score, failed, generic comparison feedback without false claims."""
        res = ScoringService.score_pronunciation(
            target="clock",
            transcript="brain",
            fallback_mistake="Missing the 'l' blend and saying 'cock'."
        )
        self.assertLess(res.score, 75)
        self.assertFalse(res.passed)
        self.assertEqual(res.bracketed_diff, "")
        self.assertIn("You said 'brain', but the target word is 'clock'", res.feedback)
        self.assertNotIn("cock", res.feedback.lower())

    def test_school_vs_sool_ch_guidance(self):
        """Target SCHOOL vs Transcript SOOL: CH-related feedback appears with bracketed diff."""
        res = ScoringService.score_pronunciation(target="school", transcript="sool")
        self.assertEqual(res.bracketed_diff, "S[CH]OOL")
        self.assertIn("ch", res.feedback.lower())

    def test_clock_vs_clok_close_pronunciation(self):
        """Target CLOCK vs Transcript CLOK: appropriate alignment appears."""
        res = ScoringService.score_pronunciation(target="clock", transcript="clok")
        self.assertEqual(res.bracketed_diff, "CLO[C]K")

    def test_score_exact_match(self):
        res = ScoringService.score_pronunciation("adventure", "adventure")
        self.assertEqual(res.score, 100)
        self.assertTrue(res.passed)
        self.assertEqual(res.bracketed_diff, "ADVENTURE")
        self.assertIn("Outstanding", res.feedback)

    def test_score_minor_pronunciation_typo_passes(self):
        res = ScoringService.score_pronunciation("garden", "gardin", pass_threshold=75)
        self.assertGreaterEqual(res.score, 75)
        self.assertTrue(res.passed)
        self.assertEqual(res.bracketed_diff, "GARD[E]N")

    def test_score_garbled_or_completely_different_word(self):
        res = ScoringService.score_pronunciation("butterfly", "telephone", pass_threshold=75)
        self.assertLess(res.score, 50)
        self.assertFalse(res.passed)
        self.assertEqual(res.bracketed_diff, "")
        self.assertIn("You said 'telephone', but the target word is 'butterfly'", res.feedback)

    def test_score_empty_transcript_safe(self):
        res = ScoringService.score_pronunciation("forest", "")
        self.assertEqual(res.score, 0)
        self.assertFalse(res.passed)
        self.assertIn("No speech", res.feedback)

    # 5. Explicit Short-Word Guardrail Tests (<= 3 characters)
    def test_short_word_rule_single_letter_substitution_must_fail(self):
        res_hat = ScoringService.score_pronunciation("cat", "hat", pass_threshold=75, short_word_threshold=90)
        self.assertLessEqual(res_hat.score, 50)
        self.assertFalse(res_hat.passed, "'hat' must NOT pass when target is 'cat'")

        res_fog = ScoringService.score_pronunciation("dog", "fog", pass_threshold=75, short_word_threshold=90)
        self.assertLessEqual(res_fog.score, 50)
        self.assertFalse(res_fog.passed, "'fog' must NOT pass when target is 'dog'")

        res_run = ScoringService.score_pronunciation("sun", "run", pass_threshold=75, short_word_threshold=90)
        self.assertLessEqual(res_run.score, 50)
        self.assertFalse(res_run.passed, "'run' must NOT pass when target is 'sun'")

    def test_two_letter_words_guardrails(self):
        """Verify that 2-letter words strictly fail on near-misses and length additions."""
        # 'at' vs 'cat' (added letter)
        res_at_cat = ScoringService.score_pronunciation("at", "cat", short_word_threshold=90)
        self.assertFalse(res_at_cat.passed)
        self.assertLess(res_at_cat.score, 80)

        # 'in' vs 'pin' (added letter)
        res_in_pin = ScoringService.score_pronunciation("in", "pin", short_word_threshold=90)
        self.assertFalse(res_in_pin.passed)

        # 'go' vs 'no' (substitution)
        res_go_no = ScoringService.score_pronunciation("go", "no", short_word_threshold=90)
        self.assertFalse(res_go_no.passed)

        # 'up' vs 'cup'
        res_up_cup = ScoringService.score_pronunciation("up", "cup", short_word_threshold=90)
        self.assertFalse(res_up_cup.passed)

    def test_vowel_substitutions_produce_meaningful_feedback(self):
        """Vowel changes like 'pin' for 'pen' fail and show bracketed difference."""
        res = ScoringService.score_pronunciation("pen", "pin", short_word_threshold=90)
        self.assertFalse(res.passed)
        self.assertEqual(res.bracketed_diff, "P[E]N")

        res_hat_hot = ScoringService.score_pronunciation("hat", "hot", short_word_threshold=90)
        self.assertFalse(res_hat_hot.passed)
        self.assertEqual(res_hat_hot.bracketed_diff, "H[A]T")

    def test_short_word_boundary_length_difference(self):
        res_cats = ScoringService.score_pronunciation("cat", "cats", pass_threshold=75, short_word_threshold=90)
        self.assertLess(res_cats.score, 90)
        self.assertFalse(res_cats.passed, "'cats' must not pass for target 'cat'")

    def test_short_word_exact_match_passes(self):
        res_exact = ScoringService.score_pronunciation("cat", "cat")
        self.assertEqual(res_exact.score, 100)
        self.assertTrue(res_exact.passed)

    # 6. Compound Words and Silent Letter Tests
    def test_compound_words_scoring(self):
        """Verify compound words score properly on partials vs full matches."""
        # Exact match passes
        res_full = ScoringService.score_pronunciation("blacksmith", "blacksmith")
        self.assertEqual(res_full.score, 100)
        self.assertTrue(res_full.passed)

        # Missing half of compound fails
        res_half = ScoringService.score_pronunciation("blacksmith", "black")
        self.assertFalse(res_half.passed)

        res_cobble = ScoringService.score_pronunciation("cobblestone", "cobble")
        self.assertFalse(res_cobble.passed)

    def test_silent_letter_phonetic_variations(self):
        """Verify words with silent letters (knight, gnome, write, climb)."""
        # knight vs nite
        res_knight = ScoringService.score_pronunciation("knight", "nite")
        self.assertEqual(res_knight.bracketed_diff, "[K]NI[GH]T")

        # write vs rite
        res_write = ScoringService.score_pronunciation("write", "rite")
        self.assertIn("wr", res_write.feedback.lower())

    # 7. Multisyllabic and High-Difficulty Tier Tests (Worlds 6 & 7)
    def test_multisyllabic_words_scoring(self):
        """Verify complex 5-8 syllable words across advanced curriculum."""
        # biomineralization (8 syllables)
        res_bio = ScoringService.score_pronunciation("biomineralization", "biomineralization")
        self.assertEqual(res_bio.score, 100)
        self.assertTrue(res_bio.passed)

        # crystallography (5 syllables)
        res_cryst = ScoringService.score_pronunciation("crystallography", "crystallography")
        self.assertEqual(res_cryst.score, 100)
        self.assertTrue(res_cryst.passed)

        # minor multisyllabic typo still receives close partial score
        res_cryst_typo = ScoringService.score_pronunciation("crystallography", "crystallografy", pass_threshold=75)
        self.assertGreaterEqual(res_cryst_typo.score, 75)
        self.assertTrue(res_cryst_typo.passed)

        # verisimilitude (6 syllables)
        res_veri = ScoringService.score_pronunciation("verisimilitude", "verisimilitude")
        self.assertEqual(res_veri.score, 100)
        self.assertTrue(res_veri.passed)


if __name__ == "__main__":
    unittest.main()
