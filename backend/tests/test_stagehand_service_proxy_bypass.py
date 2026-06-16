from app.services.stagehand_service import _ensure_loopback_no_proxy
from app.utils.proxy_bypass import ensure_loopback_no_proxy


def test_stagehand_reexports_ensure_loopback_no_proxy():
    assert _ensure_loopback_no_proxy is ensure_loopback_no_proxy