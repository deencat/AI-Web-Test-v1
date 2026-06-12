"""Self-healing from execution feedback (HF-5 Loop D)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import execution_feedback as crud_feedback
from app.crud import heal_review as crud_heal
from app.crud import test_execution as crud_executions
from app.models.execution_settings import XPathCache as XPathCacheModel
from app.models.factory_job import FactoryJob
from app.models.test_case import TestCase
from app.models.test_execution import ExecutionResult, ExecutionStatus, TestExecution
from app.services.execution_queue import get_execution_queue
from app.services.factory_journey_service import _poll_workflow, _start_crawl
from app.services.factory_job_service import append_job_event
from app.services.scheduler_service import _infer_target_url
from app.services.xpath_cache_service import XPathCacheService

logger = logging.getLogger(__name__)

SELECTOR_FAILURE_TYPES = {
    "selector_not_found",
    "element_not_found",
    "xpath_stale",
    "locator_not_found",
    "no_such_element",
}


def classify_failure_strategy(feedback_items: List[Any]) -> str:
    """Return 'xpath' for selector issues, else 'flow' (recrawl)."""
    for fb in feedback_items:
        failure_type = (getattr(fb, "failure_type", None) or "").lower()
        error_message = (getattr(fb, "error_message", None) or "").lower()
        selector_type = (getattr(fb, "selector_type", None) or "").lower()

        if failure_type in SELECTOR_FAILURE_TYPES:
            return "xpath"
        if selector_type in ("xpath", "css", "selector"):
            return "xpath"
        for needle in ("selector", "element not found", "xpath", "locator", "no such element"):
            if needle in error_message:
                return "xpath"
    return "flow"


def _resolve_crawl_url(test_case: TestCase, execution: TestExecution, feedback_items: List[Any]) -> str:
    for fb in feedback_items:
        page_url = getattr(fb, "page_url", None)
        if page_url:
            return str(page_url)
    url = execution.base_url or _infer_target_url(test_case)
    if url:
        return url
    meta = test_case.test_metadata if isinstance(test_case.test_metadata, dict) else {}
    for key in ("url", "target_url", "start_url"):
        if meta.get(key):
            return str(meta[key])
    raise ValueError("Could not determine URL for heal recrawl")


def clear_xpath_cache_for_feedback(
    db: Session,
    feedback_items: List[Any],
) -> int:
    """Delete xpath cache entries tied to failure page/instruction."""
    deleted = 0
    svc = XPathCacheService(db)

    for fb in feedback_items:
        page_url = getattr(fb, "page_url", None)
        if not page_url:
            continue

        instruction = getattr(fb, "failed_selector", None) or ""
        if instruction:
            cache_key = svc.generate_cache_key(page_url, str(instruction))
            count = (
                db.query(XPathCacheModel)
                .filter(XPathCacheModel.cache_key == cache_key)
                .delete(synchronize_session=False)
            )
            deleted += count
        else:
            normalized = XPathCacheService.normalize_cacheable_url(page_url)
            rows = db.query(XPathCacheModel).filter(XPathCacheModel.page_url == page_url).all()
            if not rows and normalized != page_url:
                rows = db.query(XPathCacheModel).filter(XPathCacheModel.page_url == normalized).all()
            for row in rows:
                db.delete(row)
                deleted += 1

    if deleted:
        db.commit()
    return deleted


def _build_recrawl_body(
    test_case: TestCase,
    execution: TestExecution,
    feedback_items: List[Any],
) -> Dict[str, Any]:
    url = _resolve_crawl_url(test_case, execution, feedback_items)
    tags = list(test_case.tags or [])
    for tag in ("factory-healed", "regression"):
        if tag not in tags:
            tags.append(tag)

    primary_fb = feedback_items[0] if feedback_items else None
    hint = ""
    if primary_fb and getattr(primary_fb, "root_cause_analysis", None):
        hint = f" Prior failure context: {primary_fb.root_cause_analysis[:500]}"

    return {
        "url": url,
        "reference_test_id": test_case.id,
        "user_instruction": (
            f"Heal failed test '{test_case.title}'. Re-crawl the flow and fix broken steps.{hint}"
        ),
        "test_title": f"{test_case.title} (healed)",
        "test_description": test_case.description or f"Healed from execution #{execution.id}",
        "tags": tags,
        "priority": test_case.priority.value if hasattr(test_case.priority, "value") else "medium",
        "test_type": "e2e",
    }


def _queue_retry_execution(
    db: Session,
    execution: TestExecution,
    user_id: int,
) -> int:
    test_case = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
    if not test_case:
        raise ValueError(f"Test case {execution.test_case_id} not found")

    base_url = execution.base_url or _infer_target_url(test_case) or ""
    new_execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case.id,
        user_id=user_id,
        browser=execution.browser or "chromium",
        environment=execution.environment or "dev",
        base_url=base_url,
    )
    new_execution.triggered_by = "factory_heal_retry"
    new_execution.queued_at = datetime.utcnow()
    new_execution.priority = 3
    db.commit()

    get_execution_queue().add_to_queue(
        execution_id=new_execution.id,
        test_case_id=test_case.id,
        user_id=user_id,
        priority=new_execution.priority,
    )
    return new_execution.id


class _NoOpMessageQueue:
    async def publish(self, *args: Any, **kwargs: Any) -> None:
        return None


async def _run_learn_from_feedback(db: Session, test_case_id: int, execution_id: int) -> None:
    try:
        from agents.evolution_agent import EvolutionAgent

        mq = _NoOpMessageQueue()
        agent = EvolutionAgent(
            agent_id="factory_heal",
            agent_type="evolution",
            priority=5,
            message_queue=mq,
            config={"use_llm": False, "db": db},
        )
        await agent.learn_from_feedback(
            generation_id=f"heal-{execution_id}",
            execution_results={
                "test_case_ids": [test_case_id],
                "execution_summary": {"source": "factory_heal", "execution_id": execution_id},
                "failed_scenarios": [],
                "successful_scenarios": [],
            },
        )
    except Exception as exc:
        logger.warning("[FactoryHeal] learn_from_feedback skipped: %s", exc)


def heal_from_feedback(
    db: Session,
    execution_id: int,
    user_id: int,
    *,
    retry_execution: bool = True,
    max_attempts: Optional[int] = None,
) -> Dict[str, Any]:
    """Heal a single failed execution. Returns result dict for API/worker."""
    max_attempts = max_attempts or settings.FACTORY_HEAL_MAX_ATTEMPTS

    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise ValueError(f"Execution {execution_id} not found")

    if execution.status != ExecutionStatus.COMPLETED:
        raise ValueError(f"Execution {execution_id} is not completed (status={execution.status})")

    if execution.result not in (ExecutionResult.FAIL, ExecutionResult.ERROR):
        raise ValueError(f"Execution {execution_id} did not fail (result={execution.result})")

    test_case = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
    if not test_case:
        raise ValueError(f"Test case {execution.test_case_id} not found")

    attempt_row = crud_heal.get_heal_attempt(db, execution_id)
    if attempt_row and attempt_row.attempt_count >= max_attempts:
        review = crud_heal.create_heal_review_item(
            db,
            execution_id=execution_id,
            test_case_id=test_case.id,
            reason=attempt_row.last_error or f"Exceeded {max_attempts} heal attempts",
        )
        return {
            "execution_id": execution_id,
            "action": "escalated",
            "strategy": attempt_row.last_action or "unknown",
            "test_case_id": test_case.id,
            "attempt_count": attempt_row.attempt_count,
            "escalated": True,
            "heal_review_id": review.id,
            "details": {"message": "Already at max heal attempts"},
        }

    feedback_items = crud_feedback.get_feedback_by_execution(db, execution_id)
    strategy = classify_failure_strategy(feedback_items)
    details: Dict[str, Any] = {"strategy": strategy, "feedback_count": len(feedback_items)}

    try:
        if strategy == "xpath":
            cleared = clear_xpath_cache_for_feedback(db, feedback_items)
            new_execution_id = None
            if retry_execution:
                new_execution_id = _queue_retry_execution(db, execution, user_id)

            attempt = crud_heal.increment_heal_attempt(
                db,
                execution_id,
                action="clear_xpath_cache",
                test_case_id=test_case.id,
            )
            asyncio.run(_run_learn_from_feedback(db, test_case.id, execution_id))

            return {
                "execution_id": execution_id,
                "action": "clear_xpath_cache",
                "strategy": strategy,
                "test_case_id": test_case.id,
                "new_execution_id": new_execution_id,
                "cache_entries_cleared": cleared,
                "attempt_count": attempt.attempt_count,
                "escalated": False,
                "details": details,
            }

        body = _build_recrawl_body(test_case, execution, feedback_items)
        workflow_id = _start_crawl(body)
        result = _poll_workflow(workflow_id, timeout_seconds=1200)
        healed_test_case_id = int(result["test_case_ids"][0])

        attempt = crud_heal.increment_heal_attempt(
            db,
            execution_id,
            action="recrawl",
            test_case_id=healed_test_case_id,
        )
        asyncio.run(_run_learn_from_feedback(db, healed_test_case_id, execution_id))

        return {
            "execution_id": execution_id,
            "action": "recrawl",
            "strategy": strategy,
            "test_case_id": healed_test_case_id,
            "workflow_id": workflow_id,
            "attempt_count": attempt.attempt_count,
            "escalated": False,
            "details": {**details, "crawl_url": body["url"]},
        }

    except Exception as exc:
        attempt = crud_heal.increment_heal_attempt(
            db,
            execution_id,
            action=strategy,
            test_case_id=test_case.id,
            error=str(exc),
        )
        escalated = False
        heal_review_id = None
        if attempt.attempt_count >= max_attempts:
            review = crud_heal.create_heal_review_item(
                db,
                execution_id=execution_id,
                test_case_id=test_case.id,
                reason=str(exc),
            )
            escalated = True
            heal_review_id = review.id
        return {
            "execution_id": execution_id,
            "action": "failed",
            "strategy": strategy,
            "test_case_id": test_case.id,
            "attempt_count": attempt.attempt_count,
            "escalated": escalated,
            "heal_review_id": heal_review_id,
            "details": {**details, "error": str(exc)},
        }


def list_failed_execution_ids(
    db: Session,
    *,
    since: Optional[datetime] = None,
    limit: int = 20,
) -> List[int]:
    rows = crud_executions.get_executions(
        db,
        status=ExecutionStatus.COMPLETED,
        result=ExecutionResult.FAIL,
        since=since,
        limit=limit,
    )
    return [row.id for row in rows]


def scan_and_heal_failures(
    db: Session,
    job: FactoryJob,
    *,
    since: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> Tuple[int, int, int]:
    """Process failed executions for Loop D. Returns (processed, healed, escalated)."""
    params = job.params or {}
    limit = int(limit or params.get("limit", settings.FACTORY_HEAL_MAX_ITEMS))
    user_id = job.created_by_user_id or settings.FACTORY_SERVICE_USER_ID

    execution_ids = list_failed_execution_ids(db, since=since, limit=limit)
    append_job_event(
        db,
        job.id,
        event_type="heal_scan_start",
        profile="qa-healer",
        message=f"Scanning {len(execution_ids)} failed execution(s)",
        payload_summary={"count": len(execution_ids), "since": since.isoformat() if since else None},
    )

    healed = 0
    escalated = 0
    for execution_id in execution_ids:
        attempt = crud_heal.get_heal_attempt(db, execution_id)
        if attempt and attempt.attempt_count >= settings.FACTORY_HEAL_MAX_ATTEMPTS:
            continue

        try:
            result = heal_from_feedback(db, execution_id, user_id)
            if result.get("action") == "failed":
                append_job_event(
                    db,
                    job.id,
                    event_type="heal_failed",
                    profile="qa-healer",
                    message=f"Execution {execution_id}: {result.get('details', {}).get('error')}",
                    payload_summary=result,
                )
                if result.get("escalated"):
                    escalated += 1
                continue
            if result.get("escalated"):
                escalated += 1
                append_job_event(
                    db,
                    job.id,
                    event_type="heal_escalated",
                    profile="qa-healer",
                    message=f"Execution {execution_id} escalated to heal review",
                    payload_summary=result,
                )
            else:
                healed += 1
                append_job_event(
                    db,
                    job.id,
                    event_type="heal_applied",
                    profile="qa-healer",
                    message=f"Healed execution {execution_id} via {result.get('action')}",
                    payload_summary=result,
                )
        except Exception as exc:
            logger.exception("[FactoryHeal] unexpected error for execution %s", execution_id)
            append_job_event(
                db,
                job.id,
                event_type="heal_failed",
                profile="qa-healer",
                message=f"Execution {execution_id}: {exc}",
                payload_summary={"execution_id": execution_id, "error": str(exc)},
            )

    append_job_event(
        db,
        job.id,
        event_type="heal_scan_complete",
        profile="qa-healer",
        message=f"Heal scan done: {healed} healed, {escalated} escalated",
        payload_summary={
            "processed": len(execution_ids),
            "healed": healed,
            "escalated": escalated,
        },
    )
    return len(execution_ids), healed, escalated
