import pytest
from ingestion.requirements_parser import RequirementsParser


def test_parse_markdown_requirements():
    sample_md = """
# Platform Specifications

## REQ-001: User Authentication
Priority: High
Category: Security
Version: 1.2
The system shall authenticate users with passwords.
### Acceptance Criteria
- Check password hash
- Lock account after 5 tries

## REQ-002: Fund Transfer
Priority: Medium
Category: Core
The system shall transfer funds between accounts.
"""
    parser = RequirementsParser()
    reqs = parser.parse_content(sample_md)

    assert len(reqs) == 2
    assert reqs[0].req_identifier == "REQ-001"
    assert reqs[0].title == "User Authentication"
    assert reqs[0].priority == "HIGH"
    assert reqs[0].category == "SECURITY"
    assert reqs[0].version == "1.2"
    assert len(reqs[0].acceptance_criteria) == 2
    assert "Check password hash" in reqs[0].acceptance_criteria[0]

    assert reqs[1].req_identifier == "REQ-002"
    assert reqs[1].title == "Fund Transfer"
    assert reqs[1].priority == "MEDIUM"


def test_parse_plain_user_story():
    sample_story = """
As a customer, I want to view my balance so that I can manage my budget.
Acceptance Criteria:
- Display accurate balance
- Refresh in real time
"""
    parser = RequirementsParser()
    reqs = parser.parse_content(sample_story)

    assert len(reqs) >= 1
    assert "balance" in reqs[0].title.lower() or "customer" in reqs[0].title.lower()
