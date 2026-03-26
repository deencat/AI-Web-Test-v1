"""Tests for on-disk flow recording after observation."""
import json
from pathlib import Path
from unittest.mock import patch

from app.utils.flow_recording_persistence import (
    build_playwright_step_ir,
    build_recording_document,
    persist_observation_flow_artifacts,
    persist_test_case_flow_manifests,
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


def test_persist_writes_files_and_mutates_obs(tmp_path: Path):
    wf = "test-wf-001"
    obs = {
        "flow_steps": [
            {"order": 1, "action": "click", "target": "Go", "page_url": "https://e.com", "locator": None},
        ],
        "start_url": "https://e.com",
        "page_context": {"url": "https://e.com", "goal_reached": False},
    }
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=tmp_path):
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
    assert obs["flow_recording_artifacts"]["directory"] == str((tmp_path / wf).resolve())
    assert obs["page_context"]["flow_recording_artifacts"]["workflow_id"] == wf

    mp = persist_test_case_flow_manifests(wf, [101, 102], obs, enabled=True)
    assert mp is not None and len(mp) == 2
    assert obs["flow_recording_artifacts"]["test_case_manifest_count"] == 2
    m0 = json.loads(Path(mp[0]).read_text(encoding="utf-8"))
    assert m0["test_case_id"] == 101
    assert m0["playwright_step_ir_file"] == str(ir_f.resolve())


def test_persist_skips_when_disabled(tmp_path: Path):
    obs = {"flow_steps": [{"order": 1, "action": "click", "target": "x"}]}
    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=tmp_path):
        out = persist_observation_flow_artifacts("wf", obs, enabled=False)
    assert out is None
    assert "flow_recording_artifacts" not in obs
