"""
API v2: Crawl-and-Save Test Endpoint

POST /api/v2/crawl-and-save-test

Uses the ObservationAgent (browser-use) to crawl a purchase/subscription flow up to a
configurable stop page, converts the recorded flow_steps into human-readable test case
steps, appends caller-provided tail_steps (hardcoded steps for the post-stop portion),
and saves the combined result as a test case in the database.

This avoids browser-use failing on complex payment/SIM-settings pages — the fragile
end-of-flow is expressed as explicit tail_steps while the navigational run-up is captured
automatically.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy.orm import Session

from app.schemas.test_case import TestCaseCreate
from app.models.test_case import TestType, Priority, TestStatus
from app.crud.test_case import create_test_case
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state, update_state, get_state

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CrawlAndSaveTestRequest(BaseModel):
    """
    Request body for the crawl-and-save-test endpoint.

    The agent will navigate the purchase flow via browser-use, recording every
    click/input/navigate action.  When ``stop_at_page_hint`` is matched against the
    current page title or URL the crawl is cancelled and partial history is used.
    The resulting steps are prepended to ``tail_steps`` and saved as a test case.
    """
    url: HttpUrl = Field(..., description="Start URL to begin crawling from")
    user_instruction: str = Field(
        ...,
        description=(
            "Instruction for browser-use, e.g. "
            "'Login and navigate the purchase flow for a SIM activation plan up to the SIM Card Setting page'"
        ),
    )
    stop_at_page_hint: Optional[str] = Field(
        None,
        description=(
            "Substring to match against page title/URL to stop crawling early "
            "(e.g. 'SIM Card Setting' or 'sim-setting'). "
            "When matched the crawl stops immediately and tail_steps take over."
        ),
    )
    tail_steps: List[str] = Field(
        default_factory=list,
        description=(
            "Hardcoded step strings to append after the crawled steps. "
            "These cover the portion of the flow that browser-use should NOT execute "
            "(e.g. SIM card settings, address, payment, signature)."
        ),
    )
    test_title: str = Field(..., description="Title for the saved test case")
    test_description: str = Field(..., description="Description for the saved test case")
    test_type: str = Field(default="e2e", description="Test type: e2e | integration | unit")
    priority: str = Field(default="high", description="Priority: high | medium | low")
    login_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="{'email': '...', 'password': '...'} or {'username': '...', 'password': '...'}"
    )
    http_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="HTTP Basic auth for preprod/UAT: {'username': '...', 'password': '...'}"
    )
    available_file_paths: Optional[List[str]] = Field(
        None,
        description="Local file paths for upload steps (e.g. HKID image)"
    )
    max_browser_steps: Optional[int] = Field(
        None, ge=1, le=500,
        description="Override max browser-use steps (default 120)"
    )
    max_flow_timeout_seconds: Optional[int] = Field(
        None, ge=60, le=7200,
        description="Override wall-clock timeout in seconds (default 1200)"
    )
    tags: Optional[List[str]] = Field(None, description="Optional tags for the test case")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            "user_instruction": (
                "Login with email hthkqa.as+94@gmail.com / DEE57vTo!, navigate to "
                "the 4.5G Greater China Pro Monthly Plan and complete the subscription "
                "flow up to (but not including) the SIM Card Setting page."
            ),
            "stop_at_page_hint": "SIM Card Setting",
            "tail_steps": [
                "Step 18: wait",
                "Step 19: Upload the HKID document from /home/dt-qa/Pictures/HKID-Sample-Blank-7.jpeg",
                "Step 20: wait",
                "Step 28: Input contact number '90457537'",
                "Step 29: Click the next button",
            ],
            "test_title": "Subscribe to 4.5G Greater China Plan (crawled + tail)",
            "test_description": "E2E purchase flow auto-crawled up to SIM Card Setting, then hardcoded tail steps",
            "login_credentials": {"email": "hthkqa.as+94@gmail.com", "password": "DEE57vTo!"},
        }
    })


class CrawlAndSaveTestResponse(BaseModel):
    """Immediate response — background job started."""
    workflow_id: str
    status: str
    message: str
    started_at: datetime


# ---------------------------------------------------------------------------
# Helper: convert flow_steps → human-readable test step strings
# ---------------------------------------------------------------------------

import re as _re

def _parse_extracted_content(content: str, login_credentials: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Parse browser-use extracted_content strings into clean plain-English descriptions.

    Browser-use produces strings like:
      "🖱️Clicked div \"Login\""
      "⌨️Typed \"pmo@example.com\" into element with index 42 (content: ...)"
      "🖱️Clicked button \"Subscribe Now\""
      "Navigated to https://..."
      "Scrolled down by 500 pixels"
    """
    if not content:
        return None

    # Strip leading emoji / special chars (code points outside normal BMP, and common icon ranges)
    c = _re.sub(r'^[\U00010000-\U0010ffff\u2600-\u27FF\uFE00-\uFE0F\u2700-\u27BF\u{1F300}-\u{1FFFF}]+\s*', '', content, flags=_re.UNICODE)
    c = c.strip()

    # Pattern: Clicked {tag} "{label}" or Clicked {tag} '{label}'
    m = _re.match(r'Clicked\s+\S+\s+["\u201c\u2018](.+?)["\u201d\u2019]', c, _re.IGNORECASE)
    if m:
        label = m.group(1).strip()
        if label and label.lower() not in ('div', 'span', 'button', 'a', 'input', 'li'):
            return f"Click the '{label}' button"

    # Pattern: Typed "{value}" into element...
    m = _re.match(r'Typed\s+["\u201c\u2018](.+?)["\u201d\u2019]\s+into', c, _re.IGNORECASE)
    if m:
        value = m.group(1).strip()
        # Mask sensitive values if they match login credentials
        if login_credentials:
            pw = login_credentials.get("password", "")
            if pw and value == pw:
                value = value  # keep as-is for test steps
        return f"Input '{value}' in the input field"

    # Pattern: Navigated to {url}
    m = _re.match(r'Navigated\s+to\s+(\S+)', c, _re.IGNORECASE)
    if m:
        return f"Navigate to {m.group(1)} in a web browser"

    return None


def _flow_steps_to_test_steps(
    flow_steps: List[Dict[str, Any]],
    login_credentials: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Convert observation agent ``flow_steps`` dicts into plain-English step strings
    compatible with the existing test case format (like test case #1079).

    Prefers ``extracted_content`` from the browser-use action result (contains rich
    descriptions like "Clicked div 'Login'" or "Typed 'user@example.com' into...").
    Falls back to DOM-derived ``target`` when extracted_content is absent or generic.
    """
    if not flow_steps:
        return []

    email = ""
    password = ""
    if login_credentials:
        email = login_credentials.get("email") or login_credentials.get("username", "")
        password = login_credentials.get("password", "")

    steps: List[str] = []
    step_num = 1

    for fs in flow_steps:
        action = (fs.get("action") or "").lower()
        target = (fs.get("target") or "").strip()
        page_url = fs.get("page_url", "")
        input_type = (fs.get("input_type") or "").lower()
        elem_type = (fs.get("element_type") or "").lower()
        extracted_content = fs.get("extracted_content", "")

        # --- Primary: try to use extracted_content (richer description from browser-use) ---
        if extracted_content:
            parsed = _parse_extracted_content(extracted_content, login_credentials)
            if parsed:
                steps.append(f"Step {step_num}: {parsed}")
                step_num += 1
                continue

        # --- Fallback: derive from DOM action / target fields ---
        if action == "navigate":
            steps.append(f"Step {step_num}: Navigate to {page_url or target} in a web browser")

        elif action == "input":
            if input_type == "email" or (target and "email" in target.lower()):
                value = email if email else "[EMAIL]"
                field_label = "email address"
            elif input_type == "password" or (target and "password" in target.lower()):
                value = password if password else "[PASSWORD]"
                field_label = "password"
            else:
                value = f"[{target.upper() if target and target not in ('input', 'div', 'span') else 'VALUE'}]"
                field_label = target if target and target not in ('input', 'div', 'span') else "input"
            steps.append(f"Step {step_num}: Input '{value}' in the {field_label} field")

        elif action == "click":
            # Skip meaningless generic targets
            if not target or target.lower() in ('div', 'span', 'li', ''):
                step_num += 1
                continue
            if elem_type == "input" and input_type == "checkbox":
                steps.append(f"Step {step_num}: Check the '{target}' checkbox")
            elif elem_type == "a":
                steps.append(f"Step {step_num}: Click the '{target}' link")
            else:
                steps.append(f"Step {step_num}: Click the '{target}' button")

        else:
            if target and target.lower() not in ('div', 'span', 'li'):
                steps.append(f"Step {step_num}: {action.capitalize()} '{target}'")
            else:
                step_num += 1
                continue

        step_num += 1

    return steps


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

async def _run_crawl_and_save(
    workflow_id: str,
    request_dict: Dict[str, Any],
    user_id: int,
    orchestration_service: OrchestrationService,
    progress_tracker: Optional[ProgressTracker],
) -> None:
    """Background coroutine: observe → convert → save test case."""
    from agents.base_agent import TaskContext
    from app.services.workflow_store import update_state
    from app.services.orchestration_service import http_credentials_for_url

    started_at = datetime.now(timezone.utc)
    pt = progress_tracker

    def _emit(evt: str, data: dict):
        if pt:
            asyncio.create_task(pt.emit(workflow_id, evt, data))
        update_state(workflow_id, current_agent=data.get("agent"), status="running")

    try:
        # ---- 1. Build ObservationAgent task payload ----
        url = str(request_dict["url"])
        user_instruction = request_dict.get("user_instruction", "")
        stop_at_page_hint = request_dict.get("stop_at_page_hint") or ""
        tail_steps: List[str] = request_dict.get("tail_steps") or []
        login_credentials = request_dict.get("login_credentials") or {}
        http_credentials = request_dict.get("http_credentials") or {}
        available_file_paths = request_dict.get("available_file_paths")
        max_browser_steps = request_dict.get("max_browser_steps")
        max_flow_timeout_seconds = request_dict.get("max_flow_timeout_seconds")

        obs_payload: Dict[str, Any] = {
            "url": url,
            "user_instruction": user_instruction,
            "max_depth": 1,
        }
        if login_credentials:
            obs_payload["login_credentials"] = login_credentials
        _creds = http_credentials_for_url(url, http_credentials)
        if _creds:
            obs_payload["http_credentials"] = _creds
        if available_file_paths:
            obs_payload["available_file_paths"] = available_file_paths
        if stop_at_page_hint:
            obs_payload["stop_at_page_hint"] = stop_at_page_hint
        if max_browser_steps is not None:
            obs_payload["max_browser_steps"] = int(max_browser_steps)
        if max_flow_timeout_seconds is not None:
            obs_payload["max_flow_timeout_seconds"] = int(max_flow_timeout_seconds)

        # ---- 2. Run observation ----
        _emit("agent_started", {"agent": "observation", "timestamp": started_at.isoformat()})
        update_state(workflow_id, status="running", current_agent="observation")

        obs_agent, _, _, _ = orchestration_service._create_agents(
            db=None,
            per_agent_llm_config=orchestration_service._resolve_per_agent_llm_config(user_id=user_id),
        )
        obs_task = TaskContext(
            conversation_id=workflow_id,
            task_id=f"{workflow_id}-obs",
            task_type="ui_element_extraction",
            payload=obs_payload,
            priority=8,
        )
        observation_result = await obs_agent.execute_task(obs_task)

        if not observation_result.success:
            raise RuntimeError(observation_result.error or "Observation failed")

        obs_data = observation_result.result
        flow_steps: List[Dict[str, Any]] = obs_data.get("flow_steps") or []

        _emit("agent_completed", {
            "agent": "observation",
            "pages_crawled": obs_data.get("pages_crawled", 0),
            "flow_steps_captured": len(flow_steps),
            "stop_triggered": bool(stop_at_page_hint),
        })

        # ---- 3. Convert flow_steps → test step strings ----
        crawled_step_strings = _flow_steps_to_test_steps(flow_steps, login_credentials)

        # ---- 4. Combine crawled + tail steps ----
        all_steps = crawled_step_strings + tail_steps
        if not all_steps:
            raise RuntimeError("No steps were captured from crawl and no tail_steps provided")

        # ---- 5. Save test case to DB ----
        test_title = request_dict.get("test_title", f"Auto-crawled test ({datetime.now().strftime('%Y%m%d%H%M')})")
        test_description = request_dict.get("test_description", user_instruction)
        test_type_str = request_dict.get("test_type", "e2e").lower()
        priority_str = request_dict.get("priority", "high").lower()
        tags: List[str] = request_dict.get("tags") or []

        # Map strings to enum values
        _type_map = {"e2e": TestType.E2E, "integration": TestType.INTEGRATION, "unit": TestType.UNIT}
        _priority_map = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}
        test_type_enum = _type_map.get(test_type_str, TestType.E2E)
        priority_enum = _priority_map.get(priority_str, Priority.HIGH)

        tc_create = TestCaseCreate(
            title=test_title,
            description=test_description,
            test_type=test_type_enum,
            priority=priority_enum,
            status=TestStatus.PENDING,
            steps=all_steps,
            expected_result="Test completes successfully through all steps",
            preconditions=(
                f"User is logged in with credentials from login_credentials. "
                f"Browser-use crawled the flow up to '{stop_at_page_hint}' stop point."
            ) if stop_at_page_hint else "User has valid login credentials.",
            tags=tags if tags else None,
            test_metadata={
                "source": "crawl_and_save",
                "workflow_id": workflow_id,
                "start_url": url,
                "stop_at_page_hint": stop_at_page_hint,
                "crawled_steps_count": len(crawled_step_strings),
                "tail_steps_count": len(tail_steps),
                "pages_crawled": obs_data.get("pages_crawled", 0),
            },
        )

        # Need a DB session — create one inline
        from app.db.session import SessionLocal
        db: Session = SessionLocal()
        try:
            saved_tc = create_test_case(db, tc_create, user_id)
            test_case_id = saved_tc.id
        finally:
            db.close()

        logger.info(
            "CrawlAndSave workflow %s: saved test case #%s (%d steps = %d crawled + %d tail)",
            workflow_id,
            test_case_id,
            len(all_steps),
            len(crawled_step_strings),
            len(tail_steps),
        )

        # ---- 6. Store final result in workflow store ----
        set_state(workflow_id, {
            "workflow_id": workflow_id,
            "status": "completed",
            "current_agent": None,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": "crawl_and_save",
            "result": {
                "test_case_id": test_case_id,
                "test_title": test_title,
                "total_steps": len(all_steps),
                "crawled_steps_count": len(crawled_step_strings),
                "tail_steps_count": len(tail_steps),
                "pages_crawled": obs_data.get("pages_crawled", 0),
                "stop_triggered": bool(stop_at_page_hint),
                "steps_preview": all_steps[:10],
            },
        })
        _emit("workflow_completed", {
            "test_case_id": test_case_id,
            "total_steps": len(all_steps),
        })

    except Exception as exc:
        logger.exception("CrawlAndSave workflow %s failed: %s", workflow_id, exc)
        set_state(workflow_id, {
            "workflow_id": workflow_id,
            "status": "failed",
            "current_agent": None,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": "crawl_and_save",
            "error": str(exc),
        })


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/crawl-and-save-test",
    response_model=CrawlAndSaveTestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Crawl purchase flow and save as test case",
    description="""
Crawls a web application flow using the ObservationAgent (browser-use) and automatically
converts the recorded steps into a saved test case.

**Key feature:** Pass ``stop_at_page_hint`` to stop the crawl exactly at a fragile page
(e.g. SIM Card Setting, payment page) and provide ``tail_steps`` with hardcoded steps for
the remainder. This prevents browser-use from making mistakes on complex forms.

The resulting test case combines the crawled navigational steps with your hardcoded tail
steps and can be executed immediately via the 3-tier testing system (Playwright / Stagehand).

**Returns:** ``workflow_id`` immediately (runs in background).  
**Poll status:** ``GET /api/v2/workflows/{workflow_id}``  
**Results (with test_case_id):** ``GET /api/v2/workflows/{workflow_id}/results``
""",
)
async def crawl_and_save_test(
    request: CrawlAndSaveTestRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> CrawlAndSaveTestResponse:
    """Start crawl-and-save workflow in background; return workflow_id immediately."""
    workflow_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    request_dict: Dict[str, Any] = {
        "url": str(request.url),
        "user_instruction": request.user_instruction,
        "stop_at_page_hint": request.stop_at_page_hint,
        "tail_steps": request.tail_steps,
        "test_title": request.test_title,
        "test_description": request.test_description,
        "test_type": request.test_type,
        "priority": request.priority,
        "login_credentials": request.login_credentials,
        "http_credentials": request.http_credentials,
        "available_file_paths": request.available_file_paths,
        "max_browser_steps": request.max_browser_steps,
        "max_flow_timeout_seconds": request.max_flow_timeout_seconds,
        "tags": request.tags,
    }

    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": started_at.isoformat(),
        "error": None,
        "workflow_type": "crawl_and_save",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await _run_crawl_and_save(
                workflow_id=workflow_id,
                request_dict=request_dict,
                user_id=1,  # default admin user, no auth required (same as generate-tests)
                orchestration_service=orchestration_service,
                progress_tracker=progress_tracker,
            )
        except Exception as e:
            logger.exception("Background crawl-and-save %s failed: %s", workflow_id, e)

    background_tasks.add_task(run_in_background)

    return CrawlAndSaveTestResponse(
        workflow_id=workflow_id,
        status="pending",
        message=(
            f"Crawl-and-save workflow started. "
            f"{'Will stop at page: ' + request.stop_at_page_hint if request.stop_at_page_hint else 'No stop page set — will run to completion or max_browser_steps.'} "
            f"Poll GET /api/v2/workflows/{workflow_id} for status."
        ),
        started_at=started_at,
    )
