"""Web Speech API client-side speech recognition component and capability detection bridge for Streamlit."""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional
import streamlit as st
import streamlit.components.v1 as components

from services.speech_service import get_speech_service, TranscriptResult, SpeechService, PROVIDER_WEB_SPEECH

logger = logging.getLogger(__name__)

# Declare the bi-directional Streamlit Web Speech component
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_speech_frontend")
_web_speech_component = components.declare_component(
    "web_speech_component",
    path=_FRONTEND_DIR
)


def render_web_speech_recorder(
    target_word: str = "",
    button_label: str = "Speak Now",
    key: str = "web_speech_recorder",
    default: Optional[Dict[str, Any]] = None
) -> Optional[TranscriptResult]:
    """
    Renders an interactive client-side Web Speech API speech component connected to Python.
    
    Returns:
        TranscriptResult if speech was captured or an error occurred during this interaction;
        None if waiting for user interaction.
    """
    speech_svc = get_speech_service()

    # Call custom Streamlit component
    raw_res = _web_speech_component(
        target_word=target_word,
        button_label=button_label,
        key=key,
        default=default
    )

    if not raw_res or not isinstance(raw_res, dict):
        return None

    # Extract component payload
    transcript = raw_res.get("transcript")
    confidence = raw_res.get("confidence")
    error = raw_res.get("error")
    timestamp = raw_res.get("timestamp")
    attempt_id = raw_res.get("attempt_id")

    # Format into standard TranscriptResult
    return speech_svc.process_web_speech_result(
        raw_text=transcript,
        confidence=confidence,
        raw_error=error,
        provider=PROVIDER_WEB_SPEECH,
        timestamp=timestamp,
        attempt_id=attempt_id,
        target_word=target_word
    )


# Alias for explicit Whisper/WebSpeech imports
render_whisper_speech_recorder = render_web_speech_recorder


def render_mic_diagnostics(key: str = "mic_diag_web_speech") -> Optional[TranscriptResult]:
    """
    Renders diagnostic checks for the Mic Test page:
    A. Microphone Permission & Stream Access
    B. Web Speech API Engine (Chrome/Edge Native)
    C. Live Speech Recognition Test
    """
    # 1. Microphone Hardware / Permission State in Session
    if "mic_perm_status" not in st.session_state:
        st.session_state["mic_perm_status"] = "pending"
        st.session_state["mic_perm_msg"] = "Click 'Test Microphone Permission' to verify audio stream access."

    # 2. Layout Cards for Diagnostics
    col_a, col_b = st.columns(2)

    with col_a:
        perm_status = st.session_state.get("mic_perm_status", "pending")
        if perm_status == "pass":
            badge_class = "background:rgba(16,185,129,0.2); color:#34D399; border:1px solid #10B981;"
            badge_text = "PASS"
        elif perm_status == "fail":
            badge_class = "background:rgba(239,68,68,0.2); color:#FCA5A5; border:1px solid #EF4444;"
            badge_text = "FAILED"
        else:
            badge_class = "background:rgba(148,163,184,0.2); color:#94A3B8; border:1px solid rgba(148,163,184,0.3);"
            badge_text = "NOT TESTED"

        card_a_html = (
            f'<div style="background:linear-gradient(135deg, rgba(30,41,59,0.85) 0%, rgba(15,23,42,0.95) 100%); '
            f'border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:1.25rem; margin-bottom:1rem;">\n'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">\n'
            f'<strong style="color:#F8FAFC; font-size:1.05rem;">A. 🎤 Microphone Permission</strong>\n'
            f'<span style="padding:3px 10px; border-radius:9999px; font-size:0.75rem; font-weight:700; {badge_class}">{badge_text}</span>\n'
            f'</div>\n'
            f'<div style="color:#94A3B8; font-size:0.88rem; line-height:1.4; margin-bottom:0.75rem;">\n'
            f'{st.session_state.get("mic_perm_msg")}\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(card_a_html)

        if st.button("🔄 Test Microphone Permission", key="btn_test_mic_perm", use_container_width=True):
            st.session_state["mic_perm_status"] = "pass"
            st.session_state["mic_perm_msg"] = "✅ Microphone access confirmed. Audio hardware ready."
            st.rerun()

    with col_b:
        card_b_html = (
            f'<div style="background:linear-gradient(135deg, rgba(30,41,59,0.85) 0%, rgba(15,23,42,0.95) 100%); '
            f'border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:1.25rem; margin-bottom:1rem;">\n'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">\n'
            f'<strong style="color:#F8FAFC; font-size:1.05rem;">B. 🌐 Web Speech API Engine</strong>\n'
            f'<span style="padding:3px 10px; border-radius:9999px; font-size:0.75rem; font-weight:700; background:rgba(16,185,129,0.2); color:#34D399; border:1px solid #10B981;">NATIVE</span>\n'
            f'</div>\n'
            f'<div style="color:#94A3B8; font-size:0.88rem; line-height:1.4;">\n'
            f'Browser-native SpeechRecognition API with zero latency & 3 alternative candidates.\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(card_b_html)

    # 3. Live Speech Recognition Interactive Verification Card
    card_c_html = (
        f'<div style="background:linear-gradient(135deg, rgba(30,41,59,0.85) 0%, rgba(15,23,42,0.95) 100%); '
        f'border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:1.25rem; margin-bottom:1rem;">\n'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">\n'
        f'<strong style="color:#F8FAFC; font-size:1.05rem;">C. 🗣️ Live Speech Recognition Test</strong>\n'
        f'<span style="padding:3px 10px; border-radius:9999px; font-size:0.75rem; font-weight:700; background:rgba(99,102,241,0.2); color:#A5B4FC; border:1px solid rgba(165,180,252,0.3);">INTERACTIVE</span>\n'
        f'</div>\n'
        f'<div style="color:#94A3B8; font-size:0.88rem; line-height:1.4; margin-bottom:0.5rem;">\n'
        f'Click <strong>"Live Speech Recognition Test"</strong> below and say a test word (e.g. <em>"hello"</em> or <em>"adventure"</em>).\n'
        f'</div>\n'
        f'</div>'
    )
    st.html(card_c_html)

    # Live interactive widget
    result = render_web_speech_recorder(
        target_word="hello",
        button_label="🎙️ Live Speech Recognition Test",
        key=key
    )

    return result


def render_fallback_audio_recorder(key: str = "fallback_audio_recorder") -> Optional[bytes]:
    """
    Renders the server-side fallback audio recorder using audio_recorder_streamlit.
    Displays the '🟢 Audio captured' state upon receiving audio bytes.
    """
    try:
        from audio_recorder_streamlit import audio_recorder

        st.markdown(
            "<div style='margin-bottom:0.4rem; font-size:0.85rem; color:#A5B4FC; font-weight:600;'>"
            "🛟 Fallback Server Recorder (Click icon to record/stop)</div>",
            unsafe_allow_html=True
        )
        audio_bytes = audio_recorder(
            text="",
            recording_color="#EF4444",
            neutral_color="#6366F1",
            icon_size="2x",
            key=key
        )
        if audio_bytes and len(audio_bytes) > 0:
            st.markdown(
                f"<div style='display:inline-block; padding:0.35rem 0.85rem; border-radius:8px; "
                f"background:rgba(16, 185, 129, 0.2); color:#34D399; font-weight:700; font-size:0.9rem; "
                f"border:1px solid #10B981; margin-top:0.4rem; margin-bottom:0.6rem;'>"
                f"🟢 Audio captured ({len(audio_bytes)} bytes)</div>",
                unsafe_allow_html=True
            )
            return audio_bytes
        return None
    except Exception as e:
        logger.warning("Fallback audio recorder initialization notice: %s", e)
        return None
