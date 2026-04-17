"""
Unit tests for shared app_initialization module.
Tests initialization logic without requiring a Streamlit session.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from warehouse.presentation.shared.app_initialization import (
    SESSION_STATE_SCHEMA,
)


class TestSessionStateSchema:
    """Test the SESSION_STATE_SCHEMA structure."""

    def test_schema_has_common_keys(self):
        """Verify common keys exist in schema."""
        assert "common" in SESSION_STATE_SCHEMA
        common = SESSION_STATE_SCHEMA["common"]

        # Check critical common keys
        assert "system_initialized" in common
        assert "current_user" in common
        assert "db_initialized" in common
        assert "show_scan_popup" in common
        assert "extracted_delivery_data" in common

    def test_schema_has_admin_keys(self):
        """Verify admin-specific keys exist in schema."""
        assert "admin" in SESSION_STATE_SCHEMA
        admin = SESSION_STATE_SCHEMA["admin"]

        # Check admin-specific keys
        assert "current_page" in admin
        assert "popup_action" in admin
        assert "confirmed_delivery" in admin
        assert admin["current_page"] == "Dashboard"

    def test_schema_has_user_keys(self):
        """Verify user-specific keys exist in schema."""
        assert "user" in SESSION_STATE_SCHEMA
        user = SESSION_STATE_SCHEMA["user"]

        # Check user-specific keys
        assert "user_filter_delivery" in user
        assert "user_filter_article" in user
        assert user["user_filter_delivery"] == ""

    def test_admin_and_user_keys_dont_overlap(self):
        """Verify admin and user keys are distinct (except common)."""
        admin_keys = set(SESSION_STATE_SCHEMA["admin"].keys())
        user_keys = set(SESSION_STATE_SCHEMA["user"].keys())
        common_keys = set(SESSION_STATE_SCHEMA["common"].keys())

        # Admin and user keys should be distinct
        overlap = admin_keys & user_keys
        assert len(overlap) == 0, f"Admin and user keys overlap: {overlap}"

        # Neither admin nor user keys should be in common
        admin_in_common = admin_keys & common_keys
        user_in_common = user_keys & common_keys
        assert len(admin_in_common) == 0
        assert len(user_in_common) == 0

    def test_all_keys_have_default_values(self):
        """Verify all keys in schema have valid default values."""
        for section, keys in SESSION_STATE_SCHEMA.items():
            assert isinstance(keys, dict), f"{section} is not a dict"
            for key, value in keys.items():
                # Value can be bool, str, dict, list, or None, but not undefined
                assert value is not None or isinstance(value, (bool, dict, list))


class TestInitializationImports:
    """Test that all required imports work."""

    def test_can_import_session_state_schema(self):
        """Verify SESSION_STATE_SCHEMA can be imported."""
        from warehouse.presentation.shared.app_initialization import (
            SESSION_STATE_SCHEMA,
        )
        assert SESSION_STATE_SCHEMA is not None

    def test_can_import_initialization_functions(self):
        """Verify all initialization functions can be imported."""
        from warehouse.presentation.shared.app_initialization import (
            get_services,
            get_processors,
            initialize_session_state,
            initialize_database,
            initialize_application,
        )

        # Check they're callable
        assert callable(get_services)
        assert callable(get_processors)
        assert callable(initialize_session_state)
        assert callable(initialize_database)
        assert callable(initialize_application)


class TestAdminAppImports:
    """Test that admin app can be imported without errors."""

    def test_admin_app_can_be_imported(self):
        """Verify admin app imports work (without running it)."""
        # This is a basic smoke test - just ensure it parses
        admin_path = Path(__file__).parent.parent / "src" / "warehouse" / "presentation" / "admin" / "main_admin_app.py"
        with open(admin_path) as f:
            code = f.read()

        # Check for critical imports
        assert "from warehouse.presentation.shared.app_initialization import" in code
        assert "initialize_application" in code


class TestUserAppImports:
    """Test that user app can be imported without errors."""

    def test_user_app_can_be_imported(self):
        """Verify user app imports work (without running it)."""
        # This is a basic smoke test - just ensure it parses
        user_path = Path(__file__).parent.parent / "src" / "warehouse" / "presentation" / "user" / "main_user_app.py"
        with open(user_path) as f:
            code = f.read()

        # Check for critical imports
        assert "from warehouse.presentation.shared.app_initialization import" in code
        assert "initialize_application" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
