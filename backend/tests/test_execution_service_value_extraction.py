"""
Unit Tests for value extraction in ExecutionService.

Focuses on dropdown/select phrasing without detailed_steps.
"""

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.execution_service import ExecutionService, ExecutionConfig


class TestExecutionServiceValueExtraction:
    """Test value extraction for dropdown/select instructions."""

    def setup_method(self):
        self.service = ExecutionService(ExecutionConfig())

    @pytest.mark.parametrize(
        "description,expected",
        [
            ("Select 'HONG KONG' from the Region dropdown.", "HONG KONG"),
            ("select 'EASTERN' from the District dropdown", "EASTERN"),
            ("Select HONG KONG from the Region dropdown", "HONG KONG"),
            ("Set Region dropdown value to HONG KONG", "HONG KONG"),
            ("Choose option 'EASTERN' in the District select", "EASTERN"),
            ("Select ‘HONG KONG’ from the Region dropdown.", "HONG KONG"),
            ("Select '01' as the expiry month dropdown", "01"),
            ("Select '39' as the expiry year dropdown", "39"),
        ],
    )
    def test_dropdown_value_extraction(self, description, expected):
        value = self.service._extract_value_from_description(description)
        assert value == expected

    @pytest.mark.parametrize(
        "description,expected",
        [
            ("Select 'HONG KONG' from the Region dropdown.", True),
            ("Set Region dropdown value to HONG KONG", True),
            ("Choose option EASTERN in the District select", True),
            ("Select the $288/month plan", False),
            ("Click the dropdown arrow", False),
        ],
    )
    def test_is_dropdown_instruction(self, description, expected):
        assert self.service._is_dropdown_instruction(description) is expected
