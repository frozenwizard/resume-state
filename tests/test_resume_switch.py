"""Tests for the Resume State switch."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant, State

from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.sensor import ResumeStatus
from custom_components.resume_state.switches.resume_state_switch import (
    ResumeStateSwitch,
)


@pytest.fixture
def resume_switch(hass: HomeAssistant) -> ResumeStateSwitch:
    """Fixture for ResumeStateSwitch bound to the real hass instance."""
    switch = ResumeStateSwitch()
    switch.hass = hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["enabled"] = True
    hass.data[DOMAIN]["status"] = ResumeStatus.IDLE.value
    return switch


async def test_switch_initializes_on(
    hass: HomeAssistant, resume_switch: ResumeStateSwitch
) -> None:
    """Test the switch initializes correctly when there is no previous state."""
    with patch(
        "custom_components.resume_state.switches.resume_state_switch.RestoreEntity.async_get_last_state",
        return_value=None,
    ):
        await resume_switch.async_added_to_hass()

    assert resume_switch.is_on is True
    assert hass.data[DOMAIN]["enabled"] is True


async def test_switch_restores_off_state(
    hass: HomeAssistant, resume_switch: ResumeStateSwitch
) -> None:
    """Test the switch restores its off state and sets status to disabled."""
    last_state = State("switch.resume_home_state_enabled", "off")

    with patch(
        "custom_components.resume_state.switches.resume_state_switch.RestoreEntity.async_get_last_state",
        return_value=last_state,
    ):
        await resume_switch.async_added_to_hass()

    assert resume_switch.is_on is False
    assert hass.data[DOMAIN]["enabled"] is False
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value


async def test_switch_restores_on_state(
    hass: HomeAssistant, resume_switch: ResumeStateSwitch
) -> None:
    """Test the switch restores its on state."""
    last_state = State("switch.resume_home_state_enabled", "on")

    with patch(
        "custom_components.resume_state.switches.resume_state_switch.RestoreEntity.async_get_last_state",
        return_value=last_state,
    ):
        await resume_switch.async_added_to_hass()

    assert resume_switch.is_on is True
    assert hass.data[DOMAIN]["enabled"] is True


async def test_switch_turn_on(
    hass: HomeAssistant, resume_switch: ResumeStateSwitch
) -> None:
    """Test turning the switch on."""
    hass.data[DOMAIN]["status"] = ResumeStatus.DISABLED.value
    with patch.object(resume_switch, "async_write_ha_state"):
        await resume_switch.async_turn_on()
    assert resume_switch.is_on is True
    assert hass.data[DOMAIN]["enabled"] is True
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_switch_turn_off(
    hass: HomeAssistant, resume_switch: ResumeStateSwitch
) -> None:
    """Test turning the switch off."""
    with patch.object(resume_switch, "async_write_ha_state"):
        await resume_switch.async_turn_off()
    assert resume_switch.is_on is False
    assert hass.data[DOMAIN]["enabled"] is False
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value
