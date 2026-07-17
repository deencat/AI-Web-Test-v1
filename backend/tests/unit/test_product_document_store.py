"""Tests for local product document cache."""
from pathlib import Path

from app.services import product_document_store as store


def test_remove_upload_clears_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_STORE_ROOT", tmp_path)
    product_id = "demo-product"
    store.save_upload(product_id, "flow-a.png", b"png", source_type="ux_ui")
    store.save_upload(product_id, "flow-b.png", b"png", source_type="ux_ui")

    assert store.remove_upload(product_id, "flow-a.png") is True
    assert not (tmp_path / product_id / "flow-a.png").is_file()
    assert (tmp_path / product_id / "flow-b.png").is_file()
    names = [f["filename"] for f in store._load_manifest(product_id)]
    assert names == ["flow-b.png"]


def test_remove_upload_for_reqiq_offer_table_md(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_STORE_ROOT", tmp_path)
    product_id = "demo-product"
    store.save_upload(product_id, "Offer Table.xlsx", b"xlsx", source_type="mvp_config")

    removed = store.remove_upload_for_reqiq_source(product_id, "Offer Table (offer table).md")
    assert removed is True
    assert not (tmp_path / product_id / "Offer Table.xlsx").is_file()
