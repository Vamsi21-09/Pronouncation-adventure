"""Pronunciation Adventure - Level Progression & Override Test Harness (Phase 3 Dev Screen)."""
from __future__ import annotations

import html
import streamlit as st
from config.settings import get_settings, ConfigurationError
from repositories.content_repo import get_content_repository
from repositories.progress_repo import get_progress_repository
from services.auth_service import get_auth_service
from services.progression_service import get_progression_service
from services.override_service import get_override_service

st.set_page_config(
    page_title="Level Progression Dev - Pronunciation Adventure",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Injected directly via st.html)
st.html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Inter', sans-serif;
    }

    .word-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    .active-word-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        background: linear-gradient(135deg, #A5B4FC 0%, #E0E7FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .hint-chip {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.2);
        color: #A5B4FC;
        border: 1px solid rgba(165, 180, 252, 0.3);
    }

    .dev-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        background: #F59E0B;
        color: #0F172A;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""")


def check_auth() -> tuple[dict, str]:
    """Ensure user is logged in."""
    auth_service = get_auth_service()
    session_info = auth_service.get_current_session()

    user = None
    if session_info and session_info.success and session_info.user:
        user = session_info.user
    elif st.session_state.get("authenticated") and st.session_state.get("user"):
        user = st.session_state["user"]

    if not user:
        st.warning("🔒 Please log in to access the level progression test harness.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/1_Login.py")
        st.stop()

    return user, user["id"]


def main() -> None:
    user, student_id = check_auth()
    override_svc = get_override_service()

    # Developer/Teacher Access Guard
    if not st.session_state.get("dev_authorized"):
        st.warning("🔒 **Developer Access Restricted**: This page is an administrative harness for instructors and developers.")
        with st.form("dev_auth_form"):
            dev_pw = st.text_input("Instructor / Developer Password", type="password", placeholder="Enter authorization key")
            dev_submit = st.form_submit_button("Authenticate Developer Access", type="primary")

        if dev_submit:
            if override_svc.authorize_teacher(dev_pw):
                st.session_state["dev_authorized"] = True
                st.success("Access authorized.")
                st.rerun()
            else:
                st.error("❌ Invalid authorization key.")

        if st.button("⬅️ Return to Student Home", use_container_width=True):
            st.switch_page("app.py")
        return

    content_repo = get_content_repository()
    progress_repo = get_progress_repository()
    progression_svc = get_progression_service()

    st.info("ℹ️ **Teacher / Developer Debugger**: This screen is an administrative test harness for Phase 3 queue state and overrides. For student gameplay, please use the [🗺️ Journey Map](pages/2_Journey_Map.py).")

    header_html = (
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:0.75rem;">\n'
        '<div>\n'
        '<h1 style="margin:0;">🛠️ Progression Dev & Override Debugger</h1>\n'
        '<p style="color:#94A3B8; margin-top:0.25rem;">Administrative debugging tool: queue reordering, skip logic, level cascades, and authorized overrides.</p>\n'
        '</div>\n'
        '<span class="dev-badge">🛠️ Admin / Dev Tool</span>\n'
        '</div>'
    )
    st.html(header_html)

    # 1. World Selection
    worlds = content_repo.get_all_worlds()
    if not worlds:
        st.error("No worlds found in database. Please run `python scripts/seed_content.py`.")
        return

    world_names = [f"World {w['order_index']}: {w['name']} {w.get('icon_emoji', '')}" for w in worlds]
    selected_world_idx = st.selectbox("🌍 Select World", range(len(worlds)), format_func=lambda i: world_names[i])
    current_world = worlds[selected_world_idx]
    current_world_id = current_world["id"]

    # World lock status
    world_prog = progress_repo.get_student_world_progress(student_id, current_world_id)
    world_status = world_prog.get("status", "locked") if world_prog else ("unlocked" if current_world["order_index"] == 1 else "locked")
    
    col_w1, col_w2 = st.columns([1, 1])
    with col_w1:
        st.metric("World Status", world_status.upper())
    with col_w2:
        st.metric("Theme Key", current_world["theme_key"])

    st.divider()

    # 2. Level Selection
    levels = content_repo.get_levels_for_world(current_world_id)
    if not levels:
        st.warning(f"No levels found for {current_world['name']}.")
        return

    level_labels = []
    for l in levels:
        l_prog = progress_repo.get_student_level_progress(student_id, l["id"])
        l_stat = l_prog.get("status", "locked") if l_prog else ("unlocked" if (current_world["order_index"] == 1 and l["order_index"] == 1) else "locked")
        level_labels.append(f"Level {l['order_index']} ({l['difficulty_band'].capitalize()}) — [{l_stat.upper()}]")

    selected_level_idx = st.selectbox("🎯 Select Level", range(len(levels)), format_func=lambda i: level_labels[i])
    current_level = levels[selected_level_idx]
    current_level_id = current_level["id"]

    # Check access permission
    has_access = progression_svc.can_access_level(student_id, current_level_id)
    
    if not has_access:
        st.error(f"🔒 **Level {current_level['order_index']} is Locked**")
        st.info("You must complete the preceding level or world before accessing this level.")
        return

    # 3. Load In-Level Word Queue
    queue_state = progression_svc.get_or_init_level_queue(student_id, current_level_id)
    active_queue = queue_state["active_queue"]
    completed_words = queue_state["completed_words"]
    resolved_words = queue_state["resolved_words"]
    all_words = queue_state["all_words"]
    is_level_completed = queue_state["is_level_completed"]

    # Metrics row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Remaining in Queue", len(active_queue))
    with col_m2:
        st.metric("Correctly Completed", len(completed_words))
    with col_m3:
        st.metric("Resolved by Override", len(resolved_words))
    with col_m4:
        st.metric("Level Progress", f"{len(completed_words) + len(resolved_words)} / {len(all_words)}")

    # 4. Level Completed Banner
    if is_level_completed:
        st.success(f"🎉 **Level {current_level['order_index']} Complete!** All 7 words have been completed or resolved.")
        st.balloons()
        return

    # 5. Current Active Word Card
    if active_queue:
        active_word = active_queue[0]
        word_id = active_word["id"]

        safe_text = html.escape(active_word['text'].upper())
        safe_hint = html.escape(active_word.get('pronunciation_hint', ''))
        safe_syllables = html.escape(active_word.get('syllable_breakdown', 'N/A'))
        safe_meaning = html.escape(active_word.get('meaning', ''))
        safe_sentence = html.escape(active_word.get('example_sentence', ''))
        safe_mistake = html.escape(active_word.get('common_mistake', 'None noted'))
        safe_status = html.escape(active_word.get('progress_status', 'pending').upper())
        attempts = active_word.get('attempt_count', 0)
        q_pos = len(active_queue)

        word_card_html = (
            f'<div class="word-card">\n'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">\n'
            f'<span class="hint-chip">Queue Position: 1 of {q_pos}</span>\n'
            f'<span style="color:#94A3B8; font-size:0.9rem;">Attempts: {attempts} | Status: {safe_status}</span>\n'
            f'</div>\n'
            f'<h2 class="active-word-title">{safe_text}</h2>\n'
            f'<p style="color:#A5B4FC; font-size:1.1rem; margin-top:0.5rem; font-weight:600;">\n'
            f'Pronunciation: <span class="hint-chip">{safe_hint}</span> &nbsp;|&nbsp; Syllables: <span class="hint-chip">{safe_syllables}</span>\n'
            f'</p>\n'
            f'<p style="color:#F1F5F9; font-size:1.05rem; line-height:1.6; margin-top:1rem;">\n'
            f'<strong>Meaning:</strong> {safe_meaning}\n'
            f'</p>\n'
            f'<p style="color:#94A3B8; font-style:italic;">\n'
            f'"{safe_sentence}"\n'
            f'</p>\n'
            f'<div style="background:rgba(239, 68, 68, 0.1); border-left:3px solid #EF4444; padding:0.5rem 1rem; border-radius:4px; margin-top:1rem;">\n'
            f'<span style="color:#FCA5A5; font-size:0.9rem;">⚠️ Common Mistake: {safe_mistake}</span>\n'
            f'</div>\n'
            f'</div>'
        )
        st.html(word_card_html)

        # 6. Interactive Action Buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("✅ Complete Word (Test)", use_container_width=True, type="primary"):
                progression_svc.complete_word(student_id, current_level_id, word_id)
                st.success(f"Marked '{active_word['text']}' as completed!")
                st.rerun()

        with col_btn2:
            if st.button("⏭️ Skip Word (Move to Back)", use_container_width=True):
                progression_svc.skip_word(student_id, current_level_id, word_id)
                st.info(f"Skipped '{active_word['text']}'. Moved to back of level queue.")
                st.rerun()

        with col_btn3:
            # Authorized Override Expander / Form
            with st.expander("🛡️ Resolve Word (Authorized Override)"):
                st.caption("Removes word from queue for students experiencing persistent mic/hardware issues. Requires teacher password.")
                with st.form(f"override_form_{word_id}"):
                    reason = st.text_input("Override Reason", value="Hardware misrecognition / microphone issue")
                    teacher_pw = st.text_input("Teacher Password", type="password", placeholder="Enter teacher/admin password")
                    submitted_override = st.form_submit_button("Confirm & Resolve Word", type="primary")

                if submitted_override:
                    if not teacher_pw:
                        st.error("Please enter the teacher authorization password.")
                    else:
                        is_auth = override_svc.authorize_teacher(teacher_pw)
                        if is_auth:
                            override_svc.resolve_word_with_override(
                                student_id=student_id,
                                level_id=current_level_id,
                                word_id=word_id,
                                authorizing_user_id=student_id,
                                reason=reason
                            )
                            st.success(f"Word '{active_word['text']}' marked as Resolved by Override.")
                            st.rerun()
                        else:
                            st.error("❌ Invalid teacher password. Override authorization rejected.")

    # 7. Queue Overview Table
    st.subheader("📋 Level Word Queue Details")
    table_data = []
    for idx, w in enumerate(all_words, start=1):
        table_data.append({
            "Word": w["text"].upper(),
            "Status": w.get("progress_status", "pending").upper(),
            "Attempts": w.get("attempt_count", 0),
            "Queue Order": w.get("queue_order", 0),
            "Difficulty": w.get("difficulty_band", "easy").capitalize(),
        })
    st.dataframe(table_data, use_container_width=True)

    # 8. Audit Log Section
    st.subheader("📜 Authorized Override Audit Trail")
    audit_logs = progress_repo.get_override_audit_logs(student_id=student_id, level_id=current_level_id)
    if audit_logs:
        st.dataframe(audit_logs, use_container_width=True)
    else:
        st.caption("No override audit records logged for this level.")


if __name__ == "__main__":
    main()
