from service import authenticate


def test_authenticate_user():
    assert authenticate("user", "password")
