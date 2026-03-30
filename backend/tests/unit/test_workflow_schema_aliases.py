"""Pydantic accepts camelCase aliases for some workflow API fields."""
from app.schemas.workflow import GenerateTestsRequest, RequirementsRequest


def test_generate_tests_accepts_flowRecordingPath_alias():
    m = GenerateTestsRequest.model_validate(
        {
            "url": "https://example.com/path",
            "flowRecordingPath": "613bbc29-4bde-493d-bbcc-fa874fcaf69c",
        }
    )
    assert m.flow_recording_path == "613bbc29-4bde-493d-bbcc-fa874fcaf69c"


def test_generate_tests_accepts_snake_case_flow_recording_path():
    m = GenerateTestsRequest.model_validate(
        {
            "url": "https://example.com/path",
            "flow_recording_path": "replay_dir",
        }
    )
    assert m.flow_recording_path == "replay_dir"


def test_requirements_accepts_flowRecordingPath_alias():
    m = RequirementsRequest.model_validate(
        {
            "flowRecordingPath": "some_recording",
            "user_instruction": "test",
        }
    )
    assert m.flow_recording_path == "some_recording"


def test_generate_tests_accepts_recordedPathOnly_alias():
    m = GenerateTestsRequest.model_validate(
        {"url": "https://example.com", "recordedPathOnly": True}
    )
    assert m.recorded_path_only is True
