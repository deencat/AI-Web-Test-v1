"""
Persist Playwright-oriented flow recordings to disk after ObservationAgent completes.

Writes under ``backend/artifacts/flow_recordings/{workflow_id}/`` (gitignored via ``backend/artifacts/``):
  - ``playwright_flow_recording.json`` — schema v1 wrapper (steps + locators)
  - ``flow_steps.json`` — same steps array alone (easy diff / tooling)
  - ``playwright_step_ir.json`` — deterministic step IR (suggestions/xpath/attrs) for non-LLM codegen
  - ``by_test_case/test_case_{id}.json`` — per generated DB test case manifest pointing at the files above

Paths are attached to ``obs_data["flow_recording_artifacts"]`` for API / workflow results.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _backend_root() -> Path:
    """Directory containing ``app/`` (e.g. .../backend)."""
    return Path(__file__).resolve().parent.parent.parent


def flow_recordings_base_dir() -> Path:
    """
    Root directory for all flow recording folders.

    Override with env ``FLOW_RECORDINGS_DIR`` or settings ``FLOW_RECORDINGS_DIR``.
    """
    from app.core.config import settings

    env = os.environ.get("FLOW_RECORDINGS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    cfg = getattr(settings, "FLOW_RECORDINGS_DIR", None)
    if cfg:
        p = Path(str(cfg)).expanduser()
        if not p.is_absolute():
            p = _backend_root() / p
        return p.resolve()
    return (_backend_root() / "artifacts" / "flow_recordings").resolve()


def build_recording_document(obs_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the canonical ``playwright_flow_recording`` dict, building it if missing."""
    rec = obs_data.get("playwright_flow_recording")
    if isinstance(rec, dict) and rec.get("steps"):
        return rec

    steps: List[Dict[str, Any]] = obs_data.get("flow_steps") or []
    if not steps:
        return None

    from app.utils.playwright_flow_recording import wrap_playwright_flow_recording

    start_url = (obs_data.get("start_url") or "").strip()
    if not start_url:
        pc = obs_data.get("page_context") or {}
        start_url = str(pc.get("url") or "").strip()
    goal = bool((obs_data.get("page_context") or {}).get("goal_reached", False))
    if "goal_reached" in (obs_data.get("navigation_flow") or {}):
        goal = bool((obs_data.get("navigation_flow") or {}).get("goal_reached", goal))

    return wrap_playwright_flow_recording(
        start_url=start_url,
        steps=steps,
        goal_reached=goal,
    )


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_playwright_step_ir(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic intermediate representation for tooling / codegen without LLM.

    Mirrors each flow_step's action metadata plus locator strategies from ObservationAgent.
    """
    ordered = sorted(steps, key=lambda s: s.get("order", 0))
    ir_steps: List[Dict[str, Any]] = []
    for s in ordered:
        loc = s.get("locator")
        if not isinstance(loc, dict):
            loc = {}
        ir_steps.append(
            {
                "order": s.get("order"),
                "action": s.get("action"),
                "target": s.get("target"),
                "page_url": s.get("page_url"),
                "page_title": s.get("page_title"),
                "element_type": s.get("element_type"),
                "input_type": s.get("input_type"),
                "playwright_suggestions": loc.get("playwright_suggestions") or [],
                "xpath": loc.get("xpath"),
                "backend_node_id": loc.get("backend_node_id"),
                "frame_id": loc.get("frame_id"),
                "attributes": loc.get("attributes") or {},
            }
        )
    return {
        "schema_version": 1,
        "source": "observation-step-ir",
        "steps": ir_steps,
        "notes": (
            "Use playwright_suggestions[0] when stable; xpath/backend_node_id are fallbacks. "
            "Not a Playwright trace; map IR to TS with a small emitter."
        ),
    }


def persist_observation_flow_artifacts(
    workflow_id: str,
    obs_data: Dict[str, Any],
    *,
    enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Write flow recording JSON files for this workflow and attach metadata to ``obs_data``.

    Returns the ``flow_recording_artifacts`` dict, or None if skipped (disabled / no steps).
    """
    from app.core.config import settings

    if not enabled:
        return None
    if not getattr(settings, "FLOW_RECORDINGS_ENABLED", True):
        return None

    recording = build_recording_document(obs_data)
    if not recording:
        logger.debug("No flow_steps / recording to persist for workflow %s", workflow_id)
        return None

    steps = recording.get("steps") or obs_data.get("flow_steps") or []
    if not steps:
        return None

    safe_wf = "".join(c if c.isalnum() or c in "-_" else "_" for c in workflow_id)[:200]
    out_dir = flow_recordings_base_dir() / safe_wf
    main_file = out_dir / "playwright_flow_recording.json"
    steps_file = out_dir / "flow_steps.json"
    ir_file = out_dir / "playwright_step_ir.json"
    step_ir = build_playwright_step_ir(steps)

    try:
        _atomic_write_json(main_file, recording)
        _atomic_write_json(steps_file, steps)
        _atomic_write_json(ir_file, step_ir)
    except OSError as e:
        logger.exception("Failed to write flow recording for workflow %s: %s", workflow_id, e)
        obs_data["flow_recording_artifacts"] = {
            "error": str(e),
            "workflow_id": workflow_id,
        }
        return obs_data["flow_recording_artifacts"]

    artifacts: Dict[str, Any] = {
        "workflow_id": workflow_id,
        "directory": str(out_dir.resolve()),
        "playwright_flow_recording_file": str(main_file.resolve()),
        "flow_steps_file": str(steps_file.resolve()),
        "playwright_step_ir_file": str(ir_file.resolve()),
        "schema_version": recording.get("schema_version"),
    }
    obs_data["flow_recording_artifacts"] = artifacts
    # Mirror in page_context for consumers that only read page_context
    pc = obs_data.setdefault("page_context", {})
    if isinstance(pc, dict):
        pc["flow_recording_artifacts"] = dict(artifacts)
    logger.info(
        "Saved flow recording for workflow %s → %s",
        workflow_id,
        main_file,
    )
    return artifacts


def persist_test_case_flow_manifests(
    workflow_id: str,
    test_case_ids: Optional[List[Any]],
    obs_data: Dict[str, Any],
    *,
    enabled: bool = True,
) -> Optional[List[str]]:
    """
    After Evolution stores test cases, write one small JSON manifest per test_case_id under
    ``{flow_recordings}/{workflow_id}/by_test_case/`` linking to the shared recording files.

    Updates ``flow_recording_artifacts["test_case_manifest_files"]`` on ``obs_data`` (and page_context).
    """
    from app.core.config import settings

    if not enabled or not test_case_ids:
        return None
    if not getattr(settings, "FLOW_RECORDINGS_ENABLED", True):
        return None

    artifacts = obs_data.get("flow_recording_artifacts")
    if not isinstance(artifacts, dict) or artifacts.get("error"):
        logger.debug("No flow_recording_artifacts to attach test manifests for workflow %s", workflow_id)
        return None
    out_dir_str = artifacts.get("directory")
    if not out_dir_str:
        return None

    base = Path(out_dir_str) / "by_test_case"
    manifest_paths: List[str] = []
    try:
        base.mkdir(parents=True, exist_ok=True)
        for tid in test_case_ids:
            tid_str = str(tid).strip()
            safe_tid = "".join(c if c.isalnum() or c in "-_" else "_" for c in tid_str)[:120]
            manifest = {
                "schema_version": 1,
                "workflow_id": workflow_id,
                "test_case_id": tid,
                "playwright_flow_recording_file": artifacts.get("playwright_flow_recording_file"),
                "flow_steps_file": artifacts.get("flow_steps_file"),
                "playwright_step_ir_file": artifacts.get("playwright_step_ir_file"),
                "shared_recording_directory": out_dir_str,
            }
            dest = base / f"test_case_{safe_tid}.json"
            _atomic_write_json(dest, manifest)
            manifest_paths.append(str(dest.resolve()))
    except OSError as e:
        logger.exception("Failed test-case flow manifests for workflow %s: %s", workflow_id, e)
        artifacts["test_case_manifest_error"] = str(e)
        return None

    artifacts["test_case_manifest_files"] = manifest_paths
    artifacts["test_case_manifest_count"] = len(manifest_paths)
    pc = obs_data.get("page_context")
    if isinstance(pc, dict):
        # Keep page_context in sync with obs_data (shallow copy from first persist would be stale).
        pc["flow_recording_artifacts"] = dict(obs_data["flow_recording_artifacts"])
    logger.info(
        "Wrote %d test-case flow manifest(s) under %s",
        len(manifest_paths),
        base,
    )
    return manifest_paths
