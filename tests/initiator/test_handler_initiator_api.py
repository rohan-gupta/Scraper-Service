"""Test initiator handler module."""
import initiator.handler_api as handler

def test_check_authorizations(monkeypatch):
    """Test check authorizations."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac"\
                      " OS X 10_15_1) AppleWebKit/537.36 "\
                      "(KHTML, like Gecko) Chrome/91.0.4472"\
                      ".77 Safari/537.36"
    }
    monkeypatch.setenv("API_KEY", "123")
    assert not handler.check_authorizations(headers)
    headers["api-key"] = "mock-key"
    assert not handler.check_authorizations(headers)
    headers["api-key"] = "123"
    assert handler.check_authorizations(headers)
