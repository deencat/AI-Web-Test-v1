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


def three_uat_my3_and_identity_upload_hints() -> str:
    """
    Navigation hints for Three HK UAT: avoid promotional traps and use the real upload control.

    The "Upload" step is often an <a> link inside the Identity Document card, not a <button>,
    so agents that only consider buttons may miss it.
    """
    return """

            THREE HK UAT — MY3 APP PROMO (CRITICAL):
            - Never click any control whose visible text is "Download My3 App" (or clearly promotes the My3 app download).
            - That action opens a blocking modal and does not advance checkout; treat it as off-limits.
            - If it is the only control you notice, scroll the page and use find_elements for links (a[href]) or text "Upload", "Next", "Continue", "Subscribe", or checkboxes/terms — do not use the My3 download button.

            THREE HK UAT — IDENTITY DOCUMENT / HKID UPLOAD (CRITICAL):
            - When you see the section titled "Identity Document" (or HKID upload instructions under "Register Info"), the file chooser is usually triggered by a blue underlined **"Upload"** link, not a primary button.
            - You MUST click that **"Upload"** link (or equivalent "Choose file" / file input) to attach the document; do not skip this step because no `<button>` labeled Upload exists.
            - After clicking Upload, complete the file picker using the provided available_file_paths when the browser-use upload tool applies.
            """
