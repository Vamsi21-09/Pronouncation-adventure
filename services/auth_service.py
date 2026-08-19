"""Authentication service encapsulating Supabase Auth & profile orchestration."""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel

from config.settings import get_settings
from repositories.supabase_client import get_supabase_client, set_client_auth_token
from repositories.profiles_repo import ProfilesRepository, ProfileRepositoryError

logger = logging.getLogger(__name__)


class AuthResult(BaseModel):
    """Result model for authentication operations."""
    success: bool
    user: Optional[Dict[str, Any]] = None
    session: Optional[Dict[str, Any]] = None
    profile: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    info_message: Optional[str] = None


class AuthService:
    """Business logic for user signup, login, session validation, and logout."""

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        profiles_repo: Optional[ProfilesRepository] = None
    ):
        self._client = supabase_client
        self._profiles_repo = profiles_repo

    @property
    def client(self) -> Any:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    @property
    def profiles_repo(self) -> ProfilesRepository:
        if self._profiles_repo is not None:
            return self._profiles_repo
        return ProfilesRepository(client=self.client)

    def validate_signup_inputs(self, email: str, password: str, username: str) -> Optional[str]:
        """Validate input formats before attempting network calls."""
        email_clean = email.strip()
        username_clean = username.strip()

        # Email regex validation
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_pattern, email_clean):
            return "Please enter a valid email address."

        # Username validation: 3-20 chars, alphanumeric + underscores
        username_pattern = r"^[a-zA-Z0-9_-]{3,20}$"
        if not re.match(username_pattern, username_clean):
            return "Username must be 3–20 characters and contain only letters, numbers, underscores, or hyphens."

        # Password strength: minimum 6 characters
        if len(password) < 6:
            return "Password must be at least 6 characters long."

        return None

    def sign_up(self, email: str, password: str, username: str) -> AuthResult:
        """
        Register a new student user and create their database profile.
        
        Args:
            email: User's email.
            password: User's chosen password.
            username: Unique student handle.
            
        Returns:
            AuthResult with user/profile data on success, or friendly error message on failure.
        """
        email_clean = email.strip().lower()
        username_clean = username.strip().lower()

        # 1. Client-side input validation
        validation_err = self.validate_signup_inputs(email_clean, password, username_clean)
        if validation_err:
            return AuthResult(success=False, error_message=validation_err)

        # 2. Check if username is already taken
        try:
            existing_profile = self.profiles_repo.get_profile_by_username(username_clean)
            if existing_profile:
                return AuthResult(
                    success=False,
                    error_message=f"The username '{username_clean}' is already taken. Please pick a different one."
                )
        except Exception as e:
            logger.warning("Username check encountered an error (proceeding to auth): %s", e)

        # 3. Create Supabase Auth user
        try:
            auth_response = self.client.auth.sign_up({
                "email": email_clean,
                "password": password,
                "options": {
                    "data": {
                        "username": username_clean,
                    }
                }
            })
        except Exception as e:
            err_msg = str(e)
            logger.error("Supabase Auth sign_up error: %s", err_msg)
            return self._map_auth_error(err_msg, default="Signup failed. Please try again.")

        if not auth_response or not getattr(auth_response, "user", None):
            return AuthResult(
                success=False,
                error_message="Account creation failed. Please check your credentials and try again."
            )

        user_obj = auth_response.user
        user_id = str(user_obj.id)
        user_dict = {
            "id": user_id,
            "email": getattr(user_obj, "email", email_clean),
        }

        # Format session if present and authenticate PostgREST client immediately
        session_dict = None
        if getattr(auth_response, "session", None):
            sess = auth_response.session
            access_token = getattr(sess, "access_token", None)
            refresh_token = getattr(sess, "refresh_token", None)
            session_dict = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
            if access_token:
                set_client_auth_token(self.client, access_token)

        # If sign_up did not return a session, auto-authenticate to establish active JWT for RLS
        if not session_dict:
            try:
                sign_in_res = self.client.auth.sign_in_with_password({
                    "email": email_clean,
                    "password": password
                })
                if sign_in_res and getattr(sign_in_res, "session", None):
                    sess = sign_in_res.session
                    access_token = getattr(sess, "access_token", None)
                    refresh_token = getattr(sess, "refresh_token", None)
                    session_dict = {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                    if access_token:
                        set_client_auth_token(self.client, access_token)
            except Exception as e:
                logger.debug("Immediate post-signup sign-in notice: %s", e)

        try:
            import streamlit as st
            if session_dict and session_dict.get("access_token") and hasattr(st, "session_state"):
                st.session_state["auth_token"] = session_dict["access_token"]
        except Exception:
            pass

        # 4. Create row in public.profiles table
        profile_dict = None
        try:
            profile_dict = self.profiles_repo.create_profile(
                user_id=user_id,
                username=username_clean,
                display_name=username_clean,
                role="student"
            )
        except Exception as e:
            logger.error("Profile row creation failed for %s: %s", user_id, e)
            try:
                profile_dict = self.profiles_repo.get_profile(user_id)
            except Exception:
                pass

        # 5. Initialize starting progression (World 1 + Level 1 unlocked)
        try:
            from services.progression_service import ProgressionService
            prog_svc = ProgressionService()
            prog_svc.init_student_initial_progress(user_id)
        except Exception as e:
            logger.warning("Could not seed initial progression for %s: %s", user_id, e)

        # Check if email confirmation is required by Supabase project
        info_msg = None
        if not session_dict:
            info_msg = "Account created! If email confirmation is enabled in your project, please check your inbox to activate your account."

        return AuthResult(
            success=True,
            user=user_dict,
            session=session_dict,
            profile=profile_dict or {
                "id": user_id,
                "username": username_clean,
                "display_name": username_clean,
                "role": "student"
            },
            info_message=info_msg
        )

    def log_in(self, email: str, password: str) -> AuthResult:
        """
        Log in an existing user with email and password.
        
        Args:
            email: User email.
            password: User password.
            
        Returns:
            AuthResult containing user, session, and profile on success.
        """
        email_clean = email.strip().lower()
        if not email_clean or not password:
            return AuthResult(success=False, error_message="Please enter both email and password.")

        try:
            auth_response = self.client.auth.sign_in_with_password({
                "email": email_clean,
                "password": password
            })
        except Exception as e:
            err_msg = str(e)
            logger.error("Supabase Auth log_in error: %s", err_msg)
            return self._map_auth_error(err_msg, default="Login failed. Please check your credentials.")

        if not auth_response or not getattr(auth_response, "user", None):
            return AuthResult(
                success=False,
                error_message="Invalid email or password. Please try again."
            )

        user_obj = auth_response.user
        user_id = str(user_obj.id)
        user_dict = {
            "id": user_id,
            "email": getattr(user_obj, "email", email_clean),
        }

        session_dict = None
        if getattr(auth_response, "session", None):
            sess = auth_response.session
            access_token = getattr(sess, "access_token", None)
            refresh_token = getattr(sess, "refresh_token", None)
            session_dict = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
            if access_token:
                set_client_auth_token(self.client, access_token)
                try:
                    import streamlit as st
                    if hasattr(st, "session_state"):
                        st.session_state["auth_token"] = access_token
                except Exception:
                    pass

        # Retrieve profile
        profile_dict = None
        try:
            profile_dict = self.profiles_repo.get_profile(user_id)
        except Exception as e:
            logger.warning("Could not fetch profile for logged-in user %s: %s", user_id, e)

        # Self-repair: If user exists in Auth but profiles row was missing due to past RLS signup failure, insert it now with authenticated session
        if not profile_dict:
            fallback_username = email_clean.split("@")[0]
            try:
                profile_dict = self.profiles_repo.create_profile(
                    user_id=user_id,
                    username=fallback_username,
                    display_name=fallback_username,
                    role="student"
                )
            except Exception as e:
                logger.warning("Could not auto-create missing profile row: %s", e)
                profile_dict = {
                    "id": user_id,
                    "username": fallback_username,
                    "display_name": fallback_username,
                    "role": "student"
                }

        return AuthResult(
            success=True,
            user=user_dict,
            session=session_dict,
            profile=profile_dict
        )

    def log_out(self) -> None:
        """Sign out the current user from Supabase and clear session state."""
        try:
            self.client.auth.sign_out()
        except Exception as e:
            logger.warning("Supabase sign_out notice: %s", e)

        # Reset PostgREST auth header back to anon key
        set_client_auth_token(self.client, None)

        # Wipe Streamlit session state keys if running inside Streamlit
        try:
            import streamlit as st
            keys_to_clear = ["authenticated", "user", "session", "profile", "auth_token"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["profile"] = None
            st.session_state["session"] = None
        except Exception:
            pass

    def get_current_session(self) -> Optional[AuthResult]:
        """
        Verify and fetch current active session from Supabase.
        Ensures local session_state is in sync with Supabase Auth state.
        """
        try:
            sess_response = self.client.auth.get_session()
            if sess_response and getattr(sess_response, "user", None):
                user_obj = sess_response.user
                user_id = str(user_obj.id)
                user_dict = {"id": user_id, "email": getattr(user_obj, "email", "")}
                
                access_token = getattr(sess_response, "access_token", None)
                if access_token:
                    set_client_auth_token(self.client, access_token)

                profile = None
                try:
                    profile = self.profiles_repo.get_profile(user_id)
                except Exception:
                    pass

                return AuthResult(
                    success=True,
                    user=user_dict,
                    profile=profile,
                    session={
                        "access_token": access_token
                    }
                )
        except Exception as e:
            logger.debug("No active Supabase session found: %s", e)

        return None

    def _map_auth_error(self, raw_error: str, default: str) -> AuthResult:
        """Map raw Supabase error messages to friendly, student-facing messages."""
        msg_lower = raw_error.lower()

        if "user already registered" in msg_lower or "already exists" in msg_lower:
            return AuthResult(
                success=False,
                error_message="An account with this email already exists. Please log in or use a different email."
            )
        if "invalid login credentials" in msg_lower or "invalid_credentials" in msg_lower:
            return AuthResult(
                success=False,
                error_message="Incorrect email or password. Please try again."
            )
        if "email not confirmed" in msg_lower:
            return AuthResult(
                success=False,
                error_message="Please confirm your email address before logging in."
            )
        if "password should be at least" in msg_lower or "weak_password" in msg_lower:
            return AuthResult(
                success=False,
                error_message="Password is too weak. Please use at least 6 characters."
            )
        if "rate limit" in msg_lower:
            return AuthResult(
                success=False,
                error_message="Too many attempts in a short time. Please wait a few moments and try again."
            )
        if "network" in msg_lower or "failed to connect" in msg_lower or "connection" in msg_lower:
            return AuthResult(
                success=False,
                error_message="Unable to reach the server. Please check your internet connection."
            )

        return AuthResult(success=False, error_message=default)


def get_auth_service() -> AuthService:
    """Helper factory to retrieve the AuthService instance."""
    return AuthService()
