"""
Three Hong Kong UAT (wwwuat.three.com.hk) environment constants.

Payment test card values are fixed for UAT; do not use in production.
"""
from urllib.parse import urlparse

# Hostname for Three HK preprod/UAT (http or https).
THREE_HK_UAT_HOSTNAME = "wwwuat.three.com.hk"

# UAT-only test card (never use real cards on UAT).
THREE_UAT_TEST_PAYMENT_CARD_NUMBER = "4111111111111111"
THREE_UAT_TEST_PAYMENT_EXPIRY = "12/28"
THREE_UAT_TEST_PAYMENT_CVV = "123"


def is_three_hk_uat_url(url: str) -> bool:
    """True when URL targets Three HK UAT host (http or https, any path)."""
    if not url:
        return False
    try:
        host = (urlparse(str(url).strip()).hostname or "").lower()
    except Exception:
        return False
    return host == THREE_HK_UAT_HOSTNAME


def three_uat_payment_test_instruction_block() -> str:
    """
    Text appended to browser-use / observation tasks for UAT payment steps.
    Values are stable UAT test credentials.
    """
    return f"""

            UAT PAYMENT / CARD DETAILS (Three HK wwwuat — use only on this environment):
            - When the flow asks for credit or debit card payment, use these UAT test card details exactly:
              • Card number: {THREE_UAT_TEST_PAYMENT_CARD_NUMBER}
              • Expiry date: {THREE_UAT_TEST_PAYMENT_EXPIRY}
              • CVV: {THREE_UAT_TEST_PAYMENT_CVV}
            - Enter them in the site's card fields as shown (expiry may be split into month/year fields: use 12 and 28 or 2028 per the form).
            - These are sandbox/test values for http(s)://{THREE_HK_UAT_HOSTNAME}/ only; do not assume they work on production.
            """
