import pytest
from traceability.ir_model import IRTraceabilityModel
from traceability.hybrid_model import HybridTraceabilityModel


def test_ir_model_tfidf_and_bm25():
    corpus = [
        {
            "artifact_identifier": "auth_service.py::login",
            "name": "login",
            "code_content": "def login(user, password): verify user credential"
        },
        {
            "artifact_identifier": "payment.py::charge",
            "name": "charge",
            "code_content": "def charge(card, amount): process credit card payment"
        }
    ]

    tfidf_model = IRTraceabilityModel(method="tfidf")
    tfidf_model.fit(corpus)
    ranked_tfidf = tfidf_model.query_similarity("user authentication and credential login")
    assert ranked_tfidf[0][0]["name"] == "login"
    assert ranked_tfidf[0][1] > ranked_tfidf[1][1]

    bm25_model = IRTraceabilityModel(method="bm25")
    bm25_model.fit(corpus)
    ranked_bm25 = bm25_model.query_similarity("credit card payment transaction")
    assert ranked_bm25[0][0]["name"] == "charge"
    assert ranked_bm25[0][1] > ranked_bm25[1][1]


def test_hybrid_model_annotation_boost():
    corpus = [
        {
            "artifact_identifier": "test_account.py::test_balance",
            "name": "test_balance",
            "target_refs": ["REQ-002"],
            "test_content": "assert balance == 100"
        },
        {
            "artifact_identifier": "test_other.py::test_other",
            "name": "test_other",
            "target_refs": [],
            "test_content": "assert True"
        }
    ]

    hybrid = HybridTraceabilityModel()
    hybrid.fit(corpus)
    ranked = hybrid.query_similarity("REQ-002", "inquire account balance")
    assert ranked[0][0]["artifact_identifier"] == "test_account.py::test_balance"
    assert ranked[0][1] >= 0.5
