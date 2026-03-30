"""Playwright-oriented flow recording helpers from browser-use interaction metadata."""
from app.utils.playwright_flow_recording import (
    SCHEMA_VERSION,
    build_locator_bundle,
    build_playwright_suggestions,
    css_selector_from_tag_and_classes,
    pick_stable_attributes,
    wrap_playwright_flow_recording,
)


def test_pick_stable_attributes_filters_keys():
    attrs = {"id": "x", "class": "noise", "data-testid": "login", "random": "y"}
    stable = pick_stable_attributes(attrs)
    assert stable == {"id": "x", "data-testid": "login"}
    assert "class" not in stable


def test_suggestions_order_testid_before_xpath():
    sug = build_playwright_suggestions(
        attributes={"data-testid": "submit", "role": "button"},
        ax_name="Go",
        node_name="button",
        xpath="/html/body/button[1]",
    )
    kinds = [s["kind"] for s in sug]
    assert kinds[0] == "testId"
    assert any(k == "xpath" for k in kinds)


def test_suggestions_include_css_compound_from_class():
    sug = build_playwright_suggestions(
        attributes={"class": "p-3 d-flex justify-content-between align-items-center"},
        ax_name=None,
        node_name="div",
        xpath="//div[1]",
    )
    kinds = [s["kind"] for s in sug]
    assert "css" in kinds
    css_s = next(s for s in sug if s["kind"] == "css")
    assert css_s["selector"] == "div.p-3.d-flex.justify-content-between.align-items-center"
    assert kinds.index("css") < kinds.index("xpath")


def test_css_selector_skips_unsafe_class_tokens():
    assert css_selector_from_tag_and_classes("div", "ok w-[1rem] tail") == "div.ok.tail"


def test_locator_bundle_includes_class_tokens_when_class_present():
    b = build_locator_bundle(
        xpath="//x",
        attributes={"class": "foo bar", "id": "z"},
        node_name="div",
    )
    assert b["class_tokens"] == ["foo", "bar"]
    kinds = [s["kind"] for s in b["playwright_suggestions"]]
    assert "css" in kinds


def test_locator_bundle_includes_backend_node():
    b = build_locator_bundle(
        xpath="//div[@id='a']",
        backend_node_id=42,
        frame_id="frame1",
        attributes={"id": "a"},
        ax_name=None,
        node_name="div",
    )
    assert b["backend_node_id"] == 42
    assert b["frame_id"] == "frame1"
    assert b["xpath"] == "//div[@id='a']"
    assert b["attributes"] == {"id": "a"}


def test_wrap_recording_schema():
    steps = [{"order": 1, "action": "navigate", "target": "https://e.com", "locator": None}]
    w = wrap_playwright_flow_recording(start_url="https://e.com", steps=steps, goal_reached=True)
    assert w["schema_version"] == SCHEMA_VERSION
    assert w["source"] == "browser-use-observation"
    assert w["steps"] == steps
    assert w["goal_reached"] is True
