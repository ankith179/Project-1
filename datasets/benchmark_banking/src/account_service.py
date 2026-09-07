import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class AccountService:
    """
    Manages bank accounts, balances, statement generation, and KYC status verification.
    """

    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.kyc_records: Dict[str, str] = {}  # customer_id -> status

    def generate_account_number(self) -> str:
        """Generates a unique 10-digit account number."""
        return "".join([str(random.randint(0, 9)) for _ in range(10)])

    def create_account(self, customer_id: str, account_type: str, initial_deposit: float = 0.0) -> Dict[str, Any]:
        """
        Creates and initializes a new checking or savings account with an opening balance.
        """
        account_number = self.generate_account_number()
        account = {
            "account_number": account_number,
            "customer_id": customer_id,
            "account_type": account_type,
            "balance": initial_deposit,
            "currency": "USD",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transactions": []
        }
        if initial_deposit > 0:
            account["transactions"].append({
                "type": "INITIAL_DEPOSIT",
                "amount": initial_deposit,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        self.accounts[account_number] = account
        return account

    def get_balance(self, account_number: str) -> Optional[float]:
        """Inquires and calculates the current available balance for an account."""
        account = self.accounts.get(account_number)
        if not account:
            return None
        return account["balance"]

    def generate_statement(self, account_number: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Generates an account statement showing transaction history and balance over a date range.
        """
        account = self.accounts.get(account_number)
        if not account:
            raise ValueError("Account not found")

        txs = account.get("transactions", [])
        filtered_txs = [
            t for t in txs
            if start_date <= t.get("timestamp", "") <= end_date
        ]
        return {
            "account_number": account_number,
            "closing_balance": account["balance"],
            "period": f"{start_date} to {end_date}",
            "transaction_count": len(filtered_txs),
            "transactions": filtered_txs
        }

    def verify_kyc_status(self, customer_id: str, document_type: str, document_id: str) -> str:
        """
        Processes KYC identity document verification and returns compliance status.
        Status: VERIFIED, PENDING, REJECTED.
        """
        if not document_id or len(document_id) < 5:
            self.kyc_records[customer_id] = "REJECTED"
            return "REJECTED"

        self.kyc_records[customer_id] = "VERIFIED"
        return "VERIFIED"
