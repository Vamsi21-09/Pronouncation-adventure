"""Pronunciation Adventure - Student Signup Page."""
from __future__ import annotations

import streamlit as st
from config.settings import get_settings, ConfigurationError
from services.auth_service import get_auth_service

from config.design_tokens import (
    AUTHENTIC_TEAL,
    AUTHENTIC_TEAL_DARK,
    AUTHENTIC_TEAL_SURFACE,
    SIDECAR_YELLOW,
    TEXT_LIGHT_PRIMARY,
    TEXT_LIGHT_SECONDARY,
    get_global_css,
)

st.set_page_config(page_title="Sign Up - Pronunciation Adventure", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# Inject Shared Design System CSS
st.html(get_global_css())

# Custom CSS for Signup in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    .signup-header {{
        text-align: center;
        margin-bottom: 2rem;
    }}
    .signup-title {{
        font-family: 'General Sans', sans-serif;
        font-size: 2.3rem;
        font-weight: 800;
        color: #102A2A;
        margin-bottom: 0.35rem;
    }}
    .signup-subtitle {{
        font-family: 'Inter', sans-serif;
        color: #365656;
        font-size: 1.02rem;
    }}
</style>
""")


def main() -> None:
    # 1. Config Check
    try:
        settings = get_settings()
        if not settings.is_configured():
            st.warning("⚙️ Supabase credentials must be configured before signing up.")
            return
    except ConfigurationError as e:
        st.error(f"Configuration error: {e}")
        return

    auth_service = get_auth_service()

    # 2. Check if already authenticated
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        st.info("👋 You are already logged in.")
        if st.button("Go to Home Dashboard", use_container_width=True, type="primary"):
            st.switch_page("app.py")
        return

    header_html = (
        '<div class="signup-header">\n'
        '<h1 class="signup-title">Join the Adventure! 🚀</h1>\n'
        '<p class="signup-subtitle">Create your student profile and start leveling up your English pronunciation.</p>\n'
        '</div>'
    )
    st.html(header_html)

    with st.form("signup_form", clear_on_submit=False):
        username = st.text_input(
            "👤 Username",
            placeholder="e.g. word_master_99",
            help="3–20 characters. Letters, numbers, hyphens, and underscores only."
        )
        email = st.text_input(
            "📧 Email Address",
            placeholder="student@example.com",
            help="Used for logging into your account."
        )
        col_pw1, col_pw2 = st.columns(2)
        with col_pw1:
            password = st.text_input("🔒 Password", type="password", placeholder="At least 6 characters")
        with col_pw2:
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password")

        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted:
        # Pre-validation
        if not username or not email or not password or not confirm_password:
            st.warning("Please complete all required fields.")
        elif password != confirm_password:
            st.error("Passwords do not match. Please re-enter your password.")
        else:
            with st.spinner("Creating your adventurer profile..."):
                result = auth_service.sign_up(email=email, password=password, username=username)

            if result.success:
                st.session_state["authenticated"] = True
                st.session_state["user"] = result.user
                st.session_state["profile"] = result.profile
                st.session_state["session"] = result.session
                st.session_state["game_mode"] = False

                st.success("🎉 Account created successfully! Redirecting to Home...")
                st.switch_page("app.py")
            else:
                st.error(result.error_message or "Unable to create account. Please check your inputs.")

    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Already have an account?")
    with col2:
        if st.button("Log In Here", use_container_width=True):
            st.switch_page("pages/1_Login.py")


if __name__ == "__main__":
    main()
