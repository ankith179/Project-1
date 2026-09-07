import uuid
from datetime import datetime, timezone
from typing import Dict, Any


class TransferService:
    """
    Coordinates fund transfers between accounts, enforces overdraft limits,
    and applies daily velocity restrictions.
    """

    def __init__(self, account_service, audit_service=None):
        self.account_service = account_service
        self.audit_service = audit_service
        self.daily_transfers: Dict[str, float] = {}  # account_number -> total_today
        self.overdraft_limits: Dict[str, float] = {} # account_number -> max_overdraft
        self.daily_limit: float = 5000.0

    def set_overdraft_limit(self, account_number: str, limit: float):
        """Configures the allowed overdraft protection ceiling."""
        self.overdraft_limits[account_number] = limit

    def check_overdraft_allowance(self, account_number: str, amount: float) -> bool:
        """
        Verifies if an account has sufficient funds or approved overdraft buffer.
        """
        current_balance = self.account_service.get_balance(account_number)
        if current_balance is None:
            return False

        allowed_overdraft = self.overdraft_limits.get(account_number, 0.0)
        return (current_balance - amount) >= (-allowed_overdraft)

    def validate_daily_limits(self, account_number: str, amount: float) -> bool:
        """
        Enforces daily cumulative transfer/withdrawal limit to prevent fraud.
        """
        current_total = self.daily_transfers.get(account_number, 0.0)
        return (current_total + amount) <= self.daily_limit

    def process_transfer(self, source_acc: str, dest_acc: str, amount: float) -> Dict[str, Any]:
        """
        Executes an atomic transfer between two bank accounts.
        Validates funds, overdraft limits, and daily transfer limits.
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be strictly positive")

        if not self.validate_daily_limits(source_acc, amount):
            raise PermissionError("Daily transfer velocity limit exceeded")

        if not self.check_overdraft_allowance(source_acc, amount):
            raise ValueError("Insufficient funds and overdraft limit exceeded")

        src = self.account_service.accounts.get(source_acc)
        dst = self.account_service.accounts.get(dest_acc)
        if not src or not dst:
            raise ValueError("Invalid source or destination account")

        # Atomic debit and credit
        tx_ref = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        src["balance"] -= amount
        dst["balance"] += amount

        src["transactions"].append({
            "tx_ref": tx_ref,
            "type": "DEBIT_TRANSFER",
            "counterparty": dest_acc,
            "amount": amount,
            "timestamp": timestamp
        })

        dst["transactions"].append({
            "tx_ref": tx_ref,
            "type": "CREDIT_TRANSFER",
            "counterparty": source_acc,
            "amount": amount,
            "timestamp": timestamp
        })

        self.daily_transfers[source_acc] = self.daily_transfers.get(source_acc, 0.0) + amount

        if self.audit_service:
            self.audit_service.record_transaction_audit(tx_ref, source_acc, dest_acc, amount, "SUCCESS")

        return {
            "tx_ref": tx_ref,
            "source_account": source_acc,
            "dest_account": dest_acc,
            "amount": amount,
            "status": "COMPLETED",
            "timestamp": timestamp
        }
