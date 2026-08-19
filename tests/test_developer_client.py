"""Unit tests verifying developer client isolation, service role key handling, and absence from app runtime."""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.developer_client import (
    get_service_role_key,
    get_privileged_supabase_client,
    PrivilegedConfigurationError,
)


class TestDeveloperClientSecurity(unittest.TestCase):
    """Verify security isolation of the developer-only privileged client."""

    def test_missing_service_role_key_raises_privileged_config_error(self):
        base_env = {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_ANON_KEY": "test-anon-key",
        }
        with patch.dict(os.environ, base_env, clear=True), \
             patch("streamlit.secrets", base_env), \
             patch("scripts.developer_client._read_toml_file", return_value={}):
            with self.assertRaises(PrivilegedConfigurationError):
                get_privileged_supabase_client()

    def test_service_role_key_read_from_environment(self):
        with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "valid-dev-service-key"}), \
             patch("streamlit.secrets", {}), \
             patch("scripts.developer_client._read_toml_file", return_value={}):
            key = get_service_role_key()
            self.assertEqual(key, "valid-dev-service-key")

    def test_placeholder_service_role_key_ignored(self):
        with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key-here"}), \
             patch("streamlit.secrets", {}), \
             patch("scripts.developer_client._read_toml_file", return_value={}):
            key = get_service_role_key()
            self.assertIsNone(key)

    def test_service_role_key_not_referenced_in_runtime_application(self):
        """
        Scan all runtime application files (app.py, pages/, services/, repositories/)
        to ensure SUPABASE_SERVICE_ROLE_KEY or developer_client are NEVER imported or used at runtime.
        """
        runtime_dirs = [
            Path("pages"),
            Path("services"),
            Path("repositories"),
        ]
        runtime_files = [Path("app.py")]
        for d in runtime_dirs:
            runtime_files.extend(d.glob("*.py"))

        forbidden_patterns = [
            r"SUPABASE_SERVICE_ROLE_KEY",
            r"developer_client",
            r"get_privileged_supabase_client",
        ]

        for py_file in runtime_files:
            content = py_file.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                match = re.search(pattern, content)
                self.assertIsNone(
                    match,
                    f"Forbidden pattern '{pattern}' found in runtime application file '{py_file}'."
                )


if __name__ == "__main__":
    unittest.main()
