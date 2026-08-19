"""Pronunciation Adventure - Login Page."""
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

st.set_page_config(page_title="Login - Pronunciation Adventure", page_icon="🔑", layout="centered", initial_sidebar_state="collapsed")

# Inject Shared Design System CSS
st.html(get_global_css())

# Custom CSS for Login in Authentic Teal & Sidecar Yellow
st.html(f"""
<style>
    .login-header {{
        text-align: center;
        margin-bottom: 2rem;
    }}
    .login-title {{
        font-family: 'General Sans', sans-serif;
        font-size: 2.3rem;
        font-weight: 800;
        color: #102A2A;
        margin-bottom: 0.35rem;
    }}
    .login-subtitle {{
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
            st.warning("⚙️ Supabase credentials must be configured before logging in.")
            return
    except ConfigurationError as e:
        st.error(f"Configuration error: {e}")
        return

    auth_service = get_auth_service()

    # 2. Check if already authenticated
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        st.info("👋 You are already logged in.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Home Dashboard", use_container_width=True, type="primary"):
                st.switch_page("app.py")
        with col2:
            if st.button("Log Out", use_container_width=True):
                auth_service.log_out()
                st.rerun()
        return

    header_html = (
        '<div class="login-header">\n'
        '<h1 class="login-title">Welcome Back! 🎙️</h1>\n'
        '<p class="login-subtitle">Enter your details below to resume your pronunciation quest.</p>\n'
        '</div>'
    )
    st.html(header_html)

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("📧 Email Address", placeholder="student@example.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.warning("Please fill in both email and password.")
        else:
            with st.spinner("Logging you in..."):
                result = auth_service.log_in(email=email, password=password)

            if result.success:
                st.session_state["authenticated"] = True
                st.session_state["user"] = result.user
                st.session_state["profile"] = result.profile
                st.session_state["session"] = result.session
                st.session_state["game_mode"] = False
                st.success("🎉 Welcome back! Redirecting to Home...")
                st.switch_page("app.py")
            else:
                st.error(result.error_message or "Login failed. Please check your credentials.")

    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Don't have an account yet?")
    with col2:
        if st.button("Sign Up Here", use_container_width=True):
            st.switch_page("pages/7_Signup.py")


if __name__ == "__main__":
    main()
