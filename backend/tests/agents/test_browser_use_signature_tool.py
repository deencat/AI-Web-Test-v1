"""Ensure custom browser-use signature tool registers alongside default actions."""

import pytest

pytest.importorskip("browser_use")


def test_draw_signature_pad_registers_on_tools():
    from browser_use.tools.service import Tools

    from agents.browser_use_signature_tool import register_draw_signature_pad_tool

    tools = Tools()
    actions = tools.registry.registry.actions
    assert "draw_signature_pad" not in actions

    register_draw_signature_pad_tool(tools)

    assert "draw_signature_pad" in actions
    action = actions["draw_signature_pad"]
    assert action.name == "draw_signature_pad"
    assert action.param_model is not None
