import pytest
from datasets.benchmark_banking.src.account_service import AccountService
from datasets.benchmark_banking.src.transfer_service import TransferService


class TestTransfer:
    """Tests for REQ-003 (Fund Transfer), REQ-004 (Overdraft Protection), and REQ-009 (Daily Withdrawal Limits)."""

    def setup_method(self):
        self.accounts = AccountService()
        self.transfer_service = TransferService(self.accounts)
        self.acc1 = self.accounts.create_account("cust_1", "CHECKING", initial_deposit=1000.0)["account_number"]
        self.acc2 = self.accounts.create_account("cust_2", "CHECKING", initial_deposit=200.0)["account_number"]

    def test_process_transfer_success(self):
        """Validates REQ-003: atomic domestic fund transfer debiting source and crediting destination."""
        res = self.transfer_service.process_transfer(self.acc1, self.acc2, 300.0)
        assert res["status"] == "COMPLETED"
        assert self.accounts.get_balance(self.acc1) == 700.0
        assert self.accounts.get_balance(self.acc2) == 500.0

    def test_overdraft_protection_enforcement(self):
        """Validates REQ-004: allow transfer within authorized overdraft, reject when limit exceeded."""
        self.transfer_service.set_overdraft_limit(self.acc1, 500.0)
        # Attempt transfer of 1200 (balance 1000 - 1200 = -200, within 500 overdraft)
        res = self.transfer_service.process_transfer(self.acc1, self.acc2, 1200.0)
        assert res["status"] == "COMPLETED"
        assert self.accounts.get_balance(self.acc1) == -200.0

        # Attempt additional transfer exceeding overdraft limit
        with pytest.raises(ValueError, match="Insufficient funds and overdraft limit exceeded"):
            self.transfer_service.process_transfer(self.acc1, self.acc2, 400.0)

    def test_daily_withdrawal_limit_velocity(self):
        """Validates REQ-009: blocks cumulative transfers exceeding the daily velocity ceiling."""
        self.transfer_service.daily_limit = 1000.0
        # First transfer of 800 should pass
        self.transfer_service.process_transfer(self.acc1, self.acc2, 800.0)
        # Second transfer of 300 exceeds 1000 daily limit
        with pytest.raises(PermissionError, match="Daily transfer velocity limit exceeded"):
            self.transfer_service.process_transfer(self.acc1, self.acc2, 300.0)
