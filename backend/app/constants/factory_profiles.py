"""Display names for QA Factory specialist profiles (Agentic QA UI)."""

FACTORY_PROFILE_DISPLAY_NAMES: dict[str, str] = {
    "qa-orchestrator": "QA Orchestrator",
    "qa-journey-planner": "Journey Planner",
    "qa-test-gen": "Test Generator",
    "qa-dispatcher": "Dispatcher",
    "qa-reporter": "Reporter",
    "qa-change-detector": "Change Detector",
    "qa-healer": "Healer",
    "factory_bridge": "Factory Node",
    "hermes_bridge": "Factory Node",
    "system": "System",
}


def factory_profile_display_name(profile: str | None) -> str:
    if not profile:
        return "System"
    return FACTORY_PROFILE_DISPLAY_NAMES.get(profile, profile)
