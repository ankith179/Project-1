import os
import pytest
from ingestion.code_parser import CodeParser


def test_parse_python_code(tmp_path):
    py_code = '''
"""Module docstring."""
import math
from datetime import datetime

class PaymentGateway:
    """Payment gateway client."""

    def process_charge(self, amount: float) -> bool:
        """Processes transaction."""
        math.ceil(amount)
        return True

def standalone_helper():
    pass
'''
    test_file = tmp_path / "gateway.py"
    test_file.write_text(py_code, encoding="utf-8")

    parser = CodeParser()
    artifacts = parser.parse_file(str(test_file))

    identifiers = [a.artifact_identifier for a in artifacts]
    types = [a.artifact_type for a in artifacts]

    assert "MODULE" in types
    assert "CLASS" in types
    assert "METHOD" in types
    assert "FUNCTION" in types

    method_art = next(a for a in artifacts if a.name == "process_charge")
    assert method_art.class_name == "PaymentGateway"
    assert "amount" in method_art.signature
    assert "ceil" in method_art.calls
