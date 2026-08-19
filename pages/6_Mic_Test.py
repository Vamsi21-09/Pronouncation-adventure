"""Pronunciation Adventure - Microphone & Speech Recognition Diagnostic Screen."""
from __future__ import annotations

import logging
import streamlit as st

logger = logging.getLogger(__name__)
from services.auth_service import get_auth_service
from services.speech_service import get_speech_service
from components.web_speech import render_mic_diagnostics, render_fallback_audio_recorder
from components.sidebar import render_app_sidebar

from config.design_tokens import (
    AUTHENTIC_TEAL,
    AUTHENTIC_TEAL_DARK,
    AUTHENTIC_TEAL_SURFACE,
    AUTHENTIC_TEAL_LIGHT,
    AUTHENTIC_TEAL_BORDER,
    SIDECAR_YELLOW,
    SIDECAR_YELLOW_LIGHT,
    SIDECAR_YELLOW_WARM,
    SIDECAR_YELLOW_BORDER,
    INK_GRAY,
    INK_GRAY_BORDER,
    ANTIQUE_GOLD,
    TEXT_LIGHT_PRIMARY,
    TEXT_LIGHT_SECONDARY,
    TEXT_DARK_PRIMARY,
    TEXT_DARK_SECONDARY,
    get_global_css,
)

st.set_page_config(
    page_title="Microphone Diagnostic - Pronunciation Adventure",
    page_icon="🎙️",
    layout="wide"
)

# Inject Shared Design System CSS
st.html(get_global_css())

# Custom Styling in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    .mic-header {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.3);
        border-radius: 18px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        color: {TEXT_LIGHT_PRIMARY};
        box-shadow: 0 8px 24px rgba(3, 83, 82, 0.25);
    }}

    .info-card {{
        background: #FFFDF5;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-top: 1rem;
        color: {TEXT_DARK_PRIMARY};
        box-shadow: 0 4px 16px rgba(47, 58, 58, 0.06);
    }}
</style>
""")


def check_auth() -> dict:
    """Ensure user is logged in."""
    auth_service = get_auth_service()
    session_info = auth_service.get_current_session()

    user = None
    if session_info and session_info.success and session_info.user:
        user = session_info.user
    elif st.session_state.get("authenticated") and st.session_state.get("user"):
        user = st.session_state["user"]

    if not user:
        st.warning("🔒 Please log in to test your microphone.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/1_Login.py")
        st.stop()

    return user


def main() -> None:
    user = check_auth()
    speech_svc = get_speech_service()

    # App Mode Sidebar ONLY (No duplicate top navbar)
    render_app_sidebar("mic", user=user, profile=st.session_state.get("profile"))

    header_html = (
        f'<div class="mic-header">\n'
        f'<h1 style="margin:0; color:{TEXT_LIGHT_PRIMARY};">🎙️ Microphone & Speech Diagnostics</h1>\n'
        f'<p style="color:{TEXT_LIGHT_SECONDARY}; margin-top:0.35rem; font-size:1.05rem;">\n'
        f'Verify your microphone hardware, browser permissions, and speech-to-text engine before playing.\n'
        f'</p>\n'
        f'</div>'
    )
    st.html(header_html)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("🛠️ Client-Side Web Speech Diagnostics (Stage A)")
        st.caption("Perform the live test below to ensure browser speech recognition is active:")
        diag_res = render_mic_diagnostics(key="mic_test_web_speech")

        # Display live recognition outcome if returned
        if diag_res:
            if diag_res.is_usable():
                conf_pct = int(diag_res.confidence * 100)
                st.success(f"🗣️ **Browser recognition result:** \"{diag_res.text}\" *(via {diag_res.provider_used}, {conf_pct}% confidence)*")
            else:
                st.warning(f"⚠️ {diag_res.error or 'Could not capture speech.'}")

        st.divider()
        st.subheader("🛟 Server-Side Fallback Recorder Test (Stage B)")
        st.caption("Use this alternative recorder if your browser cannot use the Web Speech API:")

        fallback_bytes = render_fallback_audio_recorder(key="mic_test_fallback_audio")
        if fallback_bytes:
            with st.spinner("🟡 Transcribing audio via fallback service..."):
                result = speech_svc.transcribe_audio_bytes(fallback_bytes)
                if result.is_usable():
                    st.success(f"🗣️ **Heard:** \"{result.text}\" *(via {result.provider_used})*")
                else:
                    st.warning(f"⚠️ {result.error or 'Could not recognize speech.'}")

    with col2:
        st.subheader("💡 Recommended Setup & Audio Tips")
        tips_html = f"""
        <div class="info-card">
            <h4 style="margin-top:0; color:{AUTHENTIC_TEAL}; font-weight:800;">🎙️ Hardware & Environment</h4>
            <ul style="color:{TEXT_DARK_SECONDARY}; line-height:1.7; font-size:0.95rem; padding-left:1.25rem;">
                <li>Use a headset or external microphone for best accuracy.</li>
                <li>Speak in a quiet environment away from background noise.</li>
                <li>Speak at a natural conversational volume and pace.</li>
            </ul>
            <h4 style="margin-top:1.25rem; color:{AUTHENTIC_TEAL}; font-weight:800;">🌐 Browser Compatibility</h4>
            <p style="color:{TEXT_DARK_SECONDARY}; font-size:0.92rem; margin-bottom:0.5rem;">
                The Web Speech API is natively supported on:
            </p>
            <ul style="color:{TEXT_DARK_SECONDARY}; line-height:1.7; font-size:0.95rem; padding-left:1.25rem;">
                <li><strong>Google Chrome</strong> (Desktop & Android)</li>
                <li><strong>Microsoft Edge</strong> (Desktop)</li>
                <li><strong>Chromebooks / Chrome OS</strong></li>
            </ul>
        </div>
        """
        st.html(tips_html)

        st.write("")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state["game_mode"] = False
                st.switch_page("app.py")
        with col_btn2:
            if st.button("🗺️ Journey Map", type="primary", use_container_width=True):
                st.session_state["game_mode"] = True
                st.switch_page("pages/2_Journey_Map.py")
        with col_btn3:
            if st.button("🎮 Go to Gameplay", use_container_width=True):
                st.session_state["game_mode"] = True
                st.switch_page("pages/5_Play.py")


if __name__ == "__main__":
    main()
