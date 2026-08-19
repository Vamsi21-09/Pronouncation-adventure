"""Unit tests for authentication service and profile repository."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import pytest

from services.auth_service import AuthService, AuthResult
from repositories.profiles_repo import ProfilesRepository, ProfileRepositoryError


class TestAuthServiceValidation(unittest.TestCase):
    """Test pure input validation in AuthService."""

    def setUp(self):
        self.auth_service = AuthService(supabase_client=MagicMock(), profiles_repo=MagicMock())

    def test_valid_inputs(self):
        err = self.auth_service.validate_signup_inputs("student@school.org", "strongpass123", "cool_student_1")
        self.assertIsNone(err)

    def test_invalid_email(self):
        err = self.auth_service.validate_signup_inputs("not-an-email", "strongpass123", "student1")
        self.assertIsNotNone(err)
        self.assertIn("valid email", err)

    def test_short_password(self):
        err = self.auth_service.validate_signup_inputs("student@school.org", "12345", "student1")
        self.assertIsNotNone(err)
        self.assertIn("at least 6 characters", err)

    def test_invalid_username_format(self):
        # Too short (< 3 chars)
        err = self.auth_service.validate_signup_inputs("student@school.org", "password123", "ab")
        self.assertIsNotNone(err)

        # Invalid characters (spaces, special symbols)
        err_spaces = self.auth_service.validate_signup_inputs("student@school.org", "password123", "bad name!")
        self.assertIsNotNone(err_spaces)


class TestAuthServiceOperations(unittest.TestCase):
    """Test signup, login, logout with mocked Supabase client."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_profiles_repo = MagicMock()
        self.auth_service = AuthService(
            supabase_client=self.mock_client,
            profiles_repo=self.mock_profiles_repo
        )

    def test_signup_success(self):
        # Setup mock user return
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000001"
        mock_user.email = "learner@test.com"

        mock_session = MagicMock()
        mock_session.access_token = "fake_jwt_token"
        mock_session.refresh_token = "fake_refresh_token"

        mock_auth_resp = MagicMock()
        mock_auth_resp.user = mock_user
        mock_auth_resp.session = mock_session

        self.mock_client.auth.sign_up.return_value = mock_auth_resp
        self.mock_profiles_repo.get_profile_by_username.return_value = None
        self.mock_profiles_repo.create_profile.return_value = {
            "id": str(mock_user.id),
            "username": "learner1",
            "display_name": "learner1",
            "role": "student"
        }

        result = self.auth_service.sign_up("learner@test.com", "validpassword", "learner1")

        self.assertTrue(result.success)
        self.assertEqual(result.user["id"], str(mock_user.id))
        self.assertEqual(result.profile["username"], "learner1")
        self.mock_profiles_repo.create_profile.assert_called_once()

    def test_signup_duplicate_username(self):
        self.mock_profiles_repo.get_profile_by_username.return_value = {
            "id": "existing-uuid",
            "username": "taken_username"
        }

        result = self.auth_service.sign_up("new@test.com", "validpassword", "taken_username")
        self.assertFalse(result.success)
        self.assertIn("already taken", result.error_message)
        self.mock_client.auth.sign_up.assert_not_called()

    def test_signup_duplicate_email(self):
        self.mock_profiles_repo.get_profile_by_username.return_value = None
        self.mock_client.auth.sign_up.side_effect = Exception("User already registered")

        result = self.auth_service.sign_up("existing@test.com", "validpassword", "newuser")
        self.assertFalse(result.success)
        self.assertIn("already exists", result.error_message)

    def test_login_success(self):
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000002"
        mock_user.email = "student@test.com"

        mock_session = MagicMock()
        mock_session.access_token = "token123"
        mock_session.refresh_token = "refreshtoken123"

        mock_resp = MagicMock()
        mock_resp.user = mock_user
        mock_resp.session = mock_session

        self.mock_client.auth.sign_in_with_password.return_value = mock_resp
        self.mock_profiles_repo.get_profile.return_value = {
            "id": str(mock_user.id),
            "username": "student_pro",
            "display_name": "Star Student",
            "role": "student"
        }

        result = self.auth_service.log_in("student@test.com", "password123")

        self.assertTrue(result.success)
        self.assertEqual(result.user["id"], str(mock_user.id))
        self.assertEqual(result.profile["display_name"], "Star Student")

    def test_login_invalid_credentials(self):
        self.mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

        result = self.auth_service.log_in("student@test.com", "wrongpassword")
        self.assertFalse(result.success)
        self.assertIn("Incorrect email or password", result.error_message)

    def test_login_unconfirmed_email(self):
        self.mock_client.auth.sign_in_with_password.side_effect = Exception("Email not confirmed")

        result = self.auth_service.log_in("student@test.com", "password")
        self.assertFalse(result.success)
        self.assertIn("confirm your email", result.error_message)

    def test_login_network_error(self):
        self.mock_client.auth.sign_in_with_password.side_effect = Exception("Failed to connect to host")

        result = self.auth_service.log_in("student@test.com", "password")
        self.assertFalse(result.success)
        self.assertIn("internet connection", result.error_message)

    def test_get_current_session_active(self):
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000003"
        mock_user.email = "active@test.com"

        mock_session = MagicMock()
        mock_session.user = mock_user
        mock_session.access_token = "valid_access_token"

        self.mock_client.auth.get_session.return_value = mock_session
        self.mock_profiles_repo.get_profile.return_value = {
            "id": str(mock_user.id),
            "username": "active_user",
            "display_name": "Active User",
            "role": "student"
        }

        result = self.auth_service.get_current_session()
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.user["email"], "active@test.com")
        self.assertEqual(result.profile["username"], "active_user")

    def test_get_current_session_none(self):
        self.mock_client.auth.get_session.return_value = None
        result = self.auth_service.get_current_session()
        self.assertIsNone(result)


class TestProfilesRepository(unittest.TestCase):
    """Test database queries in ProfilesRepository using mocked Supabase table calls."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.repo = ProfilesRepository(client=self.mock_client)

    def test_get_profile_found(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{
            "id": "uuid-1",
            "username": "tester",
            "display_name": "Tester",
            "role": "student"
        }])
        self.mock_client.table.return_value = mock_query

        profile = self.repo.get_profile("uuid-1")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["username"], "tester")

    def test_get_profile_not_found(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[])
        self.mock_client.table.return_value = mock_query

        profile = self.repo.get_profile("non-existent-uuid")
        self.assertIsNone(profile)

    def test_get_profile_by_username(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{
            "id": "uuid-1",
            "username": "tester_hero",
            "display_name": "Tester Hero",
            "role": "student"
        }])
        self.mock_client.table.return_value = mock_query

        profile = self.repo.get_profile_by_username("TESTER_HERO")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["username"], "tester_hero")

    def test_create_profile_success(self):
        mock_query = MagicMock()
        mock_query.insert.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{
            "id": "uuid-10",
            "username": "new_hero",
            "display_name": "New Hero",
            "role": "student"
        }])
        self.mock_client.table.return_value = mock_query

        created = self.repo.create_profile(
            user_id="uuid-10",
            username="new_hero",
            display_name="New Hero",
            role="student"
        )
        self.assertEqual(created["username"], "new_hero")

    def test_update_display_name_empty_raises(self):
        with self.assertRaises(ProfileRepositoryError):
            self.repo.update_display_name("uuid-1", "   ")

    def test_update_display_name_success(self):
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{
            "id": "uuid-1",
            "display_name": "Updated Champion"
        }])
        self.mock_client.table.return_value = mock_query

        res = self.repo.update_display_name("uuid-1", "Updated Champion")
        self.assertEqual(res["display_name"], "Updated Champion")


class TestSettingsConfiguration(unittest.TestCase):
    """Test configuration module error handling."""

    def test_missing_settings_raises_configuration_error(self):
        from config.settings import get_settings, reset_settings_cache, ConfigurationError
        reset_settings_cache()
        with patch.dict("os.environ", {}, clear=True), patch("streamlit.secrets", {}):
            with self.assertRaises(ConfigurationError):
                get_settings()


if __name__ == "__main__":
    unittest.main()

