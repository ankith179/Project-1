import hashlib
import secrets
from typing import Dict, Any, Optional


class AuthService:
    """
    Handles user authentication, password verification, session token management,
    and role-based access control.
    """

    def __init__(self):
        self.user_database: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, str] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.user_roles: Dict[str, str] = {}

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Hashes a password with a secure salt."""
        salt = salt or "secure_bank_salt"
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()

    def register_user(self, username: str, password: str, role: str = "CUSTOMER") -> bool:
        """Registers a new user with hashed credentials and role."""
        if username in self.user_database:
            return False
        self.user_database[username] = {
            "password_hash": self.hash_password(password),
            "locked": False,
        }
        self.user_roles[username] = role
        self.failed_attempts[username] = 0
        return True

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """
        Authenticates a user against stored credentials.
        Locks account after 5 consecutive failures.
        Returns a session token upon success.
        """
        user = self.user_database.get(username)
        if not user or user.get("locked"):
            return None

        expected_hash = user["password_hash"]
        actual_hash = self.hash_password(password)

        if actual_hash == expected_hash:
            self.failed_attempts[username] = 0
            token = secrets.token_hex(16)
            self.active_sessions[token] = username
            return token
        else:
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            if self.failed_attempts[username] >= 5:
                user["locked"] = True
            return None

    def check_user_role(self, username: str, required_role: str) -> bool:
        """
        Verifies role-based access control permissions for a given user.
        Tellers, Branch Managers, and Auditors have hierarchical roles.
        """
        role_hierarchy = {"CUSTOMER": 1, "TELLER": 2, "BRANCH_MANAGER": 3, "AUDITOR": 4}
        user_role = self.user_roles.get(username, "CUSTOMER")
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
