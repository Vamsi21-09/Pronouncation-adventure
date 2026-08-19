"""Pronunciation Adventure - Candy Crush Style Winding Interactive Journey Map & World Level Progression."""
from __future__ import annotations

import html
import streamlit as st

from config.world_themes import get_world_theme, WORLD_THEMES
from repositories.content_repo import get_content_repository
from repositories.profiles_repo import get_profiles_repository
from services.auth_service import get_auth_service
from services.progression_service import get_progression_service
from services.companion_service import get_companion_service
from config.design_tokens import (
    AUTHENTIC_TEAL,
    AUTHENTIC_TEAL_DARK,
    AUTHENTIC_TEAL_DEEP,
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

# 1. Page Configuration (Game Mode)
st.set_page_config(
    page_title="Journey Map - Pronunciation Adventure",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inject Shared Design System CSS
st.html(get_global_css())

# 3. Rich Candy Crush-Style Aesthetics & Winding Path Styling in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    /* Collapse Streamlit Header & Navigation in Game Mode */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    /* Ensure Streamlit native header does not block clicks */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        pointer-events: none !important;
        height: 0 !important;
    }}

    header[data-testid="stHeader"] * {{
        pointer-events: auto !important;
    }}

    /* Game Mode Sticky Top Bar (Authentic Teal + Sidecar Yellow highlights) */
    .game-topbar-wrapper {{
        position: sticky;
        top: 0.5rem;
        z-index: 9999;
        background: linear-gradient(135deg, rgba(3, 83, 82, 0.98) 0%, rgba(2, 53, 53, 0.99) 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.35);
        border-radius: 18px;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.55);
        backdrop-filter: blur(16px);
    }}

    /* Main Adventure Map Canvas */
    .adventure-canvas {{
        max-width: 680px;
        margin: 0 auto 3rem auto;
        position: relative;
        padding: 1.5rem 0.5rem;
    }}

    /* Candy-like Winding Path Track */
    .winding-track {{
        display: flex;
        flex-direction: column;
        gap: 1.75rem;
        position: relative;
        padding: 1rem 0;
    }}

    /* Connector Ribbon / Track Line (Sidecar Yellow Dotted Track) */
    .path-connector-line {{
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        width: 12px;
        transform: translateX(-50%);
        background: repeating-linear-gradient(
            to bottom,
            rgba(243, 232, 188, 0.35),
            rgba(243, 232, 188, 0.35) 12px,
            transparent 12px,
            transparent 22px
        );
        border-radius: 9999px;
        z-index: 0;
    }}

    /* Circular Level Node Button Styling along Adventure Canvas */
    .adventure-canvas div[data-testid="stButton"] > button {{
        border-radius: 50% !important;
        width: 68px !important;
        height: 68px !important;
        min-width: 68px !important;
        min-height: 68px !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-family: 'General Sans', sans-serif !important;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45) !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        user-select: none !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(145deg, #F3E8BC 0%, #E2D39A 60%, #C9B878 100%) !important;
        color: #102A2A !important;
        fill: #102A2A !important;
        border: 3.5px solid #FFFFFF !important;
        box-shadow: 0 0 24px rgba(243, 232, 188, 0.9), inset 0 2px 4px rgba(255, 255, 255, 0.8) !important;
        animation: activeNodePulse 2.2s infinite ease-in-out !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) {{
        background: linear-gradient(145deg, #10B981 0%, #059669 60%, #047857 100%) !important;
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        border: 3px solid #6EE7B7 !important;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.5), inset 0 2px 4px rgba(255, 255, 255, 0.5) !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button:disabled {{
        background: linear-gradient(145deg, rgba(2, 40, 40, 0.85) 0%, rgba(1, 25, 25, 0.95) 100%) !important;
        color: #D8E3DA !important;
        fill: #D8E3DA !important;
        border: 2px dashed rgba(243, 232, 188, 0.2) !important;
        opacity: 0.75 !important;
        cursor: not-allowed !important;
    }}

    /* Strip child elements of inner borders, backgrounds, and shadows */
    .adventure-canvas div[data-testid="stButton"] > button * {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button[kind="primary"] * {{
        color: #102A2A !important;
        fill: #102A2A !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled) * {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }}

    .adventure-canvas div[data-testid="stButton"] > button:disabled * {{
        color: #D8E3DA !important;
        fill: #D8E3DA !important;
    }}

    @keyframes activeNodePulse {{
        0%, 100% {{
            box-shadow: 0 0 20px rgba(243, 232, 188, 0.6), inset 0 2px 4px rgba(255, 255, 255, 0.6);
            transform: scale(1);
        }}
        50% {{
            box-shadow: 0 0 36px rgba(243, 232, 188, 0.95), inset 0 2px 6px rgba(255, 255, 255, 0.9);
            transform: scale(1.06);
        }}
    }}

    /* Floating Companion Speech Bubble next to Active Level */
    .floating-companion-tag {{
        background: linear-gradient(135deg, rgba(2, 53, 53, 0.95) 0%, rgba(3, 83, 82, 0.95) 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.4);
        font-family: 'General Sans', sans-serif;
        font-size: 0.78rem;
        font-weight: 800;
        padding: 4px 12px;
        border-radius: 9999px;
        white-space: nowrap;
        color: {TEXT_LIGHT_PRIMARY};
        box-shadow: 0 0 18px rgba(243, 232, 188, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        animation: floatTag 2.4s infinite ease-in-out;
        z-index: 10;
    }}

    @keyframes floatTag {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-4px); }}
    }}

    /* World Map Realm Island Card (Consistent Authentic Teal Container) */
    .realm-island {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 2px solid rgba(243, 232, 188, 0.35);
        border-radius: 20px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 8px 24px rgba(3, 83, 82, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        color: {TEXT_LIGHT_PRIMARY};
        position: relative;
    }}

    .realm-island:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(3, 83, 82, 0.4);
    }}

    .realm-active {{
        border: 2.5px solid {SIDECAR_YELLOW} !important;
        box-shadow: 0 0 24px rgba(243, 232, 188, 0.5) !important;
    }}

    .realm-completed {{
        border: 2px solid #10B981 !important;
        box-shadow: 0 0 18px rgba(16, 185, 129, 0.3) !important;
    }}

    .realm-locked {{
        border: 1.5px dashed rgba(243, 232, 188, 0.25) !important;
        background: linear-gradient(135deg, rgba(3, 83, 82, 0.75) 0%, rgba(2, 53, 53, 0.9) 100%) !important;
        opacity: 0.9;
    }}

    .realm-header {{
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }}

    .realm-icon {{
        font-size: 2.5rem;
        line-height: 1;
        background: rgba(0, 0, 0, 0.25);
        padding: 0.75rem;
        border-radius: 16px;
        border: 1px solid rgba(243, 232, 188, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 60px;
        min-height: 60px;
    }}

    .realm-details {{
        flex: 1;
    }}

    .realm-title {{
        font-family: 'General Sans', sans-serif;
        font-size: 1.35rem;
        font-weight: 800;
        color: {TEXT_LIGHT_PRIMARY};
        margin: 0.15rem 0;
        letter-spacing: -0.01em;
    }}

    .status-pill {{
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-family: 'General Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }}

    .pill-unlocked {{
        background: rgba(243, 232, 188, 0.2);
        color: {SIDECAR_YELLOW};
        border: 1px solid rgba(243, 232, 188, 0.4);
    }}

    .pill-completed {{
        background: rgba(16, 185, 129, 0.2);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }}

    .pill-locked {{
        background: rgba(0, 0, 0, 0.3);
        color: {TEXT_LIGHT_SECONDARY};
        border: 1px solid rgba(216, 227, 218, 0.2);
    }}
</style>
""")

# Standard 7 World Definitions for Curated Candy Crush Journey
SEVEN_WORLDS_METADATA = [
    {"order_index": 1, "key": "village", "name": "Sunlit Village", "icon": "🏡", "badge": "Sunlit Village", "theme": "village"},
    {"order_index": 2, "key": "forest", "name": "Whispering Forest", "icon": "🌲", "badge": "Whispering Forest", "theme": "forest"},
    {"order_index": 3, "key": "castle", "name": "Royal Castle", "icon": "🏰", "badge": "Royal Castle", "theme": "castle"},
    {"order_index": 4, "key": "ocean", "name": "Coral Cove", "icon": "🌊", "badge": "Coral Cove", "theme": "ocean"},
    {"order_index": 5, "key": "space", "name": "Cosmic Outpost", "icon": "🚀", "badge": "Cosmic Outpost", "theme": "space"},
    {"order_index": 6, "key": "galaxy", "name": "Starlight Galaxy", "icon": "🌌", "badge": "Starlight Galaxy", "theme": "galaxy"},
    {"order_index": 7, "key": "dragon", "name": "Dragon's Peak", "icon": "🐉", "badge": "Dragon's Peak", "theme": "dragon"},
]


def check_authentication() -> tuple[dict, str]:
    """Verify session with Supabase. Redirect to Login if unauthenticated."""
    auth_service = get_auth_service()
    session_info = auth_service.get_current_session()

    user = None
    if session_info and session_info.success and session_info.user:
        user = session_info.user
    elif st.session_state.get("authenticated") and st.session_state.get("user"):
        user = st.session_state["user"]

    if not user:
        st.warning("🔒 Please log in to view your Journey Map.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/1_Login.py")
        st.stop()

    return user, user["id"]


def render_gameplay_topbar(
    comp_state: dict,
    total_stars: int,
    total_score: int,
    current_streak: int
) -> None:
    """Renders the streamlined Game Mode top bar with sticky high-visibility Exit Game button."""
    comp_info = comp_state.get("stage_info")
    safe_c_name = html.escape(comp_info.name if comp_info else "Companion")
    safe_c_icon = html.escape(comp_info.icon if comp_info else "🥚")
    xp_val = comp_state.get("xp", 0)

    with st.container(border=True):
        top_col1, top_col2, top_col3 = st.columns([1.5, 2, 1.2])

        with top_col1:
            st.html(f"""
            <div style="display:flex; align-items:center; gap:0.75rem; padding:0.1rem 0;">
                <span style="font-size:2.2rem; line-height:1;">{safe_c_icon}</span>
                <div>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:#035352; text-transform:uppercase; letter-spacing:0.08em;">Companion</div>
                    <div style="font-family:'General Sans', sans-serif; font-size:1.12rem; font-weight:800; color:#102A2A;">{safe_c_name}</div>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.82rem; font-weight:700; color:#365656;">{xp_val} XP</div>
                </div>
            </div>
            """)

        with top_col2:
            st.html(f"""
            <div style="display:flex; justify-content:center; gap:1.5rem; align-items:center; height:100%; padding:0.1rem 0;">
                <div style="text-align:center;">
                    <span style="font-family:'General Sans', sans-serif; font-size:1.3rem; font-weight:800; color:#D97706;">🔥 {current_streak}</span>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; text-transform:uppercase; color:#035352; font-weight:800; letter-spacing:0.08em;">Streak</div>
                </div>
                <div style="text-align:center;">
                    <span style="font-family:'General Sans', sans-serif; font-size:1.3rem; font-weight:800; color:#B45309;">⭐ {total_stars}</span>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; text-transform:uppercase; color:#035352; font-weight:800; letter-spacing:0.08em;">Stars</div>
                </div>
                <div style="text-align:center;">
                    <span style="font-family:'General Sans', sans-serif; font-size:1.3rem; font-weight:800; color:#102A2A;">🏆 {total_score}</span>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; text-transform:uppercase; color:#035352; font-weight:800; letter-spacing:0.08em;">Score</div>
                </div>
            </div>
            """)

        with top_col3:
            if st.button("🚪 Exit Game", use_container_width=True, key="btn_exit_game_journey", help="Return to Home Dashboard"):
                st.session_state["game_mode"] = False
                st.switch_page("app.py")


def render_all_realms_map(
    student_id: str,
    journey_summary: dict,
    comp_state: dict
) -> None:
    """
    Renders the 7 Worlds as large destinations connected by a winding adventure path.
    Optimized single-pass query with zero word image loads.
    """
    all_worlds = journey_summary.get("all_worlds") or SEVEN_WORLDS_METADATA
    world_statuses = journey_summary.get("world_statuses", {})
    active_world_id = journey_summary.get("active_world_id")

    comp_info = comp_state.get("stage_info")
    comp_icon = comp_info.icon if comp_info else "🐣"
    comp_name = comp_info.name if comp_info else "Companion"

    st.html(f"""
    <div style="text-align:center; margin-bottom:2rem;">
        <h1 style="font-family:'General Sans', sans-serif; font-size:2.4rem; font-weight:800; color:{TEXT_DARK_PRIMARY}; margin-bottom:0.4rem;">
            🗺️ Realm Journey Map
        </h1>
        <p style="font-family:'General Sans', sans-serif; font-size:1.05rem; color:{TEXT_DARK_SECONDARY}; font-weight:600;">
            Embark across 7 mythical worlds connected by the magical soundway!
        </p>
    </div>
    """)

    st.html("""
    <div class="adventure-canvas">
        <div class="winding-track">
            <div class="path-connector-line"></div>
    """)

    for idx, w in enumerate(all_worlds, start=1):
        w_id = w.get("id", w.get("key", f"w{idx}"))
        w_name = w.get("name", f"World {idx}")
        theme_key = w.get("theme_key", w.get("theme", "village"))
        theme = get_world_theme(theme_key)
        w_icon = w.get("icon", theme.icon)
        w_status = world_statuses.get(w_id, "locked" if idx > 1 else "unlocked")

        is_unlocked = (w_status in ["unlocked", "completed"]) or (idx == 1)
        is_completed = (w_status == "completed")
        is_active = (w_id == active_world_id) or (is_unlocked and not is_completed and not active_world_id)

        card_class = "realm-locked"
        status_badge = '<span class="status-pill pill-locked">🔒 Locked</span>'
        stars_badge = ""

        if is_completed:
            card_class = "realm-completed"
            status_badge = '<span class="status-pill pill-completed">✓ Mastered</span>'
            stars_badge = '<span style="color:#FBBF24; font-size:0.9rem; font-weight:800; margin-left:8px;">⭐⭐⭐</span>'
        elif is_unlocked:
            card_class = "realm-unlocked"
            status_badge = '<span class="status-pill pill-unlocked">✨ Unlocked</span>'

        if is_active:
            card_class += " realm-active"

        comp_tag_html = ""
        if is_active:
            comp_tag_html = f"""
            <div class="floating-companion-tag" style="margin-bottom:8px;">
                <span>{comp_icon}</span>
                <span>{html.escape(comp_name)} is here!</span>
            </div>
            """

        st.html(f"""
        <div class="realm-island {card_class}">
            {comp_tag_html}
            <div class="realm-header">
                <div class="realm-icon">{w_icon}</div>
                <div class="realm-details">
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:{SIDECAR_YELLOW}; text-transform:uppercase; letter-spacing:0.06em;">
                        World {idx} of 7
                    </div>
                    <div class="realm-title">{html.escape(w_name)} {stars_badge}</div>
                    <div style="margin-top:4px;">{status_badge}</div>
                </div>
            </div>
        </div>
        """)

        # Action Button underneath each realm card
        btn_col_l, btn_col_m, btn_col_r = st.columns([1, 2, 1])
        with btn_col_m:
            if is_unlocked:
                btn_type = "primary" if is_active else "secondary"
                btn_txt = f"Explore {html.escape(w_name)} 🚀" if is_active else f"Enter {html.escape(w_name)} ➔"
                if st.button(btn_txt, key=f"btn_enter_world_{w_id}", type=btn_type, use_container_width=True):
                    st.session_state["selected_world_id"] = w_id
                    st.rerun()
            else:
                st.button(f"🔒 {html.escape(w_name)} Locked (Complete World {idx-1})", disabled=True, key=f"btn_locked_w_{w_id}", use_container_width=True)

        # Transition gate between connected worlds along the path
        if idx < len(all_worlds):
            gate_label = f"✨ Gate to World {idx+1}" if is_completed else f"🔒 Gate {idx} ➔ {idx+1}"
            gate_color = AUTHENTIC_TEAL if is_completed else INK_GRAY
            st.html(f"""
            <div style="text-align:center; margin: 0.35rem 0 0.85rem 0;">
                <span style="display:inline-block; padding: 0.25rem 0.85rem; border-radius:9999px; font-family:'General Sans', sans-serif; font-size:0.78rem; font-weight:800; background:#FFFDF5; border:1.5px dashed {gate_color}; color:{gate_color}; box-shadow:0 2px 8px rgba(47,58,58,0.06);">
                    {gate_label}
                </span>
            </div>
            """)

        st.write("")

    st.html("""
        </div>
    </div>
    """)


def render_world_level_map(
    student_id: str,
    world_id: str,
    progression_svc,
    comp_state: dict
) -> None:
    """
    Renders ONE continuous winding 30-level path for a specific world.
    Curated Candy Crush-style aesthetic with clickable circular level nodes.
    """
    world_summary = progression_svc.get_world_progression_summary(student_id, world_id)
    levels = world_summary.get("levels", [])
    active_level_id = world_summary.get("active_level_id")
    completed_count = world_summary.get("completed_levels_count", 0)
    world_stars = world_summary.get("world_stars", 0)

    # Get World Details
    try:
        content_repo = get_content_repository()
        all_worlds = content_repo.get_all_worlds()
    except Exception:
        all_worlds = SEVEN_WORLDS_METADATA
    world_obj = next((w for w in all_worlds if w.get("id") == world_id or w.get("key") == world_id), None)
    world_name = world_obj["name"] if world_obj and "name" in world_obj else "Realm"
    theme = get_world_theme(world_obj.get("theme_key", world_obj.get("theme", "village")) if world_obj else "village")
    
    comp_info = comp_state.get("stage_info")
    comp_icon = comp_info.icon if comp_info else "🐣"
    comp_name = comp_info.name if comp_info else "Companion"

    # Navigation back to 7 Worlds Map
    nav_col1, nav_col2 = st.columns([1.5, 3])
    with nav_col1:
        if st.button("🗺️ All Realms Map", key="btn_back_to_worlds", use_container_width=True):
            st.session_state["selected_world_id"] = None
            st.rerun()

    with nav_col2:
        st.html(f"""
        <div style="display:flex; align-items:center; gap:0.75rem; justify-content:flex-end;">
            <span style="font-size:2rem;">{theme.icon}</span>
            <div>
                <h2 style="font-family:'General Sans', sans-serif; margin:0; font-size:1.4rem; color:{TEXT_DARK_PRIMARY}; font-weight:800;">{html.escape(world_name)}</h2>
                <span style="font-family:'General Sans', sans-serif; font-size:0.85rem; color:{TEXT_DARK_SECONDARY}; font-weight:700;">Progress: {completed_count}/30 Levels Completed • ⭐ {world_stars} Stars</span>
            </div>
        </div>
        """)

    st.divider()

    st.html("""
    <div class="adventure-canvas">
        <div class="winding-track">
            <div class="path-connector-line"></div>
    """)

    # 8-Position Winding S-Curve
    s_curve_classes = [
        "pos-left",
        "pos-mid-left",
        "pos-center",
        "pos-mid-right",
        "pos-right",
        "pos-mid-right",
        "pos-center",
        "pos-mid-left"
    ]

    col_offsets = {
        "pos-left": [0.3, 1.4, 4.3],
        "pos-mid-left": [1.3, 1.4, 3.3],
        "pos-center": [2.3, 1.4, 2.3],
        "pos-mid-right": [3.3, 1.4, 1.3],
        "pos-right": [4.3, 1.4, 0.3]
    }

    for idx, lvl in enumerate(levels):
        lvl_id = lvl["id"]
        lvl_num = lvl.get("order_index", idx + 1)
        is_completed = lvl.get("is_completed", False)
        is_accessible = lvl.get("is_accessible", False)
        stars = lvl.get("stars", 0)
        is_active = (lvl_id == active_level_id) or (not is_completed and is_accessible and not active_level_id)
        is_milestone = (lvl_num % 5 == 0) or (lvl_num == 30)

        pos_class = s_curve_classes[idx % len(s_curve_classes)]
        col_ratios = col_offsets.get(pos_class, [2.3, 1.4, 2.3])

        c_pad_l, c_node, c_pad_r = st.columns(col_ratios)

        with c_node:
            if is_completed:
                star_emojis = "⭐" * max(1, min(3, stars))
                st.html(f"""
                <div style="text-align:center; margin-bottom:-4px;">
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; color:#B45309; font-weight:800;">✓ {star_emojis}</div>
                </div>
                """)
                if st.button(f"{lvl_num}", key=f"node_lvl_{lvl_id}", help=f"Level {lvl_num} Completed (⭐{stars}) • Click to Replay", use_container_width=True):
                    st.session_state["game_mode"] = True
                    st.query_params["level_id"] = lvl_id
                    st.switch_page("pages/5_Play.py")
                st.html(f"""
                <div style="text-align:center; font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:700; color:{TEXT_DARK_PRIMARY}; margin-top:2px;">
                    Level {lvl_num}
                </div>
                """)

            elif is_active or is_accessible:
                milestone_crown = "👑 " if is_milestone else ""
                st.html(f"""
                <div style="text-align:center; margin-bottom:-2px;">
                    <div class="floating-companion-tag">
                        <span>{comp_icon}</span>
                        <span>{html.escape(comp_name)} is here!</span>
                    </div>
                </div>
                """)
                if st.button(f"{milestone_crown}{lvl_num}", key=f"node_lvl_{lvl_id}", type="primary", help=f"Play Level {lvl_num} (You Are Here!)", use_container_width=True):
                    st.session_state["game_mode"] = True
                    st.query_params["level_id"] = lvl_id
                    st.switch_page("pages/5_Play.py")
                st.html(f"""
                <div style="text-align:center; font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:{AUTHENTIC_TEAL}; margin-top:2px;">
                    Level {lvl_num}
                </div>
                """)

            else:
                st.html("""<div style="height:16px;"></div>""")
                st.button("🔒", key=f"node_lvl_{lvl_id}", disabled=True, help=f"Level {lvl_num} (Locked)", use_container_width=True)
                st.html(f"""
                <div style="text-align:center; font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:600; color:{TEXT_DARK_SECONDARY}; margin-top:2px;">
                    Level {lvl_num}
                </div>
                """)

        st.write("")

    st.html("""
        </div>
    </div>
    """)


def main() -> None:
    user, student_id = check_authentication()
    st.session_state["game_mode"] = True

    progression_svc = get_progression_service()
    profiles_repo = get_profiles_repository()
    companion_svc = get_companion_service()

    # 1. Single-Pass Journey Summary Query (<15ms)
    journey_summary = progression_svc.get_student_journey_summary(student_id)
    total_stars = journey_summary.get("total_stars", 0)

    # 2. Student Profile & Score
    profile = profiles_repo.get_profile(student_id) or {}
    total_score = profile.get("total_score", 0)
    current_streak = profile.get("current_streak", 0)

    # 3. Companion State (With Graceful Fallback)
    comp_state = st.session_state.get("cached_companion")
    if not comp_state or comp_state.get("student_id") != student_id:
        try:
            comp_state = companion_svc.get_or_create_companion(student_id)
            st.session_state["cached_companion"] = comp_state
        except Exception:
            comp_state = {"stage": "egg", "xp": 0, "stage_info": None}

    # 4. Streamlined Game Mode Top Bar
    render_gameplay_topbar(comp_state, total_stars, total_score, current_streak)

    # 5. Check if student selected a specific world or should see the 7 Realms Map
    selected_world_id = st.session_state.get("selected_world_id")
    if selected_world_id:
        render_world_level_map(student_id, selected_world_id, progression_svc, comp_state)
    else:
        render_all_realms_map(student_id, journey_summary, comp_state)


if __name__ == "__main__":
    main()
