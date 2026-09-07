import pytest
from datasets.benchmark_banking.src.account_service import AccountService


class TestAccount:
    """Tests for REQ-002 (Account Opening), REQ-007 (Balance & Statements), and REQ-010 (KYC)."""

    def setup_method(self):
        self.account_service = AccountService()

    def test_create_account_with_initial_deposit(self):
        """Validates REQ-002: opening checking account with initial deposit and generating 10-digit number."""
        acc = self.account_service.create_account("cust_101", "CHECKING", initial_deposit=500.0)
        assert len(acc["account_number"]) == 10
        assert acc["balance"] == 500.0
        assert acc["customer_id"] == "cust_101"

    def test_get_balance_inquiry(self):
        """Validates REQ-007: accurate real-time balance inquiry for an open account."""
        acc = self.account_service.create_account("cust_102", "SAVINGS", initial_deposit=1200.0)
        bal = self.account_service.get_balance(acc["account_number"])
        assert bal == 1200.0

    def test_kyc_verification_status(self):
        """Validates REQ-010: KYC customer identity document verification and compliance check."""
        status_valid = self.account_service.verify_kyc_status("cust_103", "PASSPORT", "P12345678")
        assert status_valid == "VERIFIED"

        status_invalid = self.account_service.verify_kyc_status("cust_104", "ID", "12")
        assert status_invalid == "REJECTED"
