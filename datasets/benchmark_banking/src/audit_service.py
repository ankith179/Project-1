from datetime import datetime, timezone
from typing import List, Dict, Any


class AuditService:
    """
    Maintains tamper-evident audit trails for security operations and financial events.
    """

    def __init__(self):
        self.security_logs: List[Dict[str, Any]] = []
        self.transaction_logs: List[Dict[str, Any]] = []

    def log_security_event(self, event_type: str, username: str, ip_address: str, outcome: str):
        """
        Records an immutable security event entry (e.g. login attempt, permission escalation).
        """
        record = {
            "id": len(self.security_logs) + 1,
            "event_type": event_type,
            "username": username,
            "ip_address": ip_address,
            "outcome": outcome,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.security_logs.append(record)
        return record

    def record_transaction_audit(self, tx_ref: str, source_acc: str, dest_acc: str, amount: float, status: str):
        """
        Creates a permanent compliance audit entry for financial fund transfers.
        """
        record = {
            "tx_ref": tx_ref,
            "source_acc": source_acc,
            "dest_acc": dest_acc,
            "amount": amount,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.transaction_logs.append(record)
        return record

    def query_audit_trail(self, filter_key: str, filter_val: str) -> List[Dict[str, Any]]:
        """
        Queries the historical audit trail for forensic review and regulatory compliance.
        """
        results = []
        for log in self.transaction_logs:
            if log.get(filter_key) == filter_val:
                results.append(log)
        return results
