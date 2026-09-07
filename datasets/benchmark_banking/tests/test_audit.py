import pytest
from datasets.benchmark_banking.src.audit_service import AuditService


class TestAudit:
    """Tests for REQ-005: Security Audit Logging and Transaction Trail."""

    def setup_method(self):
        self.audit = AuditService()

    def test_log_security_event_immutable(self):
        """Validates REQ-005: logging security-critical authentication and authorization events."""
        event = self.audit.log_security_event("LOGIN_FAILURE", "unknown_user", "192.168.1.50", "DENIED")
        assert event["id"] == 1
        assert event["outcome"] == "DENIED"
        assert len(self.audit.security_logs) == 1

    def test_record_transaction_audit_trail(self):
        """Validates REQ-005: recording compliance transaction records for fund transfers."""
        rec = self.audit.record_transaction_audit("tx-999", "acc_10", "acc_20", 450.0, "SUCCESS")
        assert rec["tx_ref"] == "tx-999"
        assert rec["amount"] == 450.0

        query_res = self.audit.query_audit_trail("tx_ref", "tx-999")
        assert len(query_res) == 1
        assert query_res[0]["status"] == "SUCCESS"
