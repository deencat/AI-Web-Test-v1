"""Unit tests for URL snapshot capture and diff (HF-4)."""
from app.models.url_snapshot import UrlSnapshot
from app.services.url_snapshot_service import (
    diff_snapshot_records,
    element_fingerprint,
    html_summary,
    text_similarity,
    url_hash,
)


SAMPLE_HTML_A = """
<html><head><title>Plans</title></head><body>
<button id="buy">Subscribe</button><a href="/login">Login</a>
<p>Choose your 5G plan today.</p>
</body></html>
"""

SAMPLE_HTML_B = """
<html><head><title>Plans</title></head><body>
<button id="buy-now">Subscribe Now</button><a href="/login">Login</a>
<input name="voucher" type="text" />
<p>Choose your 5G plan today with voucher.</p>
</body></html>
"""


class TestUrlSnapshotService:
    def test_url_hash_stable(self):
        assert url_hash("https://example.com/") == url_hash("https://example.com")

    def test_fingerprint_detects_button_change(self):
        fp_a = element_fingerprint(SAMPLE_HTML_A)
        fp_b = element_fingerprint(SAMPLE_HTML_B)
        assert fp_a != fp_b

    def test_diff_material_change(self):
        baseline = UrlSnapshot(
            id=1,
            url="https://example.com",
            url_hash=url_hash("https://example.com"),
            page_title="Plans",
            html_summary=html_summary(SAMPLE_HTML_A),
            element_fingerprint=element_fingerprint(SAMPLE_HTML_A),
        )
        current = UrlSnapshot(
            id=2,
            url="https://example.com",
            url_hash=url_hash("https://example.com"),
            page_title="Plans",
            html_summary=html_summary(SAMPLE_HTML_B),
            element_fingerprint=element_fingerprint(SAMPLE_HTML_B),
        )
        result = diff_snapshot_records(baseline, current)
        assert result["material_change"] is True
        assert "fingerprint" in result["summary"].lower() or "similarity" in result["summary"].lower()

    def test_text_similarity_identical(self):
        text = html_summary(SAMPLE_HTML_A)
        assert text_similarity(text, text) == 1.0
