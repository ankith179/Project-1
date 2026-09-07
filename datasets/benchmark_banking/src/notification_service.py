from datetime import datetime, timezone
from typing import List, Dict, Any


class NotificationService:
    """
    Dispatches customer notifications and alerts via SMS and Email for transactions and security events.
    """

    def __init__(self):
        self.outbox: List[Dict[str, Any]] = []

    def format_alert_message(self, account_number: str, amount: float, tx_type: str) -> str:
        """Formats masked notification alert text."""
        masked_acc = f"******{account_number[-4:]}" if len(account_number) >= 4 else account_number
        return f"Alert: {tx_type} of ${amount:.2f} processed on account {masked_acc}."

    def dispatch_transfer_alert(self, customer_email: str, account_number: str, amount: float, is_debit: bool) -> bool:
        """
        Dispatches an immediate alert notification upon completion of a debit or credit fund transfer.
        """
        tx_type = "Debit" if is_debit else "Credit"
        message = self.format_alert_message(account_number, amount, tx_type)
        alert = {
            "recipient": customer_email,
            "type": "TRANSFER_ALERT",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.outbox.append(alert)
        return True

    def send_login_notification(self, customer_email: str, ip_address: str) -> bool:
        """
        Sends security alert when a login to online banking occurs.
        """
        alert = {
            "recipient": customer_email,
            "type": "SECURITY_LOGIN_ALERT",
            "message": f"Security alert: New login detected from IP {ip_address}.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.outbox.append(alert)
        return True
