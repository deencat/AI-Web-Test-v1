"""Tests for offer table xlsx → markdown conversion."""
from __future__ import annotations

import io

import pytest

from app.services.offer_table_convert import (
    convert_offer_spreadsheet_to_markdown,
    is_offer_spreadsheet,
    reqiq_markdown_filename,
)


def test_is_offer_spreadsheet():
    assert is_offer_spreadsheet("Sample of DT Offer Table_20250729_updated.xlsx")
    assert not is_offer_spreadsheet("flow.png")


def test_csv_to_markdown():
    csv_bytes = b"plan,price\n5GBB-238,238\n"
    md = convert_offer_spreadsheet_to_markdown(csv_bytes, "offers.csv")
    assert "# DT Offer table" in md
    assert "5GBB-238" in md
    assert "| plan | price |" in md


def test_xlsx_to_markdown():
    pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "5GBB"
    ws.append(["Offer", "Price"])
    ws.append(["5GBB-WiFi7", "238"])
    buf = io.BytesIO()
    wb.save(buf)

    md = convert_offer_spreadsheet_to_markdown(buf.getvalue(), "offer.xlsx")
    assert "## Sheet: 5GBB" in md
    assert "5GBB-WiFi7" in md
    assert reqiq_markdown_filename("offer.xlsx") == "offer (offer table).md"
