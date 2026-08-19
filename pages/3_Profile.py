import logging
import html
import streamlit as st
from config.settings import get_settings, ConfigurationError
from repositories.profiles_repo import ProfilesRepository, ProfileRepositoryError
from services.auth_service import get_auth_service
from services.profile_service import get_profile_service, generate_adventurer_id
from components.sidebar import render_app_sidebar

logger = logging.getLogger(__name__)

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

st.set_page_config(page_title="My Profile - Pronunciation Adventure", page_icon="👤", layout="wide")

# Inject Shared Design System CSS
st.html(get_global_css())

# Profile Specific Styling in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    .profile-card {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.3);
        border-radius: 18px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 36px rgba(3, 83, 82, 0.3);
        color: {TEXT_LIGHT_PRIMARY};
    }}
    .stats-card {{
        background: #FFFDF5;
        border: 1.5px solid {INK_GRAY_BORDER};
        border-radius: 14px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(47, 58, 58, 0.06);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .stats-card:hover {{
        transform: translateY(-2px);
        border-color: {AUTHENTIC_TEAL};
    }}
    .stats-val {{
        font-family: 'General Sans', sans-serif;
        font-size: 1.65rem;
        font-weight: 800;
        color: {TEXT_DARK_PRIMARY};
        margin-bottom: 0.25rem;
    }}
    .stats-lbl {{
        font-family: 'General Sans', sans-serif;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {AUTHENTIC_TEAL};
        font-weight: 700;
    }}
    .companion-banner {{
        background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
        border: 1.5px solid rgba(243, 232, 188, 0.3);
        border-radius: 18px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(3, 83, 82, 0.25);
        color: {TEXT_LIGHT_PRIMARY};
    }}
    .badge-card-unlocked {{
        background: #FFFDF5;
        border: 2px solid #10B981;
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
        color: {TEXT_DARK_PRIMARY};
    }}
    .badge-card-locked {{
        background: #FAF8F0;
        border: 1.5px dashed {INK_GRAY_BORDER};
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 0.75rem;
        opacity: 0.75;
        color: {TEXT_DARK_SECONDARY};
    }}
    .role-badge {{
        display: inline-block;
        padding: 0.3rem 0.85rem;
        font-family: 'General Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        border-radius: 9999px;
        background: rgba(243, 232, 188, 0.15);
        color: {SIDECAR_YELLOW};
        border: 1px solid rgba(243, 232, 188, 0.35);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
</style>
""")


def require_authentication() -> tuple[dict, ProfilesRepository]:
    """Ensure active user session with Supabase."""
    try:
        settings = get_settings()
        if not settings.is_configured():
            st.warning("⚙️ Supabase credentials must be configured.")
            st.stop()
    except ConfigurationError as e:
        st.error(f"Configuration error: {e}")
        st.stop()

    auth_service = get_auth_service()
    profiles_repo = ProfilesRepository()

    current_session = auth_service.get_current_session()
    user = None
    if current_session and current_session.success and current_session.user:
        user = current_session.user
        st.session_state["authenticated"] = True
        st.session_state["user"] = user
    elif st.session_state.get("authenticated") and st.session_state.get("user"):
        user = st.session_state["user"]

    if not user or not user.get("id"):
        st.warning("🔒 Please log in to view and manage your profile.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/1_Login.py")
        st.stop()

    return user, profiles_repo


def main() -> None:
    user, profiles_repo = require_authentication()
    user_id = user["id"]

    # Fetch full aggregated profile data with graceful error handling
    try:
        profile_service = get_profile_service()
        data = profile_service.get_full_student_profile(user_id)
    except Exception as e:
        logger.error("Failed to load profile for user %s: %s", user_id, e)
        st.warning("Your profile could not be loaded right now. Please try again.")
        if st.button("🔄 Retry Loading Profile", type="primary"):
            st.rerun()
        return

    # App Mode Sidebar ONLY (No duplicate top navbar)
    render_app_sidebar(current_page="profile", user=user, profile=data)

    st.title("👤 Student Profile")
    st.caption("Track your adventure statistics, companion evolution, and earned badges.")

    # 1. Adventurer Identity Card (Authentic Teal Container with Light Text)
    raw_display_name = data["display_name"]
    raw_username = data["username"]
    raw_role = data["role"]
    raw_created = data["created_at_readable"]
    raw_email = str(user.get("email") or "N/A")

    safe_display_name = html.escape(raw_display_name)
    safe_username = html.escape(raw_username)
    safe_role = html.escape(raw_role.upper())
    safe_created = html.escape(raw_created)
    safe_email = html.escape(raw_email)

    raw_adv_id = data.get("adventurer_id")
    if not raw_adv_id or str(raw_adv_id).lower() in ("none", "null", ""):
        raw_adv_id = generate_adventurer_id(user_id)
    safe_adv_id = html.escape(str(raw_adv_id))

    st.html(f"""
    <div class="profile-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1.25rem; flex-wrap:wrap; gap:0.75rem;">
            <div>
                <h2 style="margin:0; font-size:1.65rem; color:{TEXT_LIGHT_PRIMARY};">{safe_display_name}</h2>
                <span style="color:{TEXT_LIGHT_SECONDARY}; font-size:0.95rem;">@{safe_username}</span>
            </div>
            <span class="role-badge">🛡️ {safe_role}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
            <div>
                <div style="font-size:0.75rem; color:{SIDECAR_YELLOW}; font-weight:700; text-transform:uppercase;">Adventurer ID</div>
                <div style="font-size:1.15rem; font-family:monospace; color:{SIDECAR_YELLOW}; font-weight:800; letter-spacing:0.06em;">{safe_adv_id}</div>
            </div>
            <div>
                <div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; font-weight:700; text-transform:uppercase;">Email</div>
                <div style="font-size:0.95rem; color:{TEXT_LIGHT_PRIMARY};">{safe_email}</div>
            </div>
            <div>
                <div style="font-size:0.75rem; color:{TEXT_LIGHT_SECONDARY}; font-weight:700; text-transform:uppercase;">Member Since</div>
                <div style="font-size:0.95rem; color:{TEXT_LIGHT_PRIMARY};">{safe_created}</div>
            </div>
        </div>
    </div>
    """)

    # 2. Adventure Statistics Showcase (Cream Cards with Dark Text & Teal Labels)
    st.subheader("📊 Adventure Statistics")
    stats = data["stats"]
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.html(f"""
        <div class="stats-card">
            <div class="stats-val" style="color:#B45309;">🏆 {stats['total_score']}</div>
            <div class="stats-lbl">Total Score</div>
        </div>
        """)
        st.html(f"""
        <div class="stats-card" style="margin-top:0.75rem;">
            <div class="stats-val" style="color:{AUTHENTIC_TEAL};">⭐ {stats['total_stars']}</div>
            <div class="stats-lbl">Stars Earned</div>
        </div>
        """)

    with s_col2:
        st.html(f"""
        <div class="stats-card">
            <div class="stats-val" style="color:#C2410C;">🔥 {stats['current_streak']}</div>
            <div class="stats-lbl">Current Streak</div>
        </div>
        """)
        st.html(f"""
        <div class="stats-card" style="margin-top:0.75rem;">
            <div class="stats-val" style="color:#7E22CE;">⚡ {stats['completed_levels']} / 210</div>
            <div class="stats-lbl">Levels Completed</div>
        </div>
        """)

    with s_col3:
        st.html(f"""
        <div class="stats-card">
            <div class="stats-val" style="color:#B91C1C;">✨ {stats['best_streak']}</div>
            <div class="stats-lbl">Best Streak</div>
        </div>
        """)
        st.html(f"""
        <div class="stats-card" style="margin-top:0.75rem;">
            <div class="stats-val" style="color:#047857;">🌍 {stats['completed_worlds']} / 7</div>
            <div class="stats-lbl">Worlds Mastered</div>
        </div>
        """)

    st.write("")

    # 3. Companion Status & Evolution Card
    st.subheader("🐾 Creature Companion")
    companion = data["companion"]
    stage_info = companion["stage_info"]
    next_stage = companion.get("next_stage")
    progress_pct = companion.get("progress_pct", 0.0)

    safe_c_name = html.escape(stage_info.name)
    safe_c_icon = html.escape(stage_info.icon)
    safe_c_desc = html.escape(stage_info.description)
    current_xp = companion["xp"]

    next_msg = f"🌟 Evolution complete! Maximum stage reached." if not next_stage else f"🌱 <b>{companion['xp_to_next']} XP</b> to evolve into <b>{html.escape(next_stage.name)} {html.escape(next_stage.icon)}</b>"

    st.html(f"""
    <div class="companion-banner">
        <div style="display:flex; align-items:center; gap:1.25rem; flex-wrap:wrap;">
            <div style="font-size:3.25rem; line-height:1;">{safe_c_icon}</div>
            <div style="flex:1;">
                <div style="font-size:1.35rem; font-weight:800; color:{TEXT_LIGHT_PRIMARY};">{safe_c_name}</div>
                <div style="font-size:0.90rem; color:{TEXT_LIGHT_SECONDARY}; margin-top:0.2rem;">{safe_c_desc}</div>
                <div style="font-size:0.85rem; color:{SIDECAR_YELLOW}; margin-top:0.4rem;">{next_msg}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.5rem; font-weight:800; color:{SIDECAR_YELLOW};">{current_xp} XP</div>
            </div>
        </div>
    </div>
    """)
    st.progress(progress_pct / 100.0, text=f"Evolution Progress: {progress_pct:.0f}%")

    st.write("")

    # 4. Badges Showcase (Cream Cards with Dark Text)
    st.subheader("🏅 Badges & Achievements")
    badges = data["badges"]
    unlocked_badges = [b for b in badges if b["is_unlocked"]]
    locked_badges = [b for b in badges if not b["is_unlocked"]]

    tab_unlocked, tab_locked = st.tabs([f"Unlocked ({len(unlocked_badges)})", f"Locked ({len(locked_badges)})"])

    with tab_unlocked:
        if not unlocked_badges:
            st.info("No badges unlocked yet! Complete your first level or achieve a 3-word streak to earn your first badge.")
        else:
            b_cols = st.columns(3)
            for idx, badge in enumerate(unlocked_badges):
                col = b_cols[idx % 3]
                with col:
                    st.html(f"""
                    <div class="badge-card-unlocked">
                        <div style="font-size:2rem; margin-bottom:0.25rem;">{html.escape(badge['icon'])}</div>
                        <div style="font-weight:700; color:{TEXT_DARK_PRIMARY}; font-size:0.95rem;">{html.escape(badge['name'])}</div>
                        <div style="font-size:0.78rem; color:{TEXT_DARK_SECONDARY}; margin-top:0.25rem;">{html.escape(badge['description'])}</div>
                        <div style="font-size:0.70rem; color:#047857; margin-top:0.4rem; font-weight:700;">✓ Unlocked {html.escape(str(badge['unlocked_at']))}</div>
                    </div>
                    """)

    with tab_locked:
        if not locked_badges:
            st.success("🎉 Incredible! You have unlocked all available badges!")
        else:
            b_cols = st.columns(3)
            for idx, badge in enumerate(locked_badges):
                col = b_cols[idx % 3]
                with col:
                    st.html(f"""
                    <div class="badge-card-locked">
                        <div style="font-size:2rem; margin-bottom:0.25rem; filter:grayscale(1);">{html.escape(badge['icon'])}</div>
                        <div style="font-weight:700; color:{TEXT_DARK_PRIMARY}; font-size:0.95rem;">{html.escape(badge['name'])}</div>
                        <div style="font-size:0.78rem; color:{TEXT_DARK_SECONDARY}; margin-top:0.25rem;">{html.escape(badge['description'])}</div>
                        <div style="font-size:0.70rem; color:#B45309; margin-top:0.4rem; font-weight:700;">Goal: {html.escape(badge['criteria'])}</div>
                    </div>
                    """)

    st.write("")

    # 5. Editable Display Name Form
    st.subheader("✏️ Edit Display Name")
    st.caption("Change how your name appears across celebration screens and leaderboards.")

    with st.form("edit_profile_form"):
        new_display_name = st.text_input(
            "Display Name / Nickname",
            value=raw_display_name,
            max_chars=50,
            help="This is the friendly name displayed on badges, milestones, and celebration screens."
        )
        saved = st.form_submit_button("Save Changes", type="primary")

    if saved:
        if not new_display_name.strip():
            st.error("Display name cannot be empty.")
        else:
            with st.spinner("Updating profile in Supabase..."):
                try:
                    profiles_repo.update_display_name(user_id, new_display_name.strip())
                    confirmed_profile = profiles_repo.get_profile(user_id)
                    if confirmed_profile:
                        st.session_state["profile"] = confirmed_profile

                    st.success(f"🎉 Display name successfully updated to **{new_display_name.strip()}**!")
                    st.rerun()
                except ProfileRepositoryError as e:
                    st.error(f"Failed to update display name: {e}")

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 Return to Home", use_container_width=True):
            st.session_state["game_mode"] = False
            st.switch_page("app.py")
    with col2:
        if st.button("🗺️ Open Journey Map", use_container_width=True):
            st.session_state["game_mode"] = True
            st.switch_page("pages/2_Journey_Map.py")
    with col3:
        if st.button("🚪 Log Out", use_container_width=True):
            auth_service = get_auth_service()
            auth_service.log_out()
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["profile"] = None
            st.success("Logged out.")
            st.switch_page("app.py")


if __name__ == "__main__":
    main()
