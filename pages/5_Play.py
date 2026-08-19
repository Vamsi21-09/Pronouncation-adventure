"""Pronunciation Adventure - Main Gameplay Screen with Streamlined HUD, Word Hierarchy, and Celebration."""
from __future__ import annotations

import html
import logging
import random
import time
import streamlit as st

logger = logging.getLogger(__name__)
from config.settings import get_settings, ConfigurationError
from repositories.content_repo import get_content_repository
from repositories.progress_repo import get_progress_repository
from repositories.profiles_repo import get_profiles_repository
from repositories.level_results_repo import get_level_results_repo
from services.auth_service import get_auth_service
from services.progression_service import get_progression_service
from services.override_service import get_override_service
from services.image_service import get_image_service
from services.speech_service import get_speech_service
from services.scoring_service import get_scoring_service, ScoreResult
from services.game_progress_service import get_game_progress_service
from services.companion_service import get_companion_service
from services.treasure_service import get_treasure_service
from services.badge_service import get_badge_service
from services.mystery_service import get_mystery_service
from repositories.attempts_repo import get_attempts_repository
from components.web_speech import render_web_speech_recorder, render_fallback_audio_recorder
from components.audio_playback import render_hear_word_button, get_hear_word_button_html
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

# 1. Page Config (Game Mode)
st.set_page_config(
    page_title="Play Adventure - Pronunciation Adventure",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inject Shared Design System CSS
st.html(get_global_css())

# 3. Custom CSS for Game Mode in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    /* Collapse Streamlit Sidebar & Header in Game Mode */
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

    /* Gameplay Sticky Top Bar (Authentic Teal) */
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

    /* Target Word Hero Display: Warm Surface Container */
    .target-word-card {{
        background: #FFFDF5;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-radius: 20px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 28px rgba(47, 58, 58, 0.08);
        color: {TEXT_DARK_PRIMARY};
    }}

    .target-word-heading {{
        font-family: 'General Sans', sans-serif;
        font-size: 3.4rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        color: {TEXT_DARK_PRIMARY} !important;
        margin: 0.2rem 0;
        line-height: 1.1;
    }}

    .phonetic-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        background: {AUTHENTIC_TEAL};
        color: {TEXT_LIGHT_PRIMARY};
        border: 1px solid rgba(3, 83, 82, 0.4);
        font-family: 'General Sans', sans-serif;
        font-size: 0.92rem;
        font-weight: 700;
        margin-right: 0.5rem;
    }}

    .syllable-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        background: {SIDECAR_YELLOW_LIGHT};
        color: {TEXT_DARK_PRIMARY};
        border: 1.5px solid {INK_GRAY_BORDER};
        font-family: 'General Sans', sans-serif;
        font-size: 0.92rem;
        font-weight: 700;
    }}

    .meaning-box {{
        background: #FFFDF5;
        padding: 0.85rem 1.15rem;
        border-radius: 12px;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-left: 5px solid {AUTHENTIC_TEAL};
        margin-bottom: 0.75rem;
        color: {TEXT_DARK_PRIMARY};
        box-shadow: 0 2px 8px rgba(47, 58, 58, 0.06);
    }}

    .meaning-title {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        color: {AUTHENTIC_TEAL};
        font-weight: 800;
        margin-bottom: 0.15rem;
        letter-spacing: 0.05em;
    }}

    .meaning-text {{
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: {TEXT_DARK_PRIMARY};
        line-height: 1.45;
    }}

    .example-sentence {{
        font-family: 'Inter', sans-serif;
        color: {TEXT_DARK_SECONDARY};
        font-style: italic;
        font-size: 0.96rem;
        margin-bottom: 1rem;
    }}

    /* Compact Word Progress Header */
    .word-progress-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }}

    /* Progress Dots */
    .progress-dots-row {{
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }}

    .progress-dot {{
        width: 14px;
        height: 14px;
        border-radius: 50%;
        transition: all 0.2s ease;
    }}

    .dot-completed {{
        background: #10B981;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    }}

    .dot-active {{
        background: {SIDECAR_YELLOW};
        transform: scale(1.3);
        box-shadow: 0 0 10px rgba(243, 232, 188, 0.8);
    }}

    .dot-skipped {{
        background: #F59E0B;
    }}

    .dot-pending {{
        background: rgba(2, 53, 53, 0.8);
        border: 1px solid rgba(243, 232, 188, 0.2);
    }}

    /* Celebration Card (Authentic Teal + Sidecar Yellow Highlights) */
    .celebration-card {{
        background: linear-gradient(135deg, rgba(3, 83, 82, 0.95) 0%, rgba(2, 53, 53, 0.98) 100%);
        border: 2px solid {SIDECAR_YELLOW};
        border-radius: 24px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(243, 232, 188, 0.25);
        margin-bottom: 2rem;
        color: {TEXT_LIGHT_PRIMARY};
    }}

    .stars-display {{
        font-family: 'General Sans', sans-serif;
        font-size: 3.5rem;
        letter-spacing: 0.5rem;
        margin: 0.75rem 0;
        filter: drop-shadow(0 0 12px rgba(245, 158, 11, 0.8));
        animation: starPulse 2s infinite ease-in-out;
    }}

    @keyframes starPulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.08); }}
    }}

    .celebration-stat-box {{
        background: rgba(2, 40, 40, 0.7);
        border: 1px solid rgba(243, 232, 188, 0.2);
        border-radius: 12px;
        padding: 0.85rem 1.15rem;
        min-width: 120px;
    }}
</style>
""")

MOTIVATIONAL_MESSAGES = [
    "🌟 Outstanding pronunciation adventure! Your sound mastery is shining bright.",
    "🎉 Magnificent progress! You conquered every single word in this realm.",
    "🚀 Superb effort! You're speaking with great confidence and precision.",
    "🏆 Brilliant work, Adventurer! Your phonetics skills are leveling up rapidly.",
    "✨ Fantastic victory! You brought every sound to life with remarkable clarity."
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
        st.warning("🔒 Please log in to enter your pronunciation adventure.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/1_Login.py")
        st.stop()

    return user, user["id"]


def resolve_active_level(student_id: str, content_repo, progression_svc) -> tuple[dict, dict]:
    """
    Determine the level to play:
    1. If level_id is provided in query params, check authorization.
    2. Otherwise, find the current in-progress or highest accessible level.
    """
    all_worlds = content_repo.get_all_worlds()
    if not all_worlds:
        st.error("No worlds found in curriculum. Please run the content seeder.")
        st.stop()

    requested_level_id = st.query_params.get("level_id")
    
    if requested_level_id:
        can_access = progression_svc.can_access_level(student_id, requested_level_id)
        if can_access:
            for w in all_worlds:
                levels = content_repo.get_levels_for_world(w["id"])
                for lvl in levels:
                    if lvl["id"] == requested_level_id:
                        return w, lvl
        else:
            st.warning("🔒 **Level Locked**: You do not have access to that level yet. Directing to your current level.")

    for w in all_worlds:
        levels = content_repo.get_levels_for_world(w["id"])
        for lvl in levels:
            if progression_svc.can_access_level(student_id, lvl["id"]):
                queue = progression_svc.get_or_init_level_queue(student_id, lvl["id"])
                if not queue["is_level_completed"]:
                    return w, lvl

    for w in reversed(all_worlds):
        levels = content_repo.get_levels_for_world(w["id"])
        for lvl in reversed(levels):
            if progression_svc.can_access_level(student_id, lvl["id"]):
                return w, lvl

    w1 = all_worlds[0]
    w1_levels = content_repo.get_levels_for_world(w1["id"])
    return w1, w1_levels[0]


def render_celebration_overlay(
    current_world: dict,
    current_level: dict,
    level_result: dict,
    student_id: str,
    content_repo,
    progression_svc
) -> None:
    """
    Renders full level celebration overlay with stars, stats, companion XP, rewards,
    and a 5-second countdown timer for the Continue button.
    """
    lvl_id = current_level["id"]
    lvl_num = current_level["order_index"]
    safe_world_name = html.escape(current_world["name"])

    stars_count = int(level_result.get("stars", 1))
    score = int(level_result.get("score", 0))
    accuracy = float(level_result.get("accuracy", 100.0))
    words_completed = int(level_result.get("words_completed", 7))
    mistakes = int(level_result.get("mistakes", 0))
    streak_comp = int(level_result.get("streak_at_completion", 0))

    stars_icons = "⭐" * stars_count + "☆" * (3 - stars_count)
    star_label = "3-Star Flawless Master!" if stars_count == 3 else ("2-Star Great Pronunciation!" if stars_count == 2 else "1-Star Level Complete!")

    quote_idx = (lvl_num + stars_count) % len(MOTIVATIONAL_MESSAGES)
    quote = MOTIVATIONAL_MESSAGES[quote_idx]

    # Gamification Rewards Lookup
    companion_svc = get_companion_service()
    comp_state = companion_svc.get_or_create_companion(student_id)
    comp_info = comp_state["stage_info"]
    xp_gain = 50 + (stars_count * 25)

    treasure_svc = get_treasure_service()
    treas_res = treasure_svc.open_treasure(student_id, lvl_id)
    opened_reward = treas_res.get("reward") if treas_res else None

    mystery_svc = get_mystery_service()
    mystery_res = mystery_svc.maybe_trigger_mystery(student_id, lvl_id)

    rewards_html_parts = []
    
    # Companion XP Banner
    rewards_html_parts.append(
        f'<div style="background:rgba(3,83,82,0.85); border:1.5px solid rgba(243,232,188,0.3); border-radius:14px; padding:0.85rem 1.25rem; margin-bottom:0.75rem; text-align:left; display:flex; align-items:center; gap:1rem;">\n'
        f'<span style="font-size:2rem;">{comp_info.icon}</span>\n'
        f'<div>\n'
        f'<div style="font-size:0.8rem; font-weight:700; color:{SIDECAR_YELLOW}; text-transform:uppercase;">Companion Power Surge • +{xp_gain} XP</div>\n'
        f'<div style="font-size:0.95rem; color:{TEXT_LIGHT_PRIMARY}; font-weight:600;">{comp_info.name} (Total: {comp_state["xp"]} XP) — {companion_svc.get_reaction("level_complete", comp_state["stage"])}</div>\n'
        f'</div>\n'
        f'</div>'
    )

    # Treasure Chest Banner
    if opened_reward:
        r_name = html.escape(opened_reward.get("name", "Mystery Relic"))
        r_rarity = html.escape(opened_reward.get("rarity", "common").upper())
        r_type = html.escape(opened_reward.get("type", "item").capitalize())
        rewards_html_parts.append(
            f'<div style="background:rgba(201,162,39,0.25); border:1.5px solid #FBBF24; border-radius:14px; padding:0.85rem 1.25rem; margin-bottom:0.75rem; text-align:left; display:flex; align-items:center; gap:1rem;">\n'
            f'<span style="font-size:2rem;">🎁</span>\n'
            f'<div>\n'
            f'<div style="font-size:0.8rem; font-weight:700; color:{SIDECAR_YELLOW}; text-transform:uppercase;">Treasure Chest Opened! • {r_rarity} {r_type}</div>\n'
            f'<div style="font-size:1.05rem; color:{TEXT_LIGHT_PRIMARY}; font-weight:800;">✨ Discovered: {r_name}</div>\n'
            f'</div>\n'
            f'</div>'
        )

    # Mystery Surprise Banner
    if mystery_res and mystery_res.get("triggered"):
        m_info = mystery_res.get("info")
        if m_info:
            rewards_html_parts.append(
                f'<div style="background:rgba(3,83,82,0.85); border:1.5px solid rgba(243,232,188,0.3); border-radius:14px; padding:0.85rem 1.25rem; margin-bottom:0.75rem; text-align:left; display:flex; align-items:center; gap:1rem;">\n'
                f'<span style="font-size:2.2rem;">{m_info.icon}</span>\n'
                f'<div>\n'
                f'<div style="font-size:0.8rem; font-weight:700; color:{SIDECAR_YELLOW}; text-transform:uppercase;">Surprise Encounter • {html.escape(m_info.name)}</div>\n'
                f'<div style="font-size:0.95rem; color:{TEXT_LIGHT_PRIMARY};">{html.escape(m_info.message)}</div>\n'
                f'</div>\n'
                f'</div>'
            )

    combined_rewards_html = "\n".join(rewards_html_parts)

    card_html = (
        f'<div class="celebration-card">\n'
        f'<div style="font-size:3.5rem; margin-bottom:0.5rem;">🎉 🏆 🎊</div>\n'
        f'<h1 style="color:{TEXT_LIGHT_PRIMARY}; margin-bottom:0.25rem; font-size:2.6rem; font-weight:900;">LEVEL {lvl_num} COMPLETE!</h1>\n'
        f'<div style="color:{SIDECAR_YELLOW}; font-weight:800; font-size:1.15rem; text-transform:uppercase; letter-spacing:0.05em;">{star_label}</div>\n'
        f'<div class="stars-display">{stars_icons}</div>\n'
        f'<p style="color:{TEXT_LIGHT_SECONDARY}; font-size:1.15rem; max-width:650px; margin:0 auto 1.5rem auto; line-height:1.5;">\n'
        f'{quote}\n'
        f'</p>\n'
        f'<div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem;">\n'
        f'<div class="celebration-stat-box">\n'
        f'<div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; text-transform:uppercase; font-weight:700;">Level Score</div>\n'
        f'<div style="font-size:1.3rem; font-weight:800; color:#FBBF24;">⭐ +{score}</div>\n'
        f'</div>\n'
        f'<div class="celebration-stat-box">\n'
        f'<div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; text-transform:uppercase; font-weight:700;">Accuracy</div>\n'
        f'<div style="font-size:1.3rem; font-weight:800; color:#34D399;">🎯 {accuracy:.1f}%</div>\n'
        f'</div>\n'
        f'<div class="celebration-stat-box">\n'
        f'<div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; text-transform:uppercase; font-weight:700;">Words</div>\n'
        f'<div style="font-size:1.3rem; font-weight:800; color:#38BDF8;">✓ {words_completed}</div>\n'
        f'</div>\n'
        f'<div class="celebration-stat-box">\n'
        f'<div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; text-transform:uppercase; font-weight:700;">Mistakes</div>\n'
        f'<div style="font-size:1.3rem; font-weight:800; color:#F87171;">⚠️ {mistakes}</div>\n'
        f'</div>\n'
        f'<div class="celebration-stat-box">\n'
        f'<div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; text-transform:uppercase; font-weight:700;">Final Streak</div>\n'
        f'<div style="font-size:1.3rem; font-weight:800; color:#F59E0B;">🔥 {streak_comp}</div>\n'
        f'</div>\n'
        f'</div>\n'
        f'<div style="max-width:700px; margin:0 auto 1.5rem auto;">\n'
        f'{combined_rewards_html}\n'
        f'</div>\n'
        f'</div>'
    )
    st.html(card_html)

    # 5-Second Timer Enforcement for Continue Button
    timer_key = f"level_comp_timestamp_{lvl_id}"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time()

    elapsed = time.time() - st.session_state[timer_key]
    time_remaining = max(0, int(5 - elapsed))
    is_ready = time_remaining <= 0

    # Resolve Next Level
    world_levels = content_repo.get_levels_for_world(current_world["id"])
    next_level = next((l for l in world_levels if l.get("order_index") == current_level["order_index"] + 1), None)

    all_worlds = content_repo.get_all_worlds()
    curr_world_idx = current_world.get("order_index", 1)
    next_world = next((w for w in all_worlds if w.get("order_index") == curr_world_idx + 1), None)

    col1, col2 = st.columns([1, 1])

    with col1:
        if next_level:
            button_label = f"Continue to Level {next_level['order_index']} ➡️" if is_ready else f"Continue to Level {next_level['order_index']} ({time_remaining}s)..."
            if st.button(button_label, type="primary", use_container_width=True, disabled=not is_ready):
                if timer_key in st.session_state:
                    del st.session_state[timer_key]
                st.query_params["level_id"] = next_level["id"]
                st.rerun()
        elif next_world and progression_svc.can_access_level(student_id, (content_repo.get_levels_for_world(next_world["id"]) or [{}])[0].get("id", "")):
            button_label = f"Journey to {next_world['name']} 🌍" if is_ready else f"Journey to {next_world['name']} ({time_remaining}s)..."
            if st.button(button_label, type="primary", use_container_width=True, disabled=not is_ready):
                if timer_key in st.session_state:
                    del st.session_state[timer_key]
                st.session_state["celebrate_unlocked_world"] = next_world["id"]
                st.session_state["celebrate_unlocked_world_name"] = next_world["name"]
                st.session_state["celebrate_unlocked_world_theme"] = next_world.get("theme_key", "forest")
                st.switch_page("pages/2_Journey_Map.py")
        else:
            st.info("🌟 **End of Curriculum Content**: You have completed all currently available adventure stages!")

    with col2:
        if st.button("Return to Journey Map 🗺️", use_container_width=True):
            if timer_key in st.session_state:
                del st.session_state[timer_key]
            st.switch_page("pages/2_Journey_Map.py")

    if not is_ready:
        time.sleep(1)
        st.rerun()


def main() -> None:
    user, student_id = check_authentication()
    st.session_state["game_mode"] = True

    content_repo = get_content_repository()
    progress_repo = get_progress_repository()
    progression_svc = get_progression_service()
    override_svc = get_override_service()
    image_svc = get_image_service()
    speech_svc = get_speech_service()
    scoring_svc = get_scoring_service()
    attempts_repo = get_attempts_repository()
    profiles_repo = get_profiles_repository()
    game_progress_svc = get_game_progress_service()
    companion_svc = get_companion_service()

    # 1. Resolve authorized level
    current_world, current_level = resolve_active_level(student_id, content_repo, progression_svc)
    current_world_id = current_world["id"]
    current_level_id = current_level["id"]
    lvl_num = current_level["order_index"]

    # 2. World Theme Configuration
    theme = get_world_theme(current_world.get("theme_key"))

    # 3. Load latest profile & companion for HUD
    profile = profiles_repo.get_profile(student_id) or {}
    current_streak = profile.get("current_streak", 0) or 0
    comp_state = companion_svc.get_or_create_companion(student_id)
    comp_info = comp_state["stage_info"]

    # 4. Streamlined Gameplay Top Bar:
    # 🐦 Companion • World • Level • 🔥 Current Streak • 🚪 Exit
    with st.container(border=True):
        col_c, col_w, col_s, col_exit = st.columns([1.3, 1.8, 1, 1.1])
        
        with col_c:
            st.html(f"""
            <div style="display:flex; align-items:center; gap:0.65rem; padding:0.1rem 0;">
                <span style="font-size:2.2rem; line-height:1;">{comp_info.icon}</span>
                <div>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:#035352; text-transform:uppercase; letter-spacing:0.08em;">Companion</div>
                    <div style="font-family:'General Sans', sans-serif; font-size:1.12rem; font-weight:800; color:#102A2A;">{html.escape(comp_info.name)}</div>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.82rem; font-weight:700; color:#365656;">{comp_state.get('xp', 0)} XP</div>
                </div>
            </div>
            """)

        with col_w:
            st.html(f"""
            <div style="display:flex; align-items:center; gap:0.65rem; padding:0.1rem 0;">
                <span style="font-size:2.2rem; line-height:1;">{theme.icon}</span>
                <div>
                    <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:#035352; text-transform:uppercase; letter-spacing:0.08em;">{html.escape(theme.badge_label)}</div>
                    <div style="font-family:'General Sans', sans-serif; font-size:1.12rem; font-weight:800; color:#102A2A;">{html.escape(current_world['name'])} &bull; Level {lvl_num}</div>
                </div>
            </div>
            """)

        with col_s:
            st.html(f"""
            <div style="text-align:center; padding:0.1rem 0;">
                <div style="font-family:'General Sans', sans-serif; font-size:1.3rem; font-weight:800; color:#D97706;">🔥 {current_streak}</div>
                <div style="font-family:'General Sans', sans-serif; font-size:0.75rem; font-weight:800; color:#035352; text-transform:uppercase; letter-spacing:0.08em;">Streak</div>
            </div>
            """)

        with col_exit:
            if st.button("🚪 Exit Game", use_container_width=True, key="gameplay_exit_btn", help="Return to Home Dashboard"):
                st.session_state["game_mode"] = False
                st.switch_page("app.py")

    # 5. Milestone Alert Toast (if triggered)
    milestone_msg = st.session_state.pop("streak_milestone_alert", None)
    if milestone_msg:
        st.toast(milestone_msg, icon="🔥")

    # 6. Fetch Level Word Queue
    queue_state = progression_svc.get_or_init_level_queue(student_id, current_level_id)
    all_words = queue_state["all_words"]
    is_level_completed = queue_state["is_level_completed"]

    if not all_words:
        st.warning("⚠️ No words found in this level.")
        return

    # Check if student explicitly completed level and celebration is queued
    celebration_key = f"celebrate_level_{current_level_id}"
    if is_level_completed and st.session_state.get(celebration_key):
        level_result = game_progress_svc.complete_level_with_results(student_id, current_level_id)
        render_celebration_overlay(current_world, current_level, level_result, student_id, content_repo, progression_svc)
        return

    # 7. Word View Index in Level (0-indexed across all_words)
    idx_key = f"view_word_idx_{current_level_id}"
    if idx_key not in st.session_state or st.session_state[idx_key] >= len(all_words):
        # Default to first pending/uncompleted word in level, or Word 1 (index 0)
        default_idx = next(
            (i for i, w in enumerate(all_words) if w.get("progress_status") not in ("completed", "resolved_by_override")),
            0
        )
        st.session_state[idx_key] = default_idx

    view_idx = st.session_state[idx_key]
    active_word = all_words[view_idx]
    word_id = active_word["id"]
    active_index_in_level = view_idx + 1
    total_w = len(all_words)
    is_word_already_done = active_word.get("progress_status") in ("completed", "resolved_by_override")

    # Compact Progress Header: Word X of 7 + Dots (● ● ● ○ ○ ○ ○)
    dots_html = ["<div class='progress-dots-row'>"]
    for idx_w, w in enumerate(all_words):
        st_val = w.get("progress_status", "pending")
        if idx_w == view_idx:
            dots_html.append("<span class='progress-dot dot-active' title='Current Word'></span>")
        elif st_val in ("completed", "resolved_by_override"):
            dots_html.append("<span class='progress-dot dot-completed' title='Completed'></span>")
        elif st_val == "skipped":
            dots_html.append("<span class='progress-dot dot-skipped' title='Skipped'></span>")
        else:
            dots_html.append("<span class='progress-dot dot-pending' title='Pending'></span>")
    dots_html.append("</div>")

    prog_header_html = (
        f'<div class="word-progress-header">\n'
        f'<span style="font-size:0.95rem; font-weight:800; color:{AUTHENTIC_TEAL}; text-transform:uppercase; letter-spacing:0.05em;">\n'
        f'Word {active_index_in_level} of {total_w}\n'
        f'</span>\n'
        f'{"".join(dots_html)}\n'
        f'</div>'
    )
    st.html(prog_header_html)

    # 9. Word Presentation Hierarchy
    # 1. Word X of 7 + progress dots (rendered above)
    # 2. TARGET WORD (large typography)
    # 3. IMAGE
    # 4. SHORT MEANING
    # 5. REAL-LIFE EXAMPLE
    # 6. PRONUNCIATION HINT & SYLLABLES
    # 7. 🎙️ SPEAK NOW

    col_img, col_content = st.columns([1, 2])

    with col_img:
        image_svc.display_word_image(
            image_path=active_word.get("image_path"),
            word_text=active_word["text"],
            alt_text=active_word.get("image_alt_text", ""),
            theme_icon=theme.icon,
            accent_color=theme.accent_color
        )

    with col_content:
        safe_word_text = html.escape(active_word['text'].upper())
        safe_hint = html.escape(active_word.get('pronunciation_hint', ''))
        safe_syllables = html.escape(active_word.get('syllable_breakdown', active_word['text']))
        safe_meaning = html.escape(active_word.get('meaning', ''))
        safe_sentence = html.escape(active_word.get('example_sentence', ''))
        accent_hex = theme.accent_color

        # Header Row: Target Vocabulary Word + Hear Word Audio Button directly beside each other
        col_w_title, col_w_hear = st.columns([1.6, 1.2])
        with col_w_title:
            st.html(f'<h1 class="target-word-heading" style="margin:0.2rem 0;">{safe_word_text}</h1>')
        with col_w_hear:
            render_hear_word_button(active_word["text"], key=f"hear_btn_{word_id}")

        word_card_html = (
            f'<div class="target-word-card" style="padding-top:1.25rem;">\n'
            f'<div style="margin-bottom:1rem;">\n'
            f'<span class="phonetic-chip">🗣️ {safe_hint}</span>\n'
            f'<span class="syllable-chip">🧩 {safe_syllables}</span>\n'
            f'</div>\n'
            f'<div class="meaning-box">\n'
            f'<div class="meaning-title">Meaning</div>\n'
            f'<div class="meaning-text">{safe_meaning}</div>\n'
            f'</div>\n'
            f'<div class="example-sentence">\n'
            f'"{safe_sentence}"\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(word_card_html)

        # Primary Microphone Component: 🎙️ Speak Now
        web_speech_res = render_web_speech_recorder(
            target_word=active_word["text"],
            button_label="🎙️ Speak Now",
            key=f"speech_rec_{word_id}"
        )

        if web_speech_res:
            res_ts = web_speech_res.timestamp
            last_ts_key = f"last_ws_ts_{word_id}"

            if res_ts is None or res_ts != st.session_state.get(last_ts_key):
                st.session_state[last_ts_key] = res_ts
                logger.info(
                    "[EVENT_TRACE] PYTHON_COMPONENT_RESULT_RECEIVED: attempt_id=%s, text='%s', error=%s, is_usable=%s",
                    web_speech_res.attempt_id, web_speech_res.text, web_speech_res.error, web_speech_res.is_usable()
                )

                if web_speech_res.is_usable():
                    logger.info("[EVENT_TRACE] TRANSCRIPT_RECEIVED: '%s'", web_speech_res.text)
                    logger.info(
                        "[EVENT_TRACE] SCORING_CALLED: target='%s', transcript='%s', attempt_id=%s",
                        active_word["text"], web_speech_res.text, web_speech_res.attempt_id
                    )
                    score_res = scoring_svc.score_pronunciation(
                        target=active_word["text"],
                        transcript=web_speech_res.text,
                        fallback_mistake=active_word.get("common_mistake")
                    )
                    attempts_repo.record_attempt(
                        student_id=student_id,
                        word_id=word_id,
                        level_id=current_level_id,
                        transcribed_text=web_speech_res.text,
                        score=score_res.score,
                        passed=score_res.passed
                    )
                    st.session_state[f"last_score_{word_id}"] = (score_res, web_speech_res.text)
                    logger.info(
                        "[EVENT_TRACE] SCORING_RETURNED: target='%s', score=%s, passed=%s",
                        active_word["text"], score_res.score, score_res.passed
                    )

                    if score_res.passed:
                        # Only record points/streak/completion if word was not already completed
                        if not is_word_already_done:
                            succ_res = game_progress_svc.record_word_success(
                                student_id=student_id,
                                word_id=word_id,
                                level_id=current_level_id,
                                pronunciation_score=score_res.score
                            )
                            if succ_res.get("is_milestone"):
                                st.session_state["streak_milestone_alert"] = f"🔥 Streak Boost! {succ_res['current_streak']} in a row! ⭐ +{succ_res['points_awarded']} pts"
                    else:
                        if not is_word_already_done:
                            game_progress_svc.update_streak(student_id, passed=False)
                else:
                    logger.info(
                        "[EVENT_TRACE] ATTEMPT_FAILED: error='%s', attempt_id=%s",
                        web_speech_res.error, web_speech_res.attempt_id
                    )
                    st.warning(f"⚠️ {web_speech_res.error or 'Could not recognize speech. Please try speaking again.'}")

        # Show past attempt badge if word was already completed and no current eval in session
        last_eval = st.session_state.get(f"last_score_{word_id}")
        if not last_eval and is_word_already_done:
            attempts = attempts_repo.get_attempts_for_word(student_id, word_id)
            latest_att = attempts[-1] if attempts else None
            score_num = latest_att.get("score", 100) if latest_att else 100
            st.html(f"""
            <div style="background:#FAF5DC; border:1.5px solid #10B981; border-radius:12px; padding:0.65rem 1rem; margin:0.75rem 0; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:800; color:#035352;">✓ Completed Word</span>
                    <span style="color:#2F3A3A; font-size:0.9rem; margin-left:0.5rem; font-weight:700;">Score: {score_num}/100</span>
                </div>
                <div style="font-size:0.85rem; color:#365656; font-style:italic;">
                    Ready for practice pronunciation anytime
                </div>
            </div>
            """)

        # PRONUNCIATION RESULT UI (Score, Feedback, Correction, Action)
        if last_eval:
            score_res, heard_text = last_eval
            safe_target = html.escape(active_word["text"].upper())
            safe_heard = html.escape(str(heard_text).upper())
            safe_diff = html.escape(str(score_res.bracketed_diff))
            safe_feedback = html.escape(str(score_res.feedback)).replace("\n", "<br>")

            if score_res.passed:
                # EXACT SUCCESS: 100/100 or passing score
                card_border = "#10B981"
                badge_lbl = "🌟 PASSED (100/100)" if score_res.score == 100 else f"✓ PASSED ({score_res.score}/100)"
            else:
                card_border = "#D97706"
                badge_lbl = f"💪 TRY AGAIN ({score_res.score}/100)"

            diff_html = ""
            if safe_diff and safe_diff.strip() and safe_diff.upper() != safe_target:
                diff_html = (
                    f'<div style="margin-bottom:0.5rem;">\n'
                    f'<span style="font-size:0.8rem; text-transform:uppercase; color:{TEXT_DARK_SECONDARY}; font-weight:700;">Word Alignment: </span>\n'
                    f'<span style="font-size:1.15rem; font-weight:800; font-family:monospace; color:{TEXT_DARK_PRIMARY};">{safe_diff}</span>\n'
                    f'</div>'
                )

            feedback_box = (
                f'<div style="background:#FFFDF5; border:2px solid {card_border}; border-radius:14px; padding:1.15rem 1.35rem; margin:1rem 0; box-shadow:0 4px 16px rgba(47,58,58,0.08);">\n'
                f'<div style="font-size:1.15rem; font-weight:800; color:{card_border}; margin-bottom:0.5rem;">\n'
                f'{badge_lbl}\n'
                f'</div>\n'
                f'<div style="display:flex; gap:1.5rem; margin-bottom:0.5rem; flex-wrap:wrap;">\n'
                f'<div style="font-size:0.9rem; color:{TEXT_DARK_SECONDARY};"><strong>Target:</strong> <span style="color:{TEXT_DARK_PRIMARY}; font-weight:700;">{safe_target}</span></div>\n'
                f'<div style="font-size:0.9rem; color:{TEXT_DARK_SECONDARY};"><strong>You said:</strong> <span style="color:#C2410C; font-weight:700;">{safe_heard}</span></div>\n'
                f'</div>\n'
                f'{diff_html}\n'
                f'<div style="font-size:0.95rem; color:{TEXT_DARK_PRIMARY}; line-height:1.5;">{safe_feedback}</div>\n'
                f'</div>'
            )
            st.html(feedback_box)

            if score_res.passed:
                next_btn_label = "➡️ Continue to Next Word" if view_idx < len(all_words) - 1 else "🌟 Complete Level & See Results!"
                if st.button(next_btn_label, type="primary", use_container_width=True, key=f"btn_next_w_{word_id}"):
                    if f"last_score_{word_id}" in st.session_state:
                        del st.session_state[f"last_score_{word_id}"]
                    if view_idx < len(all_words) - 1:
                        st.session_state[idx_key] = view_idx + 1
                        st.rerun()
                    else:
                        st.session_state[celebration_key] = True
                        st.rerun()

        # Action Buttons Row: ⬅️ Previous Word | ⏭️ Skip Word / Next Word | 🎧 Having Trouble?
        act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
        with act_col1:
            # ⬅️ Previous Word
            is_first_word = (view_idx == 0)
            if st.button("⬅️ Previous Word", use_container_width=True, disabled=is_first_word, key=f"btn_prev_w_{view_idx}"):
                if f"last_score_{word_id}" in st.session_state:
                    del st.session_state[f"last_score_{word_id}"]
                st.session_state[idx_key] = max(0, view_idx - 1)
                st.rerun()

        with act_col2:
            # If word is completed, show "Next Word ➡️", otherwise show "⏭️ Skip Word"
            if is_word_already_done and view_idx < len(all_words) - 1:
                if st.button("Next Word ➡️", use_container_width=True, key=f"btn_next_w_nav_{view_idx}"):
                    if f"last_score_{word_id}" in st.session_state:
                        del st.session_state[f"last_score_{word_id}"]
                    st.session_state[idx_key] = view_idx + 1
                    st.rerun()
            else:
                if st.button("⏭️ Skip Word", use_container_width=True, key=f"btn_skip_{word_id}"):
                    progression_svc.skip_word(student_id, current_level_id, word_id)
                    if f"last_score_{word_id}" in st.session_state:
                        del st.session_state[f"last_score_{word_id}"]
                    st.rerun()

        with act_col3:
            # Having Trouble Help Menu (Available on EVERY gameplay level)
            with st.popover("🎧 Having Trouble?"):
                st.markdown("#### 🎧 Having Trouble with Audio?")
                st.caption("Use an alternate microphone or request instructor assistance.")

                st.markdown("##### 1. 🎧 Use Backup Mic")
                fallback_bytes = render_fallback_audio_recorder(key=f"play_fb_rec_{word_id}")
                if fallback_bytes:
                    with st.spinner("🟡 Processing audio with backup service..."):
                        fb_res = speech_svc.transcribe_audio_bytes(fallback_bytes)
                        if fb_res.is_usable():
                            score_res = scoring_svc.score_pronunciation(
                                target=active_word["text"],
                                transcript=fb_res.text,
                                fallback_mistake=active_word.get("common_mistake")
                            )
                            attempts_repo.record_attempt(
                                student_id=student_id,
                                word_id=word_id,
                                level_id=current_level_id,
                                transcribed_text=fb_res.text,
                                score=score_res.score,
                                passed=score_res.passed
                            )
                            st.session_state[f"last_score_{word_id}"] = (score_res, fb_res.text)
                            if score_res.passed:
                                if not is_word_already_done:
                                    game_progress_svc.record_word_success(
                                        student_id=student_id,
                                        word_id=word_id,
                                        level_id=current_level_id,
                                        pronunciation_score=score_res.score
                                    )
                            else:
                                if not is_word_already_done:
                                    game_progress_svc.update_streak(student_id, passed=False)
                            st.rerun()
                        else:
                            st.warning(f"⚠️ {fb_res.error or 'Could not capture speech.'}")

                st.divider()
                st.markdown("##### 2. 🛠️ Resolve This Word")
                st.caption("A teacher can authorize word completion if persistent mic hardware issues prevent recording.")
                with st.form(f"resolve_form_{word_id}"):
                    teacher_pw = st.text_input("Teacher Password", type="password", placeholder="Enter teacher credential")
                    reason_txt = st.text_input("Reason", value="Hardware misrecognition / microphone issue")
                    submit_override = st.form_submit_button("Confirm & Resolve Word", type="primary")

                if submit_override:
                    if not teacher_pw:
                        st.error("Please enter the teacher password.")
                    else:
                        is_auth = override_svc.authorize_teacher(teacher_pw)
                        if is_auth:
                            override_svc.resolve_word_with_override(
                                student_id=student_id,
                                level_id=current_level_id,
                                word_id=word_id,
                                authorizing_user_id=student_id,
                                reason=reason_txt
                            )
                            st.success(f"Word '{active_word['text']}' marked as Resolved.")
                            st.rerun()
                        else:
                            st.error("❌ Invalid teacher password. Override authorization rejected.")

    # 10. Level Navigation (Previous Level & Return to Journey Map)
    st.divider()
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1.5, 1])

    world_levels = content_repo.get_levels_for_world(current_world_id)
    prev_level = next((l for l in world_levels if l.get("order_index") == lvl_num - 1), None)
    next_level = next((l for l in world_levels if l.get("order_index") == lvl_num + 1), None)

    with nav_col1:
        if prev_level and progression_svc.can_access_level(student_id, prev_level["id"]):
            if st.button(f"⬅️ Previous Level ({prev_level['order_index']})", use_container_width=True, key="btn_prev_level"):
                st.session_state.pop(f"celebrate_level_{prev_level['id']}", None)
                st.session_state[f"view_word_idx_{prev_level['id']}"] = 0
                st.query_params["level_id"] = prev_level["id"]
                st.rerun()

    with nav_col2:
        if st.button("🗺️ Return to Journey Map", use_container_width=True, key="btn_return_journey"):
            st.switch_page("pages/2_Journey_Map.py")

    with nav_col3:
        # Next Level appears ONLY when viewing an already completed level AND next level is unlocked
        lvl_prog = progress_repo.get_student_level_progress(student_id, current_level_id)
        is_curr_completed = (lvl_prog and lvl_prog.get("status") == "completed")
        if next_level and is_curr_completed and progression_svc.can_access_level(student_id, next_level["id"]):
            if st.button(f"Next Level ({next_level['order_index']}) ➡️", use_container_width=True, key="btn_next_level"):
                st.session_state.pop(f"celebrate_level_{next_level['id']}", None)
                st.session_state[f"view_word_idx_{next_level['id']}"] = 0
                st.query_params["level_id"] = next_level["id"]
                st.rerun()


if __name__ == "__main__":
    main()
