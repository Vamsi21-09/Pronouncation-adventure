"""Unit tests for SpeechService transcript normalization, error classification, and confidence formatting."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from services.speech_service import (
    SpeechService,
    TranscriptResult,
    ERROR_PERMISSION_DENIED,
    ERROR_NO_SPEECH,
    ERROR_AUDIO_TIMEOUT,
    ERROR_UNSUPPORTED_BROWSER,
    ERROR_NETWORK,
    ERROR_API_FAILURE,
    PROVIDER_WEB_SPEECH,
    PROVIDER_SERVER_FALLBACK,
)


class TestSpeechService(unittest.TestCase):
    """Test suite for speech recognition processing and error handling."""

    def test_transcribe_successful_speech(self):
        result = SpeechService.transcribe(
            raw_text="  Garden  ",
            confidence=0.95,
            provider=PROVIDER_WEB_SPEECH
        )
        self.assertTrue(result.is_success)
        self.assertTrue(result.is_usable())
        self.assertEqual(result.text, "garden")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.provider_used, PROVIDER_WEB_SPEECH)
        self.assertIsNone(result.error)
        self.assertIsNone(result.error_type)

    def test_transcribe_empty_text_returns_no_speech_error(self):
        result = SpeechService.transcribe(raw_text="   ")
        self.assertFalse(result.is_success)
        self.assertFalse(result.is_usable())
        self.assertEqual(result.text, "")
        self.assertEqual(result.error_type, ERROR_NO_SPEECH)
        self.assertIsNotNone(result.error)

    def test_transcribe_permission_denied_error(self):
        result = SpeechService.transcribe(error="not-allowed")
        self.assertFalse(result.is_success)
        self.assertFalse(result.is_usable())
        self.assertEqual(result.error_type, ERROR_PERMISSION_DENIED)
        self.assertIn("lock icon", result.error.lower())

    def test_transcribe_timeout_error(self):
        result = SpeechService.transcribe(error="timeout")
        self.assertFalse(result.is_success)
        self.assertEqual(result.error_type, ERROR_AUDIO_TIMEOUT)

    def test_transcribe_unsupported_browser_error(self):
        result = SpeechService.transcribe(error="not-supported")
        self.assertFalse(result.is_success)
        self.assertEqual(result.error_type, ERROR_UNSUPPORTED_BROWSER)

    def test_transcribe_network_error(self):
        result = SpeechService.transcribe(error="network")
        self.assertFalse(result.is_success)
        self.assertEqual(result.error_type, ERROR_NETWORK)

    def test_confidence_bounds_clamped(self):
        res_high = SpeechService.transcribe(raw_text="hello", confidence=1.85)
        self.assertEqual(res_high.confidence, 1.0)

        res_low = SpeechService.transcribe(raw_text="hello", confidence=-0.45)
        self.assertEqual(res_low.confidence, 0.0)

    # --- Stage B Fallback Audio Bytes Tests ---

    def test_transcribe_audio_bytes_empty_returns_no_speech(self):
        res = SpeechService.transcribe_audio_bytes(b"")
        self.assertFalse(res.is_success)
        self.assertEqual(res.error_type, ERROR_NO_SPEECH)
        self.assertEqual(res.provider_used, PROVIDER_SERVER_FALLBACK)

    @patch("speech_recognition.AudioFile")
    def test_transcribe_audio_bytes_success(self, mock_audio_file):
        mock_rec = MagicMock()
        mock_rec.recognize_google.return_value = "Forest"
        fake_audio_bytes = b"RIFF" + b"\x00" * 200

        res = SpeechService.transcribe_audio_bytes(fake_audio_bytes, recognizer=mock_rec)
        self.assertTrue(res.is_success)
        self.assertEqual(res.text, "forest")
        self.assertEqual(res.provider_used, PROVIDER_SERVER_FALLBACK)

    @patch("speech_recognition.AudioFile")
    def test_transcribe_audio_bytes_unknown_value_error(self, mock_audio_file):
        import speech_recognition as sr
        mock_rec = MagicMock()
        mock_rec.recognize_google.side_effect = sr.UnknownValueError()
        fake_audio_bytes = b"RIFF" + b"\x00" * 200

        res = SpeechService.transcribe_audio_bytes(fake_audio_bytes, recognizer=mock_rec)
        self.assertFalse(res.is_success)
        self.assertEqual(res.error_type, ERROR_NO_SPEECH)

    @patch("speech_recognition.AudioFile")
    def test_transcribe_audio_bytes_request_error(self, mock_audio_file):
        import speech_recognition as sr
        mock_rec = MagicMock()
        mock_rec.recognize_google.side_effect = sr.RequestError("Network connection down")
        fake_audio_bytes = b"RIFF" + b"\x00" * 200

        res = SpeechService.transcribe_audio_bytes(fake_audio_bytes, recognizer=mock_rec)
        self.assertFalse(res.is_success)
        self.assertEqual(res.error_type, ERROR_NETWORK)

    def test_extract_candidate_single_word_exact(self):
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("bat", "bat")
        self.assertEqual(cand, "bat")
        self.assertFalse(is_hallu)

    def test_extract_candidate_minimal_pair_bad_not_forced_to_bat(self):
        """When user says 'bad' for target 'bat', candidate must remain 'bad'."""
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("bad", "bat")
        self.assertEqual(cand, "bad")
        self.assertFalse(is_hallu)

    def test_extract_candidate_minimal_pair_back_not_forced_to_bat(self):
        """When user says 'back' for target 'bat', candidate must remain 'back'."""
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("back", "bat")
        self.assertEqual(cand, "back")
        self.assertFalse(is_hallu)

    def test_extract_candidate_minimal_pair_cap_not_forced_to_cat(self):
        """When user says 'cap' for target 'cat', candidate must remain 'cap'."""
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("cap", "cat")
        self.assertEqual(cand, "cap")
        self.assertFalse(is_hallu)

    def test_extract_candidate_minimal_pair_dot_not_forced_to_dog(self):
        """When user says 'dot' for target 'dog', candidate must remain 'dot'."""
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("dot", "dog")
        self.assertEqual(cand, "dot")
        self.assertFalse(is_hallu)

    def test_extract_candidate_multi_word_hallucination_best_match(self):
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("I am a bad boy", "bat")
        self.assertEqual(cand, "bad")
        self.assertFalse(is_hallu)

    def test_extract_candidate_multi_word_with_the_prefix(self):
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("the bat", "bat")
        self.assertEqual(cand, "bat")
        self.assertFalse(is_hallu)

    def test_extract_candidate_sentence_mode_preserved(self):
        target = "A gentle brown bat flew over the trees."
        raw = "a gentle brown bat flew over the trees"
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate(raw, target)
        self.assertEqual(cand, raw)
        self.assertFalse(is_hallu)

    def test_extract_candidate_ungrounded_hallucination_filtered(self):
        cand, reason, is_hallu = SpeechService.extract_vocabulary_candidate("thank you for watching this video", "bat")
        self.assertEqual(cand, "")
        self.assertTrue(is_hallu)


if __name__ == "__main__":
    unittest.main()
