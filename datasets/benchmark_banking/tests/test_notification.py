import pytest
from datasets.benchmark_banking.src.notification_service import NotificationService


class TestNotification:
    """Tests for REQ-006: Transaction Notification and Customer Alerts."""

    def setup_method(self):
        self.notifier = NotificationService()

    def test_dispatch_transfer_alert_masked(self):
        """Validates REQ-006: dispatch real-time notification alert with masked account number."""
        success = self.notifier.dispatch_transfer_alert("user@bank.com", "1234567890", 250.0, is_debit=True)
        assert success is True
        assert len(self.notifier.outbox) == 1
        msg = self.notifier.outbox[0]["message"]
        assert "Debit" in msg
        assert "$250.00" in msg
        assert "******7890" in msg

    def test_send_login_notification_security(self):
        """Validates REQ-006: dispatch security login alert to customer email."""
        success = self.notifier.send_login_notification("user@bank.com", "10.0.0.1")
        assert success is True
        assert len(self.notifier.outbox) == 1
        assert "10.0.0.1" in self.notifier.outbox[0]["message"]
