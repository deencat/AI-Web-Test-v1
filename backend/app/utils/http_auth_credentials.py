"""
HTTP Basic Auth helpers shared by Observation (API/orchestration), Analysis realtime execution, and test runs.
"""
from typing import Dict, Optional
from urllib.parse import quote, urlparse, urlunparse

from app.utils.three_uat_test_credentials import is_three_hk_uat_url

# Legacy prefix check superseded by hostname match (supports http:// and https://).
UAT_URL_PREFIX = "https://wwwuat.three.com.hk/"
UAT_HTTP_CREDENTIALS: Dict[str, str] = {"username": "user", "password": "3.comUXuat"}


def http_credentials_for_url(
    url: str,
    user_credentials: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, str]]:
    """
    When URL is Three HK UAT, return UAT credentials.
    Otherwise return user-provided credentials if both username and password are set.
    """
    if not url:
        return None
    if is_three_hk_uat_url(str(url)):
        return dict(UAT_HTTP_CREDENTIALS)
    if user_credentials and user_credentials.get("username") and user_credentials.get("password"):
        return {
            "username": str(user_credentials["username"]).strip(),
            "password": str(user_credentials["password"]).strip(),
        }
    return None


def url_with_embedded_http_basic_auth(
    url: str,
    username: str,
    password: str,
) -> str:
    """Embed HTTP Basic credentials in URL for Playwright/Stagehand first navigation."""
    user_q = quote(username, safe="")
    pass_q = quote(password, safe="")
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    host = parsed.hostname or ""
    if not host:
        return url
    port = f":{parsed.port}" if parsed.port else ""
    auth_netloc = f"{user_q}:{pass_q}@{host}{port}"
    return urlunparse((parsed.scheme, auth_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
