"""Shared top navigation bar component for Pronunciation Adventure."""
from __future__ import annotations

import streamlit as st
from services.auth_service import get_auth_service


def render_navbar(current_page: str = "") -> None:
    """
    Renders a sleek, responsive navigation bar at the top of authenticated pages.
    Exposes Home, Journey Map, Profile, Mic Test, Let's Play, and Logout.
    """
    st.html("""
    <style>
        .nav-wrapper {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 0.5rem 0.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(10px);
        }
        div.stButton > button.nav-active-btn {
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid #818CF8 !important;
            box-shadow: 0 0 14px rgba(99, 102, 241, 0.4) !important;
        }
    </style>
    """)

    col_home, col_map, col_play, col_profile, col_mic, col_logout = st.columns([1, 1.1, 1.1, 1, 1, 0.9])

    with col_home:
        if current_page == "home":
            st.button("🏠 Home", type="primary", use_container_width=True, disabled=True, key="navbar_home_active")
        else:
            if st.button("🏠 Home", use_container_width=True, key="navbar_home_btn"):
                st.session_state["game_mode"] = False
                st.switch_page("app.py")

    with col_map:
        if current_page == "journey":
            st.button("🗺️ Journey", type="primary", use_container_width=True, disabled=True, key="navbar_journey_active")
        else:
            if st.button("🗺️ Journey", use_container_width=True, key="navbar_journey_btn"):
                st.session_state["game_mode"] = True
                st.switch_page("pages/2_Journey_Map.py")

    with col_play:
        if current_page == "play":
            st.button("🎮 Let's Play", type="primary", use_container_width=True, disabled=True, key="navbar_play_active")
        else:
            if st.button("🎮 Let's Play", use_container_width=True, key="navbar_play_btn", type="primary"):
                st.session_state["game_mode"] = True
                st.switch_page("pages/2_Journey_Map.py")

    with col_profile:
        if current_page == "profile":
            st.button("👤 Profile", type="primary", use_container_width=True, disabled=True, key="navbar_profile_active")
        else:
            if st.button("👤 Profile", use_container_width=True, key="navbar_profile_btn"):
                st.session_state["game_mode"] = False
                st.switch_page("pages/3_Profile.py")

    with col_mic:
        if current_page == "mic":
            st.button("🎙️ Mic Test", type="primary", use_container_width=True, disabled=True, key="navbar_mic_active")
        else:
            if st.button("🎙️ Mic Test", use_container_width=True, key="navbar_mic_btn"):
                st.session_state["game_mode"] = False
                st.switch_page("pages/6_Mic_Test.py")

    with col_logout:
        if st.button("🚪 Logout", use_container_width=True, key="navbar_logout_btn"):
            auth_service = get_auth_service()
            auth_service.log_out()
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["profile"] = None
            st.session_state["game_mode"] = False
            st.session_state.pop("cached_companion", None)
            st.success("Successfully logged out.")
            st.rerun()

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
