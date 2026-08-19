"""Unit tests for the client-side Web Speech component and Python bridge."""
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

from components.web_speech import render_web_speech_recorder, render_mic_diagnostics
from services.speech_service import TranscriptResult, PROVIDER_WEB_SPEECH, ERROR_PERMISSION_DENIED, ERROR_NO_SPEECH


class TestWebSpeechComponentBridge(unittest.TestCase):
    """Test suite for Web Speech component input/output processing."""

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_recorder_no_interaction_returns_none(self, mock_comp):
        """When component has not received user interaction, returns None."""
        mock_comp.return_value = None
        res = render_web_speech_recorder(target_word="hello", key="test_key")
        self.assertIsNone(res)

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_recorder_successful_transcript(self, mock_comp):
        """When component returns a transcript dict, formats into standard TranscriptResult."""
        mock_comp.return_value = {
            "transcript": "adventure",
            "confidence": 0.96,
            "error": None,
            "timestamp": 1723618492000
        }
        res = render_web_speech_recorder(target_word="adventure", key="test_key")
        self.assertIsNotNone(res)
        self.assertIsInstance(res, TranscriptResult)
        self.assertTrue(res.is_usable())
        self.assertEqual(res.text, "adventure")
        self.assertEqual(res.confidence, 0.96)
        self.assertEqual(res.provider_used, PROVIDER_WEB_SPEECH)
        self.assertEqual(res.timestamp, 1723618492000)
        self.assertIsNone(res.error)

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_wrong_word_is_usable(self, mock_comp):
        """When user says 'baker' for 'clock', result is still usable (not a speech error)."""
        mock_comp.return_value = {
            "transcript": "baker",
            "confidence": 0.94,
            "error": None,
            "timestamp": 1723618495000
        }
        res = render_web_speech_recorder(target_word="clock", key="test_key")
        self.assertIsNotNone(res)
        self.assertTrue(res.is_usable())
        self.assertEqual(res.text, "baker")
        self.assertIsNone(res.error)

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_recorder_permission_denied_error(self, mock_comp):
        """When component returns permission denied, maps to friendly guidance without crashing."""
        mock_comp.return_value = {
            "transcript": "",
            "confidence": 0.0,
            "error": "not-allowed"
        }
        res = render_web_speech_recorder(target_word="cat", key="test_key")
        self.assertIsNotNone(res)
        self.assertFalse(res.is_usable())
        self.assertEqual(res.error_type, ERROR_PERMISSION_DENIED)
        self.assertIn("Microphone access was blocked", res.error)

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_recorder_no_speech_error(self, mock_comp):
        """When component returns no-speech timeout, maps to friendly no speech guidance."""
        mock_comp.return_value = {
            "transcript": "",
            "confidence": 0.0,
            "error": "no-speech"
        }
        res = render_web_speech_recorder(target_word="dog", key="test_key")
        self.assertIsNotNone(res)
        self.assertFalse(res.is_usable())
        self.assertEqual(res.error_type, ERROR_NO_SPEECH)
        self.assertIn("didn't hear you", res.error.lower())

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_recorder_attempt_id_forwarded(self, mock_comp):
        """When component sends attempt_id, it is preserved in TranscriptResult."""
        mock_comp.return_value = {
            "attempt_id": 42,
            "transcript": "dragon",
            "confidence": 0.98,
            "error": None,
            "timestamp": 1723618500000
        }
        res = render_web_speech_recorder(target_word="dragon", key="test_key")
        self.assertIsNotNone(res)
        self.assertEqual(res.attempt_id, 42)
        self.assertEqual(res.text, "dragon")
        self.assertTrue(res.is_usable())

    @patch("components.web_speech._web_speech_component")
    def test_render_web_speech_timeout_error_mapping(self, mock_comp):
        """When component returns timeout error, correctly maps to audio_timeout error type."""
        mock_comp.return_value = {
            "attempt_id": 43,
            "transcript": "",
            "confidence": 0.0,
            "error": "timeout",
            "timestamp": 1723618505000
        }
        res = render_web_speech_recorder(target_word="castle", key="test_key")
        self.assertIsNotNone(res)
        self.assertFalse(res.is_usable())
        self.assertEqual(res.attempt_id, 43)
        self.assertEqual(res.error_type, "audio_timeout")


if __name__ == "__main__":
    unittest.main()
