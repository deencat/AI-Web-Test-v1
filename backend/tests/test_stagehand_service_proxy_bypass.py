import os

from app.services.stagehand_service import _ensure_loopback_no_proxy


def test_ensure_loopback_no_proxy_sets_required_hosts(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)

    _ensure_loopback_no_proxy()

    expected_hosts = {"127.0.0.1", "localhost", "::1"}
    for key in ("NO_PROXY", "no_proxy"):
        value = os.environ[key]
        assert expected_hosts.issubset({entry.strip() for entry in value.split(",") if entry.strip()})


def test_ensure_loopback_no_proxy_preserves_existing_entries(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "example.com,localhost")
    monkeypatch.setenv("no_proxy", "example.com,localhost")

    _ensure_loopback_no_proxy()

    values = {entry.strip() for entry in os.environ["NO_PROXY"].split(",") if entry.strip()}
    assert "example.com" in values
    assert "127.0.0.1" in values
    assert "localhost" in values
    assert "::1" in values