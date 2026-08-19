"""End-to-end simulated workflow integration tests for Phase 1."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from services.auth_service import AuthService
from repositories.profiles_repo import ProfilesRepository


class TestPhase1IntegrationWorkflow(unittest.TestCase):
    """Simulates complete student lifecycle from signup to profile modification and logout."""

    def setUp(self):
        # In-memory mock storage simulating Supabase
        self.mock_auth_users = {}
        self.mock_profiles_db = {}

        self.mock_client = MagicMock()
        self.mock_repo = ProfilesRepository(client=self.mock_client)
        self.auth_service = AuthService(
            supabase_client=self.mock_client,
            profiles_repo=self.mock_repo
        )

        # Mock table operations to interact with in-memory dict
        def mock_table(table_name):
            query = MagicMock()
            if table_name == "profiles":
                def mock_select(*args):
                    select_query = MagicMock()
                    def mock_eq(col, val):
                        exec_mock = MagicMock()
                        if col == "id":
                            rec = self.mock_profiles_db.get(val)
                            exec_mock.execute.return_value = MagicMock(data=[rec] if rec else [])
                        elif col == "username":
                            matches = [r for r in self.mock_profiles_db.values() if r["username"] == val]
                            exec_mock.execute.return_value = MagicMock(data=matches)
                        return exec_mock
                    select_query.eq = mock_eq
                    return select_query

                def mock_insert(payload):
                    exec_mock = MagicMock()
                    self.mock_profiles_db[payload["id"]] = payload
                    exec_mock.execute.return_value = MagicMock(data=[payload])
                    return exec_mock

                def mock_update(payload):
                    update_query = MagicMock()
                    def mock_eq(col, val):
                        exec_mock = MagicMock()
                        if val in self.mock_profiles_db:
                            self.mock_profiles_db[val].update(payload)
                            exec_mock.execute.return_value = MagicMock(data=[self.mock_profiles_db[val]])
                        else:
                            exec_mock.execute.return_value = MagicMock(data=[])
                        return exec_mock
                    update_query.eq = mock_eq
                    return update_query

                query.select = mock_select
                query.insert = mock_insert
                query.update = mock_update
            return query

        self.mock_client.table = mock_table

    def test_complete_student_lifecycle(self):
        # 1. Sign Up Step
        user_uuid = "00000000-0000-0000-0000-111111111111"
        mock_user = MagicMock(id=user_uuid, email="alex@school.edu")
        mock_session = MagicMock(access_token="tok_123", refresh_token="ref_123")
        self.mock_client.auth.sign_up.return_value = MagicMock(user=mock_user, session=mock_session)

        signup_res = self.auth_service.sign_up(
            email="alex@school.edu",
            password="securePassword123",
            username="alex_sound"
        )
        self.assertTrue(signup_res.success)
        self.assertEqual(signup_res.profile["username"], "alex_sound")
        self.assertEqual(signup_res.profile["role"], "student")

        # Verify profile is now in DB
        db_profile = self.mock_repo.get_profile(user_uuid)
        self.assertIsNotNone(db_profile)
        self.assertEqual(db_profile["username"], "alex_sound")

        # 2. Duplicate Username Rejection Step
        dup_user_res = self.auth_service.sign_up(
            email="other@school.edu",
            password="anotherPassword123",
            username="alex_sound"
        )
        self.assertFalse(dup_user_res.success)
        self.assertIn("already taken", dup_user_res.error_message)

        # 3. Log In Step
        self.mock_client.auth.sign_in_with_password.return_value = MagicMock(user=mock_user, session=mock_session)
        login_res = self.auth_service.log_in(email="alex@school.edu", password="securePassword123")
        self.assertTrue(login_res.success)
        self.assertEqual(login_res.profile["username"], "alex_sound")

        # 4. View Profile & Update Display Name Step
        current_profile = self.mock_repo.get_profile(user_uuid)
        self.assertEqual(current_profile["display_name"], "alex_sound")

        # Update display name
        update_res = self.mock_repo.update_display_name(user_uuid, "Alex The Explorer")
        self.assertEqual(update_res["display_name"], "Alex The Explorer")

        # Re-fetch from DB to confirm persistence
        re_fetched = self.mock_repo.get_profile(user_uuid)
        self.assertEqual(re_fetched["display_name"], "Alex The Explorer")

        # 5. Log Out Step
        self.auth_service.log_out()
        self.mock_client.auth.sign_out.assert_called_once()


if __name__ == "__main__":
    unittest.main()
