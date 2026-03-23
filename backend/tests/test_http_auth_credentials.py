"""Tests for shared HTTP Basic auth helpers (UAT + URL embedding)."""
from app.utils.http_auth_credentials import (
    http_credentials_for_url,
    url_with_embedded_http_basic_auth,
    UAT_HTTP_CREDENTIALS,
)


def test_uat_url_returns_uat_credentials():
    c = http_credentials_for_url("https://wwwuat.three.com.hk/path", None)
    assert c == UAT_HTTP_CREDENTIALS


def test_uat_http_scheme_returns_uat_credentials():
    """http://wwwuat.three.com.hk/ must still get UAT Basic auth (hostname match)."""
    c = http_credentials_for_url("http://wwwuat.three.com.hk/", None)
    assert c == UAT_HTTP_CREDENTIALS


def test_non_uat_with_user_returns_user():
    c = http_credentials_for_url(
        "https://example.com/",
        {"username": "u", "password": "p"},
    )
    assert c == {"username": "u", "password": "p"}


def test_url_embedding():
    u = url_with_embedded_http_basic_auth(
        "https://example.com/foo",
        "user",
        "p@ss",
    )
    assert u.startswith("https://")
    assert "example.com" in u
    assert "user" in u
    assert "p%40ss" in u or "p@ss" in u
