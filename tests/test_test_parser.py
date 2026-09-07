import pytest
from ingestion.test_parser import TestParser


def test_parse_python_tests(tmp_path):
    test_code = '''
import pytest

class TestBilling:
    """Tests for REQ-003 billing."""

    def test_calculate_fee(self):
        """Validates REQ-003 fee calculation."""
        assert 10 > 5
        assert 20 == 20

def test_standalone_refund():
    assert True
'''
    test_file = tmp_path / "test_billing.py"
    test_file.write_text(test_code, encoding="utf-8")

    parser = TestParser()
    tests = parser.parse_file(str(test_file))

    assert len(tests) == 2
    method_names = [t.test_method for t in tests]
    assert "test_calculate_fee" in method_names
    assert "test_standalone_refund" in method_names

    t1 = next(t for t in tests if t.test_method == "test_calculate_fee")
    assert t1.test_class == "TestBilling"
    assert t1.assertions_count == 2
    assert "REQ-003" in t1.target_refs
