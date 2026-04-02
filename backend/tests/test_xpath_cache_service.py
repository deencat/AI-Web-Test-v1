"""Tests for XPath cache-key normalization behavior."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.xpath_cache_service import XPathCacheService


def test_generate_cache_key_normalizes_mastercard_session_urls():
    instruction = "Step 45: Input card holder name test"
    session_url_a = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION0002122229635M30652816E8"
    session_url_b = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION0002963629514H1563650M70"

    assert XPathCacheService.generate_cache_key(session_url_a, instruction) == XPathCacheService.generate_cache_key(
        session_url_b,
        instruction,
    )


def test_generate_cache_key_keeps_instruction_specificity_after_gateway_normalization():
    session_url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION0002122229635M30652816E8"

    key_a = XPathCacheService.generate_cache_key(session_url, "Step 45: Input card holder name test")
    key_b = XPathCacheService.generate_cache_key(session_url, "Step 46: Input CVV 100")

    assert key_a != key_b


def test_generate_cache_key_does_not_merge_gateway_and_autopay_pages():
    instruction = "Step 45: Input card holder name test"
    gateway_url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION0002122229635M30652816E8"
    autopay_url = "https://three.com.hk/postpaid/en/checkout/checkout?promotionId=HPPRM0000000187&step=autopay"

    assert XPathCacheService.generate_cache_key(gateway_url, instruction) != XPathCacheService.generate_cache_key(
        autopay_url,
        instruction,
    )