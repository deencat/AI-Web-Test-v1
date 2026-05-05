"""
Step Module Resolver — Sprint 10.11.

Expands @module:name(param=value) references to concrete step lists
before the 3-tier execution service dispatches steps.

Syntax:
  @module:login_three_hk()
  @module:login_flow(username=admin@test.com,password=secret)
  @module:checkout_flow        (no parens shorthand)
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

# Regex: @module:<name> optionally followed by (<params>)
_MODULE_REF_RE = re.compile(
    r"^@module:(?P<name>[a-zA-Z0-9_\-]+)(?:\((?P<params>[^)]*)\))?$",
    re.IGNORECASE,
)


def is_module_ref(step: str) -> bool:
    """Return True if *step* is a @module: reference."""
    if not isinstance(step, str):
        return False
    return bool(_MODULE_REF_RE.match(step.strip()))


def parse_module_ref(step: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    Parse a @module: reference into (name, params_dict).

    Returns None if the step is not a @module: reference.
    """
    if not isinstance(step, str):
        return None
    m = _MODULE_REF_RE.match(step.strip())
    if not m:
        return None

    name = m.group("name")
    raw_params = m.group("params") or ""
    params: Dict[str, str] = {}

    if raw_params.strip():
        for pair in raw_params.split(","):
            pair = pair.strip()
            if "=" in pair:
                key, _, val = pair.partition("=")
                params[key.strip()] = val.strip()

    return name, params


def _substitute_params(step_text: str, params: Dict[str, str]) -> str:
    """Replace {param_name} placeholders in *step_text* with provided values."""
    result = step_text
    for key, value in params.items():
        result = result.replace(f"{{{key}}}", value)
    return result


def resolve_steps(
    raw_steps: List[Any],
    db: Session,
    user_id: int,
) -> List[Any]:
    """
    Expand @module: references in *raw_steps* to concrete step lists.

    Steps without @module: references pass through unchanged.
    Missing or invalid module references produce an error step entry
    instead of raising an exception — this prevents execution crashes.

    Args:
        raw_steps: Original list of step strings or step dicts.
        db: SQLAlchemy database session.
        user_id: ID of the owning user (scope guard).

    Returns:
        Flat list of concrete steps ready for 3-tier dispatch.
    """
    from app.models.step_library_module import StepLibraryModule

    resolved: List[Any] = []

    for step in raw_steps:
        if not isinstance(step, str) or not is_module_ref(step):
            resolved.append(step)
            continue

        parsed = parse_module_ref(step)
        if parsed is None:
            resolved.append(step)
            continue

        module_name, params = parsed

        module = (
            db.query(StepLibraryModule)
            .filter(
                StepLibraryModule.name == module_name,
                StepLibraryModule.user_id == user_id,
            )
            .first()
        )

        if module is None:
            resolved.append(
                f"[ERROR] Step Library module '{module_name}' not found. "
                "Please create it in the Step Library before running this test."
            )
            continue

        # Expand each module step, substituting parameters
        for module_step in (module.steps or []):
            if isinstance(module_step, str) and params:
                resolved.append(_substitute_params(module_step, params))
            else:
                resolved.append(module_step)

    return resolved
