"""Pronunciation Adventure - Main Application Entrypoint & App Mode Home Dashboard."""
from __future__ import annotations

import html
import logging
import streamlit as st
from config.settings import get_settings, ConfigurationError
from repositories.content_repo import get_content_repository
from repositories.profiles_repo import get_profiles_repository
from repositories.progress_repo import get_progress_repository
from repositories.level_results_repo import get_level_results_repo
from services.auth_service import get_auth_service
from services.profile_service import generate_adventurer_id
from services.progression_service import get_progression_service
from services.companion_service import get_companion_service
from components.sidebar import render_app_sidebar
from config.world_themes import get_world_theme
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

logger = logging.getLogger(__name__)

# 1. Page Configuration
st.set_page_config(
    page_title="Pronunciation Adventure",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Shared Design System CSS
st.html(get_global_css())

# 3. App Mode Home Specific Styling
st.html(f"""
<style>
    /* Hero Banner Card (Authentic Teal Container) */
    .home-hero-card {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.3);
        border-radius: 20px;
        padding: 2rem 2.25rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 32px 0 rgba(3, 83, 82, 0.3);
        position: relative;
        overflow: hidden;
    }}
    
    .home-hero-title {{
        font-family: 'General Sans', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        color: {TEXT_LIGHT_PRIMARY};
        margin-bottom: 0.35rem;
        letter-spacing: -0.01em;
    }}
    
    .home-hero-subtitle {{
        font-family: 'Inter', sans-serif;
        font-size: 1.02rem;
        color: {TEXT_LIGHT_SECONDARY};
        max-width: 680px;
        line-height: 1.55;
    }}

    /* Frontier Adventure Card: Sidecar Yellow / Cream Light Container */
    .frontier-card {{
        background: #FFFDF5;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-radius: 18px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 24px rgba(47, 58, 58, 0.08);
        color: {TEXT_DARK_PRIMARY};
    }}

    .frontier-tag {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        color: {AUTHENTIC_TEAL};
        letter-spacing: 0.08em;
    }}

    .frontier-pill {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.82rem;
        padding: 4px 12px;
        border-radius: 9999px;
        background: {AUTHENTIC_TEAL};
        color: {TEXT_LIGHT_PRIMARY};
        font-weight: 700;
    }}

    .frontier-realm-title {{
        font-family: 'General Sans', sans-serif;
        margin: 0;
        font-size: 1.95rem;
        color: {TEXT_DARK_PRIMARY};
        font-weight: 800;
        letter-spacing: -0.01em;
    }}

    .frontier-realm-sub {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.85rem;
        color: {TEXT_DARK_SECONDARY};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .frontier-progress-strip {{
        background: rgba(3, 83, 82, 0.08);
        border: 1px solid rgba(3, 83, 82, 0.18);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: {TEXT_DARK_PRIMARY};
        font-family: 'General Sans', sans-serif;
    }}

    /* Companion & Dashboard Cards (Authentic Teal) */
    .dashboard-teal-card {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.25);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 6px 20px rgba(3, 83, 82, 0.25);
        color: {TEXT_LIGHT_PRIMARY};
    }}

    /* Stat Mini Boxes (Cream Surface with Ink Gray Border) */
    .stat-box {{
        background: #FFFDF5;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-radius: 12px;
        padding: 0.85rem 1rem;
        text-align: center;
        flex: 1;
        min-width: 105px;
        box-shadow: 0 4px 12px rgba(47, 58, 58, 0.06);
    }}

    .stat-val {{
        font-family: 'General Sans', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: {TEXT_DARK_PRIMARY};
        margin-bottom: 0.15rem;
    }}

    .stat-lbl {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {AUTHENTIC_TEAL};
        font-weight: 700;
    }}

    .badge-student {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(243, 232, 188, 0.18);
        color: {SIDECAR_YELLOW};
        border: 1px solid rgba(243, 232, 188, 0.35);
        margin-bottom: 0.75rem;
        font-family: 'General Sans', sans-serif;
    }}
</style>
""")


def init_session_state() -> None:
    """Initialize defaults for session state."""
    defaults = {
        "authenticated": False,
        "user": None,
        "profile": None,
        "session": None,
        "auth_token": None,
        "game_mode": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def check_configuration() -> bool:
    """Validate settings and return True if configured, False with banner otherwise."""
    try:
        settings = get_settings()
        if not settings.is_configured():
            st.warning(
                "⚙️ **Supabase Setup Required**: Placeholder credentials detected. "
                "Please configure your real `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.streamlit/secrets.toml`."
            )
            return False
        return True
    except ConfigurationError as e:
        st.error(f"⚠️ **Configuration Error**: {e}")
        st.info("💡 Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your Supabase credentials.")
        return False


def find_frontier_level(student_id: str, content_repo, progression_svc) -> tuple[dict, dict, dict]:
    """
    Look up the student's actual current authorized frontier level and queue.
    Uses cached worlds/levels to avoid multiple network hops.
    """
    all_worlds = content_repo.get_all_worlds()
    if not all_worlds:
        return {}, {}, {}

    for w in all_worlds:
        levels = content_repo.get_levels_for_world(w["id"])
        for lvl in levels:
            if progression_svc.can_access_level(student_id, lvl["id"]):
                queue = progression_svc.get_or_init_level_queue(student_id, lvl["id"])
                if not queue["is_level_completed"]:
                    return w, lvl, queue

    # If all in-progress levels are completed, find highest unlocked
    for w in reversed(all_worlds):
        levels = content_repo.get_levels_for_world(w["id"])
        for lvl in reversed(levels):
            if progression_svc.can_access_level(student_id, lvl["id"]):
                queue = progression_svc.get_or_init_level_queue(student_id, lvl["id"])
                return w, lvl, queue

    w1 = all_worlds[0]
    w1_levels = content_repo.get_levels_for_world(w1["id"])
    l1 = w1_levels[0] if w1_levels else {}
    q1 = progression_svc.get_or_init_level_queue(student_id, l1["id"]) if l1 else {}
    return w1, l1, q1


def render_authenticated_view(user: dict, profile: dict | None) -> None:
    """Render landing screen for authenticated students in APP MODE."""
    st.session_state["game_mode"] = False
    student_id = user["id"]

    content_repo = get_content_repository()
    progression_svc = get_progression_service()
    profiles_repo = get_profiles_repository()
    level_results_repo = get_level_results_repo()
    companion_svc = get_companion_service()

    # 1. Load profile data & resolve robust Adventurer ID
    fresh_profile = profile or {}
    try:
        db_prof = profiles_repo.get_profile(student_id)
        if db_prof:
            fresh_profile = db_prof
            st.session_state["profile"] = db_prof
    except Exception as e:
        logger.debug("Could not refresh profile from DB: %s", e)

    raw_display_name = fresh_profile.get("display_name", user.get("email", "Adventurer"))
    raw_username = fresh_profile.get("username", user.get("email", ""))
    total_score = fresh_profile.get("total_score", 0) or 0
    current_streak = fresh_profile.get("current_streak", 0) or 0
    best_streak = fresh_profile.get("best_streak", 0) or 0

    # Ensure Adventurer ID is NEVER "None" or empty
    raw_adv_id = fresh_profile.get("adventurer_id")
    if not raw_adv_id or str(raw_adv_id).lower() in ("none", "null", ""):
        raw_adv_id = generate_adventurer_id(student_id)

    display_name = html.escape(str(raw_display_name))
    username = html.escape(str(raw_username))
    adv_id = html.escape(str(raw_adv_id))

    # 2. Optimized Single-Query Star Calculation
    total_stars = 0
    try:
        all_results = level_results_repo.get_all_level_results(student_id)
        total_stars = sum(int(r.get("stars", 0)) for r in all_results if r.get("stars"))
    except Exception as e:
        logger.debug("Could not query all level results: %s", e)

    # 3. Load Companion State with Graceful Fallback & UI Memoization
    comp_state = st.session_state.get("cached_companion")
    if not comp_state or comp_state.get("student_id") != student_id:
        try:
            comp_state = companion_svc.get_or_create_companion(student_id)
            st.session_state["cached_companion"] = comp_state
        except Exception as e:
            logger.error("Failed to load companion state for student %s: %s", student_id, e)
            comp_state = None

    # 4. Resolve Frontier Level
    current_world, current_level, queue = find_frontier_level(student_id, content_repo, progression_svc)
    frontier_world_name = current_world.get("name", "Village")
    frontier_world_theme = get_world_theme(current_world.get("theme_key"))
    frontier_lvl_num = current_level.get("order_index", 1)
    frontier_diff = str(current_level.get("difficulty_band", "easy")).capitalize()
    all_words = queue.get("all_words", [])
    active_queue = queue.get("active_queue", [])
    words_done = len(all_words) - len(active_queue)
    total_words = max(7, len(all_words))

    # 5. Render App Mode Sidebar ONLY (No duplicate top navigation bar)
    render_app_sidebar(current_page="home", user=user, profile=fresh_profile)

    # 6. Welcome Hero Banner
    adv_id_tag = f" &nbsp;•&nbsp; ID: <code>{adv_id}</code>"
    hero_html = (
        f'<div class="home-hero-card">\n'
        f'<span class="badge-student">✨ Student Dashboard</span>\n'
        f'<h1 class="home-hero-title">Welcome back, {display_name}! 👋</h1>\n'
        f'<p class="home-hero-subtitle">\n'
        f'Logged in as <strong>@{username}</strong>{adv_id_tag}. Ready to conquer your next English pronunciation quest?\n'
        f'</p>\n'
        f'</div>'
    )
    st.html(hero_html)

    # 7. Main Dashboard Layout (2 columns: Adventure Frontier + Companion & Stats)
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        # CURRENT ADVENTURE FRONTIER CARD (Sidecar Yellow Container)
        frontier_html = (
            f'<div class="frontier-card">\n'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem; flex-wrap:wrap; gap:0.5rem;">\n'
            f'<span class="frontier-tag">📍 CURRENT ADVENTURE</span>\n'
            f'<span class="frontier-pill">Level {frontier_lvl_num} • {frontier_diff}</span>\n'
            f'</div>\n'
            f'<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">\n'
            f'<span style="font-size:2.8rem; filter:drop-shadow(0 0 10px rgba(3,83,82,0.3));">{frontier_world_theme.icon}</span>\n'
            f'<div>\n'
            f'<div class="frontier-realm-sub">{html.escape(frontier_world_theme.badge_label)}</div>\n'
            f'<h2 class="frontier-realm-title">{html.escape(frontier_world_name)}</h2>\n'
            f'</div>\n'
            f'</div>\n'
            f'<div class="frontier-progress-strip">\n'
            f'<span style="font-size:0.92rem; font-weight:600;">Progress: <strong>{words_done} of {total_words} words completed</strong></span>\n'
            f'<span style="font-size:0.85rem; font-weight:800; color:{AUTHENTIC_TEAL};">{"✓ Level Complete" if queue.get("is_level_completed") else "▶ In Progress"}</span>\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(frontier_html)

        # Primary vs Secondary Home CTAs
        btn_col1, btn_col2 = st.columns([1.3, 1])
        with btn_col1:
            if st.button("▶ Resume Adventure", type="primary", use_container_width=True, key="home_btn_resume"):
                st.session_state["game_mode"] = True
                if current_level and "id" in current_level:
                    st.query_params["level_id"] = current_level["id"]
                st.switch_page("pages/5_Play.py")

        with btn_col2:
            if st.button("🗺️ Explore Journey Map", use_container_width=True, key="home_btn_explore_map"):
                st.session_state["game_mode"] = True
                st.switch_page("pages/2_Journey_Map.py")

    with col_right:
        # COMPANION CARD (Authentic Teal Container)
        if comp_state and comp_state.get("stage_info"):
            comp_info = comp_state["stage_info"]
            comp_reaction = companion_svc.get_reaction(
                "streak_milestone" if current_streak >= 3 else "success",
                comp_state.get("stage", "egg")
            )
            safe_c_name = html.escape(comp_info.name)
            safe_c_icon = html.escape(comp_info.icon)
            safe_c_desc = html.escape(comp_info.description)
            next_msg = "🌟 Max evolution reached" if not comp_state.get("next_stage") else f"🌱 {comp_state['xp_to_next']} XP to {html.escape(comp_state['next_stage'].name)}"

            companion_card_html = (
                f'<div class="dashboard-teal-card">\n'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">\n'
                f'<span style="font-family:\'General Sans\', sans-serif; font-size:0.78rem; font-weight:800; text-transform:uppercase; color:{SIDECAR_YELLOW}; letter-spacing:0.06em;">🐾 Creature Companion</span>\n'
                f'<span style="font-family:\'General Sans\', sans-serif; font-size:0.88rem; font-weight:800; color:{SIDECAR_YELLOW};">{comp_state["xp"]} XP</span>\n'
                f'</div>\n'
                f'<div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem;">\n'
                f'<span style="font-size:2.8rem; line-height:1;">{safe_c_icon}</span>\n'
                f'<div>\n'
                f'<div style="font-family:\'General Sans\', sans-serif; font-size:1.25rem; font-weight:800; color:{TEXT_LIGHT_PRIMARY};">{safe_c_name}</div>\n'
                f'<div style="font-family:\'Inter\', sans-serif; font-size:0.85rem; color:{TEXT_LIGHT_SECONDARY};">{safe_c_desc}</div>\n'
                f'</div>\n'
                f'</div>\n'
                f'<div style="font-family:\'Inter\', sans-serif; font-size:0.85rem; color:{SIDECAR_YELLOW}; font-style:italic; border-top:1px dashed rgba(243,232,188,0.2); padding-top:0.6rem; margin-top:0.6rem;">\n'
                f'{comp_reaction}\n'
                f'</div>\n'
                f'</div>'
            )
            st.html(companion_card_html)
            st.progress(comp_state["progress_pct"] / 100.0, text=f"Evolution: {comp_state['progress_pct']:.0f}% ({next_msg})")
        else:
            # Graceful Fallback Card when companion temporarily cannot be queried
            fallback_html = (
                f'<div class="dashboard-teal-card" style="text-align:center; padding:1.75rem 1.25rem;">\n'
                f'<div style="font-size:2.8rem; margin-bottom:0.5rem;">🥚</div>\n'
                f'<div style="font-family:\'General Sans\', sans-serif; font-size:1.15rem; font-weight:800; color:{TEXT_LIGHT_PRIMARY}; margin-bottom:0.25rem;">Mystic Companion Nest</div>\n'
                f'<div style="font-family:\'Inter\', sans-serif; font-size:0.85rem; color:{TEXT_LIGHT_SECONDARY}; margin-bottom:1rem;">Your companion is resting in the sound sanctuary.</div>\n'
                f'</div>'
            )
            st.html(fallback_html)
            if st.button("🔄 Wake Companion", use_container_width=True, key="btn_retry_companion"):
                st.session_state.pop("cached_companion", None)
                st.rerun()

        st.write("")

        # STATS OVERVIEW CARDS (Cream Surfaces with Dark Text & Teal Labels)
        stats_html = (
            f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap;">\n'
            f'<div class="stat-box">\n'
            f'<div class="stat-val" style="color:#C2410C;">🔥 {current_streak}</div>\n'
            f'<div class="stat-lbl">Streak</div>\n'
            f'</div>\n'
            f'<div class="stat-box">\n'
            f'<div class="stat-val" style="color:#B91C1C;">✨ {best_streak}</div>\n'
            f'<div class="stat-lbl">Best Streak</div>\n'
            f'</div>\n'
            f'<div class="stat-box">\n'
            f'<div class="stat-val" style="color:#B45309;">🏆 {total_score}</div>\n'
            f'<div class="stat-lbl">Score</div>\n'
            f'</div>\n'
            f'<div class="stat-box">\n'
            f'<div class="stat-val" style="color:{AUTHENTIC_TEAL};">⭐ {total_stars}</div>\n'
            f'<div class="stat-lbl">Stars</div>\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(stats_html)


def render_unauthenticated_view() -> None:
    """Render landing screen for visitors."""
    # Hide sidebar for visitors
    st.html("""
    <style>
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
    """)

    hero_html = (
        f'<div class="home-hero-card">\n'
        f'<span class="badge-student">🌟 Interactive English Learning</span>\n'
        f'<h1 class="home-hero-title">Pronunciation Adventure 🎙️</h1>\n'
        f'<p class="home-hero-subtitle">\n'
        f'Embark on a sound-guided journey across unique fantasy worlds! Master English pronunciation, '
        f'unlock creature companions, earn stars, and level up your skills.\n'
        f'</p>\n'
        f'</div>'
    )
    st.html(hero_html)

    col1, col2 = st.columns(2)

    with col1:
        returning_html = (
            f'<div class="dashboard-teal-card">\n'
            f'<h3 style="margin-top:0; font-family:\'General Sans\', sans-serif; color:{TEXT_LIGHT_PRIMARY};">🔑 Returning Student?</h3>\n'
            f'<p style="font-family:\'Inter\', sans-serif; color:{TEXT_LIGHT_SECONDARY};">Log in to resume your pronunciation quest right where you left off.</p>\n'
            f'</div>'
        )
        st.html(returning_html)
        if st.button("Log In to Account", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Login.py")

    with col2:
        new_user_html = (
            f'<div class="dashboard-teal-card">\n'
            f'<h3 style="margin-top:0; font-family:\'General Sans\', sans-serif; color:{TEXT_LIGHT_PRIMARY};">🚀 New Adventurer?</h3>\n'
            f'<p style="font-family:\'Inter\', sans-serif; color:{TEXT_LIGHT_SECONDARY};">Create your student adventurer profile to begin your sound journey.</p>\n'
            f'</div>'
        )
        st.html(new_user_html)
        if st.button("Create New Account", use_container_width=True, type="primary"):
            st.switch_page("pages/7_Signup.py")


def main() -> None:
    init_session_state()
    is_ready = check_configuration()

    if not is_ready:
        st.stop()

    auth_service = get_auth_service()

    # Re-validate session if flagged authenticated or check active session
    if not st.session_state.get("authenticated"):
        session_info = auth_service.get_current_session()
        if session_info and session_info.success and session_info.user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = session_info.user
            st.session_state["profile"] = session_info.profile
            if session_info.session and session_info.session.get("access_token"):
                st.session_state["auth_token"] = session_info.session["access_token"]
                st.session_state["session"] = session_info.session

    if st.session_state.get("authenticated") and st.session_state.get("user"):
        render_authenticated_view(st.session_state["user"], st.session_state.get("profile"))
    else:
        render_unauthenticated_view()


if __name__ == "__main__":
    main()
