# Banking Core Platform — Software Requirements Specification

## REQ-001: User Authentication and Credential Verification
Priority: High
Category: Security
Version: 1.0
The system shall authenticate bank customers and administrative staff using unique usernames and hashed passwords.
### Acceptance Criteria
- Verify user credentials against the secure identity store.
- Reject invalid passwords and lock accounts after 5 failed consecutive attempts.
- Issue a secure session token upon successful credential validation.

## REQ-002: Bank Account Opening and Initialization
Priority: High
Category: CoreBanking
Version: 1.0
The system shall allow new and existing verified customers to open checking and savings accounts with an initial deposit.
### Acceptance Criteria
- Generate a unique 10-digit account number.
- Assign currency, account type, and link customer identity.
- Initialize opening ledger balance and emit an account creation event.

## REQ-003: Domestic Fund Transfer Between Accounts
Priority: High
Category: Transactions
Version: 1.0
The system shall process funds transfers between internal accounts and external domestic bank accounts atomically.
### Acceptance Criteria
- Debit source account balance and credit destination account within a single transactional boundary.
- Validate that sender account has sufficient available funds.
- Generate a unique transaction reference number and record timestamps.

## REQ-004: Overdraft Protection and Credit Limit Enforcement
Priority: Medium
Category: RiskManagement
Version: 1.0
The system shall verify if an account has approved overdraft protection when debit transactions exceed available balance.
### Acceptance Criteria
- Prevent account balance from dropping below the authorized overdraft threshold.
- Apply standard overdraft processing fees if configured.
- Reject transfer requests when overdraft limits are exceeded.

## REQ-005: Security Audit Logging and Transaction Trail
Priority: High
Category: Compliance
Version: 1.0
The system shall maintain an immutable, tamper-evident audit trail of all financial transactions and security-critical events.
### Acceptance Criteria
- Log user identity, timestamp, IP address, event type, and outcome for all transactions.
- Prevent modification or deletion of existing audit records.
- Provide querying mechanisms for compliance and forensic investigations.

## REQ-006: Transaction Notification and Customer Alerts
Priority: Medium
Category: CustomerExperience
Version: 1.0
The system shall dispatch real-time notifications via email or SMS whenever account debits, credits, or logins occur.
### Acceptance Criteria
- Send immediate alert message upon completed fund transfer.
- Include masked account number, transaction amount, and timestamp in alert body.
- Support opt-out for marketing alerts while keeping security alerts mandatory.

## REQ-007: Account Balance Inquiry and Statement Generation
Priority: Medium
Category: CoreBanking
Version: 1.0
The system shall provide real-time account balances and generate monthly historical account statements in structured formats.
### Acceptance Criteria
- Calculate available balance including pending credits and debits.
- Filter statement transactions by custom start and end date ranges.
- Export transaction summaries with opening and closing balances.

## REQ-008: Role-Based Access Control and Permission Verification
Priority: High
Category: Security
Version: 1.0
The system shall enforce role-based access control (RBAC) to ensure tellers, branch managers, and auditors only perform permitted actions.
### Acceptance Criteria
- Restrict sensitive account operations (e.g. limit overrides) to manager roles.
- Deny unauthorized access attempts and raise a security event.
- Validate permissions on every administrative endpoint request.

## REQ-009: Daily Withdrawal Limit and Velocity Check
Priority: Medium
Category: FraudPrevention
Version: 1.0
The system shall enforce daily cumulative withdrawal and transfer limits per customer to prevent unauthorized draining of funds.
### Acceptance Criteria
- Track aggregate debit transactions within a rolling 24-hour window.
- Block transfers exceeding the customer's daily allowed ceiling.
- Allow authorized administrators to temporarily increase withdrawal limits.

## REQ-010: KYC Customer Identity Verification and Document Upload
Priority: High
Category: Compliance
Version: 1.0
The system shall verify customer identity documents (passport, national ID) and track KYC compliance status before enabling account operations.
### Acceptance Criteria
- Validate document submission and record verification status (PENDING, VERIFIED, REJECTED).
- Restrict full transactional privileges until KYC verification is marked as VERIFIED.
- Flag high-risk accounts requiring enhanced due diligence.
