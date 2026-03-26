"""Three HK UAT hostname + payment test instruction helpers."""
from app.utils.three_uat_test_credentials import (
    THREE_UAT_TEST_PAYMENT_CARD_NUMBER,
    THREE_UAT_TEST_PAYMENT_CVV,
    THREE_UAT_TEST_PAYMENT_EXPIRY,
    is_three_hk_uat_url,
    three_uat_my3_and_identity_upload_hints,
    three_uat_payment_test_instruction_block,
)


def test_is_three_hk_uat_url_http_and_https():
    assert is_three_hk_uat_url("http://wwwuat.three.com.hk/")
    assert is_three_hk_uat_url("https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/")
    assert not is_three_hk_uat_url("https://www.three.com.hk/")
    assert not is_three_hk_uat_url("")


def test_payment_block_contains_stable_test_values():
    block = three_uat_payment_test_instruction_block()
    assert THREE_UAT_TEST_PAYMENT_CARD_NUMBER in block
    assert THREE_UAT_TEST_PAYMENT_EXPIRY in block
    assert THREE_UAT_TEST_PAYMENT_CVV in block


def test_my3_and_identity_hints_cover_promo_and_upload_link():
    block = three_uat_my3_and_identity_upload_hints()
    assert "Download My3 App" in block
    assert "Identity Document" in block
    assert "Upload" in block
