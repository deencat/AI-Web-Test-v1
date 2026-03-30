"""Tests for on-disk flow recording after observation."""
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from app.utils.playwright_flow_recording import normalize_strict_replay_locator
from app.utils.flow_recording_persistence import (
    build_playwright_step_ir,
    build_recording_document,
    flow_recording_directory_name,
    observation_result_from_flow_recording_dir,
    persist_observation_flow_artifacts,
    persist_requirements_result_to_flow_recording,
    persist_test_case_flow_manifests,
    resolve_flow_recording_directory,
)


def test_build_recording_document_from_existing_wrapper():
    obs = {
        "playwright_flow_recording": {"schema_version": 1, "steps": [{"order": 1}], "start_url": "https://x.com"},
    }
    doc = build_recording_document(obs)
    assert doc["schema_version"] == 1
    assert len(doc["steps"]) == 1


def test_build_playwright_step_ir_from_steps():
    obs_steps = [
        {
            "order": 1,
            "action": "click",
            "target": "OK",
            "page_url": "https://e.com",
            "locator": {
                "playwright_suggestions": [{"kind": "role", "snippet": "page.getByRole('button')"}],
                "xpath": "//button",
                "attributes": {"role": "button"},
            },
        }
    ]
    doc = build_playwright_step_ir(obs_steps)
    assert doc["schema_version"] == 1
    assert doc["steps"][0]["action"] == "click"
    assert doc["steps"][0]["playwright_suggestions"][0]["kind"] == "role"


def test_normalize_strict_replay_locator_merges_flat_ir_step():
    """playwright_step_ir.json uses top-level xpath/suggestions (no nested locator)."""
    flat = {
        "order": 13,
        "action": "click",
        "element_type": "div",
        "target": "html/body/div/…",
        "xpath": "html/body/div/div[1]/main/div",
        "playwright_suggestions": [{"kind": "role", "role": "button", "name": "Next"}],
        "attributes": {"type": "button"},
    }
    loc = normalize_strict_replay_locator(flat)
    assert loc["xpath"] == "html/body/div/div[1]/main/div"
    assert loc["playwright_suggestions"][0]["kind"] == "role"


def test_normalize_strict_replay_locator_synthesizes_css_from_class_tokens():
    flat = {
        "action": "click",
        "element_type": "div",
        "xpath": "//x",
        "playwright_suggestions": [],
        "class_tokens": ["p-3", "d-flex", "justify-content-between"],
    }
    loc = normalize_strict_replay_locator(flat)
    css_kinds = [s.get("kind") for s in loc["playwright_suggestions"]]
    assert "css" in css_kinds
    assert any(
        str(s.get("selector", "")).startswith("div.") and "p-3" in str(s.get("selector", ""))
        for s in loc["playwright_suggestions"]
        if s.get("kind") == "css"
    )


def test_build_playwright_step_ir_passes_class_tokens():
    obs_steps = [
        {
            "order": 1,
            "action": "click",
            "target": "x",
            "locator": {
                "playwright_suggestions": [],
                "xpath": "//d",
                "attributes": {},
                "class_tokens": ["p-3", "d-flex"],
            },
        }
    ]
    doc = build_playwright_step_ir(obs_steps)
    assert doc["steps"][0]["class_tokens"] == ["p-3", "d-flex"]


def test_build_recording_document_from_flow_steps_only():
    obs = {
        "flow_steps": [{"order": 1, "action": "navigate", "target": "https://x.com"}],
        "start_url": "https://x.com",
        "page_context": {"goal_reached": True},
    }
    doc = build_recording_document(obs)
    assert doc["schema_version"] == 1
    assert doc["goal_reached"] is True
    assert doc["steps"][0]["action"] == "navigate"


def test_flow_recording_directory_name_sortable_utc():
    a = flow_recording_directory_name(
        "613bbc29-4bde-493d-bbcc-fa874fcaf69c",
        at=datetime(2026, 3, 24, 10, 0, 0, tzinfo=timezone.utc),
    )
    b = flow_recording_directory_name(
        "fa9e0459-cd7b-4d41-b1ce-111e3a6d0080",
        at=datetime(2026, 3, 26, 11, 30, 15, tzinfo=timezone.utc),
    )
    assert a < b
    assert a.startswith("20260324T100000Z_")
    assert a.endswith("_613bbc29")
    assert b.startswith("20260326T113015Z_")


def test_persist_writes_files_and_mutates_obs(tmp_path: Path):
    wf = "test-wf-001"
    obs = {
        "flow_steps": [
            {"order": 1, "action": "click", "target": "Go", "page_url": "https://e.com", "locator": None},
        ],
        "start_url": "https://e.com",
        "page_context": {"url": "https://e.com", "goal_reached": False},
    }
    fixed_dir = "20260326T120000Z_testwf001"
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=tmp_path):
        with patch(
            "app.utils.flow_recording_persistence.flow_recording_directory_name",
            return_value=fixed_dir,
        ):
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.FLOW_RECORDINGS_ENABLED = True
                out = persist_observation_flow_artifacts(wf, obs, enabled=True)

    assert out is not None
    assert "playwright_flow_recording_file" in out
    assert "playwright_step_ir_file" in out
    main = Path(out["playwright_flow_recording_file"])
    steps_f = Path(out["flow_steps_file"])
    ir_f = Path(out["playwright_step_ir_file"])
    assert main.exists()
    assert steps_f.exists()
    assert ir_f.exists()
    data = json.loads(main.read_text(encoding="utf-8"))
    assert data["source"] == "browser-use-observation"
    assert len(data["steps"]) == 1
    ir_data = json.loads(ir_f.read_text(encoding="utf-8"))
    assert ir_data["source"] == "observation-step-ir"
    assert len(ir_data["steps"]) == 1
    assert out["directory_name"] == fixed_dir
    assert obs["flow_recording_artifacts"]["directory"] == str((tmp_path / fixed_dir).resolve())
    assert obs["page_context"]["flow_recording_artifacts"]["workflow_id"] == wf

    mp = persist_test_case_flow_manifests(wf, [101, 102], obs, enabled=True)
    assert mp is not None and len(mp) == 2
    assert obs["flow_recording_artifacts"]["test_case_manifest_count"] == 2
    m0 = json.loads(Path(mp[0]).read_text(encoding="utf-8"))
    assert m0["test_case_id"] == 101
    assert m0["playwright_step_ir_file"] == str(ir_f.resolve())


def test_resolve_flow_recording_directory_rejects_escape(tmp_path: Path):
    base = tmp_path / "flow_recordings"
    base.mkdir()
    (base / "good").mkdir()
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=base):
        resolved = resolve_flow_recording_directory("good")
        assert resolved.name == "good"
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=base):
        with pytest.raises(ValueError, match="must be under"):
            resolve_flow_recording_directory("../outside")


def test_observation_result_from_flow_dir_playwright_file(tmp_path: Path):
    rec = tmp_path / "myrun"
    rec.mkdir()
    doc = {
        "schema_version": 1,
        "source": "browser-use-observation",
        "start_url": "https://example.com/start",
        "goal_reached": True,
        "steps": [
            {
                "order": 1,
                "action": "navigate",
                "target": "https://example.com/start",
                "page_url": "https://example.com/start",
                "page_title": "Home",
                "element_type": "navigate",
                "locator": None,
            },
            {
                "order": 2,
                "action": "click",
                "target": "Go",
                "page_url": "https://example.com/start",
                "element_type": "button",
                "locator": {"xpath": "//button"},
            },
        ],
    }
    (rec / "playwright_flow_recording.json").write_text(json.dumps(doc), encoding="utf-8")
    obs = observation_result_from_flow_recording_dir(rec)
    assert obs["page_context"]["goal_reached"] is True
    assert obs["page_context"]["url"] == "https://example.com/start"
    assert len(obs["flow_steps"]) == 2
    assert len(obs["ui_elements"]) == 2
    assert obs["page_context"]["flow_recording_artifacts"]["replayed_from_disk"] is True


def test_persist_skips_when_disabled(tmp_path: Path):
    obs = {"flow_steps": [{"order": 1, "action": "click", "target": "x"}]}
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=tmp_path):
        out = persist_observation_flow_artifacts("wf", obs, enabled=False)
    assert out is None
    assert "flow_recording_artifacts" not in obs


def test_persist_requirements_result_writes_under_requirements_subdir(tmp_path: Path):
    rec = tmp_path / "20260326T120000Z_abc12345"
    rec.mkdir()
    obs = {
        "page_context": {
            "flow_recording_artifacts": {
                "directory": str(rec.resolve()),
                "directory_name": rec.name,
            },
        },
    }
    req_payload = {"scenarios": [{"id": "S1", "title": "Login"}], "coverage_metrics": {"x": 1}}
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.FLOW_RECORDINGS_ENABLED = True
        paths = persist_requirements_result_to_flow_recording(
            obs,
            req_payload,
            workflow_id="613bbc29-4bde-493d-bbcc-fa874fcaf69c",
        )
    assert paths is not None
    dest = Path(paths["requirements_result_file"])
    assert dest.exists()
    assert dest.parent.name == "requirements"
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["requirements_result"]["scenarios"][0]["id"] == "S1"
    assert obs["page_context"]["flow_recording_artifacts"]["requirements_result_file"] == str(dest.resolve())


def test_persist_requirements_result_skips_without_artifacts_dir():
    obs = {"page_context": {}}
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.FLOW_RECORDINGS_ENABLED = True
        out = persist_requirements_result_to_flow_recording(obs, {"scenarios": []}, workflow_id="w")
    assert out is None
