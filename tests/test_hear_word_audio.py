"""Tests for the lightweight 'Hear Word' audio pronunciation feature."""
import pytest
from components.audio_playback import get_hear_word_button_html


class TestHearWordAudioFeature:
    """Test suite for Hear Word pronunciation button."""

    def test_get_hear_word_button_html_structure(self):
        """Verify the HTML structure, button label, and SpeechSynthesisUtterance call."""
        html_out = get_hear_word_button_html("DOG", button_id="hear_btn_123")
        
        assert "hear-word-btn" in html_out
        assert "id=\"hear_btn_123\"" in html_out
        assert "🔊 Hear Word" in html_out
        assert "SpeechSynthesisUtterance" in html_out
        assert "\"DOG\"" in html_out
        assert "en-US" in html_out
        assert "hear_btn_123_err" in html_out
        assert "Audio playback isn’t available. Please try again." in html_out

    def test_get_hear_word_button_html_special_characters(self):
        """Verify escaping for words with quotes or special characters."""
        html_out = get_hear_word_button_html("can't", button_id="hear_btn_cant")
        
        assert "hear-word-btn" in html_out
        assert "can&#x27;t" in html_out or "can't" in html_out
        assert "\"can't\"" in html_out  # JSON encoded safe string
        assert "hear_btn_cant" in html_out

    def test_get_hear_word_dual_engine_audio_fallback(self):
        """Verify audio fallback to open dictionary audio stream is present."""
        html_out = get_hear_word_button_html("BUTTERFLY", button_id="hear_butterfly")
        
        assert "dictvoice" in html_out or "translate_tts" in html_out
        assert "new Audio(" in html_out
        assert "playAudioFallback" in html_out
        assert "SpeechSynthesisUtterance" in html_out

    def test_render_hear_word_button_call(self, monkeypatch):
        """Verify render_hear_word_button calls components.html with expected markup."""
        from components.audio_playback import render_hear_word_button
        called = {}

        def mock_components_html(html, height=None, scrolling=False):
            called["html"] = html
            called["height"] = height
            called["scrolling"] = scrolling

        import streamlit.components.v1 as components
        monkeypatch.setattr(components, "html", mock_components_html)

        render_hear_word_button("GALAXY", key="hear_galaxy")
        assert "GALAXY" in called["html"]
        assert called["height"] == 48
        assert called["scrolling"] is False
