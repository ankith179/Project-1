import pytest
from datasets.benchmark_banking.src.auth_service import AuthService


class TestAuth:
    """Tests for REQ-001 (User Authentication) and REQ-008 (Role-Based Access Control)."""

    def setup_method(self):
        self.auth = AuthService()
        self.auth.register_user("john_doe", "SuperSecret123", role="CUSTOMER")
        self.auth.register_user("admin_user", "AdminSecret456", role="BRANCH_MANAGER")

    def test_authenticate_valid_credentials(self):
        """Validates REQ-001: authenticate valid username and password returning token."""
        token = self.auth.authenticate_user("john_doe", "SuperSecret123")
        assert token is not None
        assert len(token) == 32

    def test_authenticate_invalid_password_locks_after_5_attempts(self):
        """Validates REQ-001: reject invalid credentials and lock account after 5 attempts."""
        for _ in range(5):
            token = self.auth.authenticate_user("john_doe", "WrongPass")
            assert token is None

        # 6th attempt should remain locked even with correct password
        locked_token = self.auth.authenticate_user("john_doe", "SuperSecret123")
        assert locked_token is None

    def test_role_based_access_control(self):
        """Validates REQ-008: verify role-based access permissions for customer vs manager."""
        assert self.auth.check_user_role("john_doe", "CUSTOMER") is True
        assert self.auth.check_user_role("john_doe", "BRANCH_MANAGER") is False
        assert self.auth.check_user_role("admin_user", "BRANCH_MANAGER") is True
