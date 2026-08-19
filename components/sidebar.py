"""App Mode Sidebar component with Authentic Teal and Sidecar Yellow brand visual identity."""
from __future__ import annotations

import html
import streamlit as st
from services.auth_service import get_auth_service
from config.design_tokens import (
    AUTHENTIC_TEAL,
    AUTHENTIC_TEAL_DARK,
    AUTHENTIC_TEAL_LIGHT,
    AUTHENTIC_TEAL_SURFACE,
    SIDECAR_YELLOW,
    SIDECAR_YELLOW_WARM,
    INK_GRAY,
    INK_GRAY_BORDER,
    TEXT_LIGHT_PRIMARY,
    TEXT_LIGHT_SECONDARY,
    TEXT_DARK_PRIMARY,
    TEXT_DARK_SECONDARY,
)


def render_app_sidebar(current_page: str = "home", user: dict | None = None, profile: dict | None = None) -> None:
    """
    Renders the dedicated, child-friendly App Mode sidebar for authenticated students.
    Strictly contains ONLY:
    🏠 Home
    🗺️ Journey Map
    👤 Profile
    🎙️ Mic Test
    ⚙️ Settings
    ────────────
    🎮 Enter Game
    🚪 Logout

    Hides default Streamlit multi-page auto-navigation list ([data-testid="stSidebarNav"])
    to ensure developer/debug pages and auth pages are never exposed to normal students.
    """
    # 1. Hide default Streamlit auto-nav pages and style sidebar with Sidecar Yellow & Authentic Teal
    st.html(f"""
    <style>
        /* Hide raw multi-page auto-navigation list */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* Sidebar Container Theming: Sidecar Yellow Canvas */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FAF5DC 0%, {SIDECAR_YELLOW} 100%) !important;
            border-right: 1.5px solid rgba(47, 58, 58, 0.25) !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {TEXT_DARK_PRIMARY};
        }}

        /* Clean Single-Layer Button Wrappers: Remove any nested container borders or outlines */
        [data-testid="stSidebar"] div[data-testid="stButton"],
        [data-testid="stSidebar"] div[data-testid="stPopover"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 0 0.45rem 0 !important;
        }}

        /* Inactive Sidebar Buttons: Authentic Teal Single-Layer with Light Cream Text & Icons */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled),
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button {{
            background: {AUTHENTIC_TEAL} !important;
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
            border: 1.5px solid #023535 !important;
            border-radius: 12px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            padding: 0 1.15rem !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.96rem !important;
            text-align: left !important;
            width: 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            box-shadow: 0 2px 6px rgba(47, 58, 58, 0.12) !important;
            outline: none !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}

        /* Child overrides to prevent nested inner pill or wrong text color */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) *,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) p,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) span,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) div,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button *,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button p,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button span,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button div,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button svg {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* Inactive Sidebar Buttons Hover */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled):hover,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover {{
            background: {AUTHENTIC_TEAL_LIGHT} !important;
            border-color: {AUTHENTIC_TEAL} !important;
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
            transform: translateX(2px) !important;
            box-shadow: 0 4px 12px rgba(3, 83, 82, 0.25) !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled):hover *,
        [data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover * {{
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
        }}

        /* Active Navigation Item (Disabled primary button on Sidecar Yellow sidebar):
           Clean single layer, #FFFDF5 Cream surface with strong #102A2A Dark Primary border and text */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:disabled,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:disabled {{
            background: #FFFDF5 !important;
            color: {TEXT_DARK_PRIMARY} !important;
            fill: {TEXT_DARK_PRIMARY} !important;
            border: 2px solid {TEXT_DARK_PRIMARY} !important;
            border-radius: 12px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            padding: 0 1.15rem !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 800 !important;
            font-size: 0.96rem !important;
            text-align: left !important;
            width: 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            opacity: 1 !important;
            box-shadow: 0 3px 10px rgba(16, 42, 42, 0.15) !important;
            outline: none !important;
            transform: none !important;
            cursor: default !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:disabled *,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:disabled *,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:disabled p,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:disabled span {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: {TEXT_DARK_PRIMARY} !important;
            fill: {TEXT_DARK_PRIMARY} !important;
            font-weight: 800 !important;
            opacity: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* Settings Popover Body: Sidecar Yellow / Cream Surface with Dark Text */
        [data-testid="stPopoverBody"] {{
            background: #FFFDF5 !important;
            border: 1.5px solid {INK_GRAY_BORDER} !important;
            border-radius: 16px !important;
            box-shadow: 0 12px 36px rgba(47, 58, 58, 0.25) !important;
            color: {TEXT_DARK_PRIMARY} !important;
            padding: 1.25rem !important;
        }}

        [data-testid="stPopoverBody"] h1,
        [data-testid="stPopoverBody"] h2,
        [data-testid="stPopoverBody"] h3,
        [data-testid="stPopoverBody"] h4,
        [data-testid="stPopoverBody"] h5,
        [data-testid="stPopoverBody"] h6 {{
            color: {AUTHENTIC_TEAL} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 800 !important;
        }}

        [data-testid="stPopoverBody"] p,
        [data-testid="stPopoverBody"] span,
        [data-testid="stPopoverBody"] label,
        [data-testid="stPopoverBody"] [data-testid="stWidgetLabel"] p,
        [data-testid="stPopoverBody"] [data-testid="stWidgetLabel"] span {{
            color: {TEXT_DARK_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 600 !important;
        }}

        [data-testid="stPopoverBody"] .stCaption,
        [data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] p,
        [data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] span {{
            color: {TEXT_DARK_SECONDARY} !important;
            font-family: 'Inter', sans-serif !important;
        }}

        [data-testid="stPopoverBody"] div[data-baseweb="slider"] span,
        [data-testid="stPopoverBody"] div[data-baseweb="slider"] div {{
            color: {TEXT_DARK_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
        }}

        [data-testid="stPopoverBody"] div[data-testid="stToggle"] label p,
        [data-testid="stPopoverBody"] div[data-testid="stToggle"] label span {{
            color: {TEXT_DARK_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
        }}

        /* Sidebar Brand Card */
        .sidebar-brand-card {{
            background: {AUTHENTIC_TEAL};
            border: 1.5px solid #023535;
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin-bottom: 1rem;
            text-align: center;
            box-shadow: 0 4px 14px rgba(47, 58, 58, 0.12);
        }}
        .sidebar-brand-title {{
            font-family: 'General Sans', sans-serif;
            font-size: 1.15rem;
            font-weight: 800;
            color: {TEXT_LIGHT_PRIMARY};
            margin: 0;
            letter-spacing: -0.01em;
        }}
        .sidebar-brand-sub {{
            font-family: 'General Sans', sans-serif;
            font-size: 0.76rem;
            color: {SIDECAR_YELLOW};
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-top: 2px;
        }}
        .sidebar-student-badge {{
            font-family: 'General Sans', sans-serif;
            font-size: 0.88rem;
            color: {TEXT_LIGHT_PRIMARY};
            font-weight: 600;
            margin-top: 0.4rem;
            background: rgba(255, 253, 245, 0.15);
            border-radius: 8px;
            padding: 3px 10px;
            display: inline-block;
        }}

        .sidebar-nav-header {{
            font-family: 'General Sans', sans-serif;
            font-size: 0.8rem;
            font-weight: 800;
            color: {TEXT_DARK_PRIMARY} !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0.85rem 0 0.45rem 0;
        }}

        [data-testid="stSidebar"] hr {{
            border-color: rgba(47, 58, 58, 0.25) !important;
            margin: 0.75rem 0 !important;
        }}
    </style>
    """)

    # 2. Render Custom Student Sidebar Content
    with st.sidebar:
        # Brand & User Info
        display_name = ""
        if profile and profile.get("display_name"):
            display_name = html.escape(str(profile["display_name"]))
        elif user and user.get("email"):
            display_name = html.escape(str(user["email"]).split("@")[0])
        else:
            display_name = "Adventurer"

        st.html(f"""
        <div class="sidebar-brand-card">
            <div class="sidebar-brand-title">🎙️ Pronunciation Adventure</div>
            <div class="sidebar-brand-sub">Student Portal</div>
            <div class="sidebar-student-badge">👋 {display_name}</div>
        </div>
        <div class="sidebar-nav-header">🧭 Navigation</div>
        """)

        # 1. 🏠 Home
        if current_page == "home":
            st.button("🏠 Home", type="primary", use_container_width=True, disabled=True, key="sb_home_active")
        else:
            if st.button("🏠 Home", use_container_width=True, key="sb_btn_home"):
                st.session_state["game_mode"] = False
                st.switch_page("app.py")

        # 2. 🗺️ Journey Map
        if current_page == "journey":
            st.button("🗺️ Journey Map", type="primary", use_container_width=True, disabled=True, key="sb_journey_active")
        else:
            if st.button("🗺️ Journey Map", use_container_width=True, key="sb_btn_journey"):
                st.session_state["game_mode"] = True
                st.switch_page("pages/2_Journey_Map.py")

        # 3. 👤 Profile
        if current_page == "profile":
            st.button("👤 Profile", type="primary", use_container_width=True, disabled=True, key="sb_profile_active")
        else:
            if st.button("👤 Profile", use_container_width=True, key="sb_btn_profile"):
                st.session_state["game_mode"] = False
                st.switch_page("pages/3_Profile.py")

        # 4. 🎙️ Mic Test
        if current_page == "mic":
            st.button("🎙️ Mic Test", type="primary", use_container_width=True, disabled=True, key="sb_mic_active")
        else:
            if st.button("🎙️ Mic Test", use_container_width=True, key="sb_btn_mic"):
                st.session_state["game_mode"] = False
                st.switch_page("pages/6_Mic_Test.py")

        # 5. ⚙️ Settings
        with st.popover("⚙️ Settings", use_container_width=True):
            st.markdown("#### ⚙️ Student Settings")
            st.caption("Customize your audio & pronunciation experience.")
            
            # Sound effects volume toggle
            sfx_enabled = st.toggle("Sound Effects & Chimes", value=st.session_state.get("setting_sfx", True), key="toggle_sfx")
            st.session_state["setting_sfx"] = sfx_enabled

            # Speech confidence strictness
            mic_sens = st.select_slider(
                "Speech Sensitivity",
                options=["Gentle", "Standard", "Challenging"],
                value=st.session_state.get("setting_sens", "Standard"),
                key="slider_sens"
            )
            st.session_state["setting_sens"] = mic_sens
            st.success("Preferences saved.")

        st.divider()

        # 6. 🎮 Enter Game
        if st.button("🎮 Enter Game", use_container_width=True, key="sb_btn_enter_game"):
            st.session_state["game_mode"] = True
            st.switch_page("pages/2_Journey_Map.py")

        # 7. 🚪 Logout
        if st.button("🚪 Logout", use_container_width=True, key="sb_btn_logout"):
            auth_service = get_auth_service()
            auth_service.log_out()
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["profile"] = None
            st.session_state["game_mode"] = False
            st.session_state.pop("cached_companion", None)
            st.success("Logged out.")
            st.switch_page("app.py")
