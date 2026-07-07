"""Tests for the Resume State button."""

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.components.input_boolean import DOMAIN as INPUT_BOOLEAN_DOMAIN
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.resume_state.button import ResumeStateButton
from custom_components.resume_state.config import CONF_ENTITIES, CONF_THROTTLE
from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.sensor import ResumeStatus, ResumeStatusSensor

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def resume_button(hass: HomeAssistant) -> ResumeStateButton:
    """Fixture for ResumeStateButton bound to the real hass instance."""
    button = ResumeStateButton()
    button.hass = hass
    return button


def _mock_recorder(historical_states: dict) -> MagicMock:
    """Build a recorder mock whose executor job returns historical_states."""
    recorder = MagicMock()
    recorder.async_add_executor_job = AsyncMock(return_value=historical_states)
    return recorder


async def test_resume_light_off(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a light to the 'off' state."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_resume_light_on_with_brightness(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a light to 'on' with brightness."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    historical_states = {entity_id: [State(entity_id, "on", {"brightness": 200})]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id, "brightness": 200}


async def test_resume_skip_if_matches(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test that we skip resuming if the state already matches."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on", {"brightness": 100})
    turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "on", {"brightness": 100})]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not turn_on
    assert not turn_off


async def test_resume_color_temp_light_sends_only_color_temp(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """
    Restore a color-temp light with color_temp_kelvin only, not rgb_color.

    Home Assistant exposes a derived ``rgb_color`` alongside
    ``color_temp_kelvin`` while in color_temp mode; sending both to
    ``light.turn_on`` violates its exclusive color group and fails the resume.
    """
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    historical_states = {
        entity_id: [
            State(
                entity_id,
                "on",
                {
                    "color_mode": "color_temp",
                    "color_temp_kelvin": 3000,
                    # The derived representation HA also reports while in
                    # color_temp mode — must NOT be replayed.
                    "rgb_color": (255, 166, 87),
                    "brightness": 180,
                },
            )
        ]
    }

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": entity_id,
        "brightness": 180,
        "color_temp_kelvin": 3000,
    }
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_skip_if_matches_rgb(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """
    Skip an rgb light already in the target color despite list/tuple types.

    The recorder yields ``rgb_color`` as a tuple while the live state holds a
    list (or vice versa); the comparison must normalize before deciding to skip.
    """
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    # Live state stores rgb_color as a list...
    hass.states.async_set(
        entity_id,
        "on",
        {"color_mode": "rgb", "rgb_color": [255, 0, 0], "brightness": 100},
    )
    turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    # ...while the recorded historical state holds the equivalent tuple.
    historical_states = {
        entity_id: [
            State(
                entity_id,
                "on",
                {"color_mode": "rgb", "rgb_color": (255, 0, 0), "brightness": 100},
            )
        ]
    }

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not turn_on
    assert not turn_off


async def test_resume_fan_off(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a fan to the 'off' state."""
    entity_id = "fan.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, FAN_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_resume_fan_on_with_percentage(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a fan to 'on' with a percentage."""
    entity_id = "fan.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, FAN_DOMAIN, "turn_on")
    historical_states = {
        entity_id: [State(entity_id, "on", {"percentage": 50, "preset_mode": None})]
    }

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id, "percentage": 50}


async def test_resume_fan_preset_mode_sends_only_preset(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """
    Restore a fan in a preset mode with preset_mode only, not percentage.

    A fan running in a preset mode still reports a ``percentage`` alongside
    it; how ``fan.turn_on`` reconciles both at once is integration-defined,
    so only the preset must be replayed.
    """
    entity_id = "fan.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, FAN_DOMAIN, "turn_on")
    historical_states = {
        entity_id: [State(entity_id, "on", {"percentage": 33, "preset_mode": "auto"})]
    }

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id, "preset_mode": "auto"}
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_fan_skip_if_matches(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test that we skip resuming a fan if the state already matches."""
    entity_id = "fan.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on", {"percentage": 50})
    turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, FAN_DOMAIN, "turn_off")
    historical_states = {
        entity_id: [State(entity_id, "on", {"percentage": 50, "preset_mode": None})]
    }

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not turn_on
    assert not turn_off


async def test_resume_switch_on(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a switch to the 'on' state."""
    entity_id = "switch.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, SWITCH_DOMAIN, "turn_on")
    historical_states = {entity_id: [State(entity_id, "on")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_switch_off(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a switch to the 'off' state."""
    entity_id = "switch.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, SWITCH_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}


async def test_resume_switch_skip_if_matches(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test that we skip resuming a switch if the state already matches."""
    entity_id = "switch.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    turn_on = async_mock_service(hass, SWITCH_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, SWITCH_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "on")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not turn_on
    assert not turn_off


async def test_resume_input_boolean_on(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming an input boolean to the 'on' state."""
    entity_id = "input_boolean.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "off")
    calls = async_mock_service(hass, INPUT_BOOLEAN_DOMAIN, "turn_on")
    historical_states = {entity_id: [State(entity_id, "on")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}


async def test_resume_input_boolean_off(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming an input boolean to the 'off' state."""
    entity_id = "input_boolean.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, INPUT_BOOLEAN_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}


async def test_resume_select_option(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a select to its previously selected option."""
    entity_id = "select.test"
    resume_at = dt_util.utcnow()
    options = ["cool", "heat", "off"]

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "cool", {"options": options})
    calls = async_mock_service(hass, SELECT_DOMAIN, "select_option")
    historical_states = {entity_id: [State(entity_id, "heat", {"options": options})]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id, "option": "heat"}
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_resume_input_select_option(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming an input select to its previously selected option."""
    entity_id = "input_select.test"
    resume_at = dt_util.utcnow()
    options = ["morning", "day", "night"]

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "day", {"options": options})
    calls = async_mock_service(hass, INPUT_SELECT_DOMAIN, "select_option")
    historical_states = {entity_id: [State(entity_id, "night", {"options": options})]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id, "option": "night"}


async def test_resume_select_skip_if_matches(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test that we skip resuming a select if the option already matches."""
    entity_id = "select.test"
    resume_at = dt_util.utcnow()
    options = ["cool", "heat", "off"]

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "heat", {"options": options})
    calls = async_mock_service(hass, SELECT_DOMAIN, "select_option")
    historical_states = {entity_id: [State(entity_id, "heat", {"options": options})]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not calls


async def test_resume_select_skip_if_option_unavailable(
    hass: HomeAssistant,
    resume_button: ResumeStateButton,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A recorded option no longer offered is skipped, not errored."""
    entity_id = "select.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    # "heat" was recorded but the entity no longer offers it: select_option
    # would raise, so we must skip gracefully instead of failing the batch.
    hass.states.async_set(entity_id, "cool", {"options": ["cool", "off"]})
    calls = async_mock_service(hass, SELECT_DOMAIN, "select_option")
    historical_states = {
        entity_id: [State(entity_id, "heat", {"options": ["cool", "heat", "off"]})]
    }

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not calls
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert "option heat is no longer available" in caplog.text


async def test_resume_select_skip_if_entity_reports_no_options(
    hass: HomeAssistant,
    resume_button: ResumeStateButton,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A select whose live entity is unavailable (no options) is skipped."""
    entity_id = "select.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    # The live entity is unavailable, so it exposes no `options` attribute and
    # cannot accept select_option; attempting it would raise and error the
    # batch, so the recorded option must be skipped instead.
    hass.states.async_set(entity_id, "unavailable")
    calls = async_mock_service(hass, SELECT_DOMAIN, "select_option")
    historical_states = {
        entity_id: [State(entity_id, "heat", {"options": ["cool", "heat", "off"]})]
    }

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not calls
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert "reports no options" in caplog.text


async def test_resume_select_skip_unavailable(
    hass: HomeAssistant,
    resume_button: ResumeStateButton,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that we skip resuming a select if historical state was unavailable."""
    entity_id = "select.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "cool", {"options": ["cool", "heat"]})
    calls = async_mock_service(hass, SELECT_DOMAIN, "select_option")
    historical_states = {entity_id: [State(entity_id, "unavailable")]}

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not calls
    assert "historical state was unavailable" in caplog.text


async def test_resume_skip_unavailable(
    hass: HomeAssistant,
    resume_button: ResumeStateButton,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that we skip resuming if historical state was unavailable."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    # Current state is "off" so that, absent the unavailable/unknown guard,
    # the historical "on"/"off" branches would otherwise fire a service call.
    hass.states.async_set(entity_id, "off")
    turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "unavailable")]}

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert not turn_on
    assert not turn_off
    # The guard must fire explicitly, not silently fall through.
    assert "historical state was unavailable" in caplog.text


async def test_resume_recorder_called_with_correct_args(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """
    Guard the recorder lookup: single entity_id, attributes preserved.

    This exercises the real argument passing (not a pre-baked return value),
    which is where the original light handling was broken.
    """
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }
    hass.states.async_set(entity_id, "off")
    async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    captured: dict = {}

    def fake_scdp(
        _hass: object,
        start: object,
        end: object,
        ent: object,
        *,
        no_attributes: bool,
        include_start_time_state: bool,
    ) -> dict:
        captured.update(
            start=start,
            end=end,
            ent=ent,
            no_attributes=no_attributes,
            include_start_time_state=include_start_time_state,
        )
        return {entity_id: [State(entity_id, "off")]}

    async def run_job(target: Callable[..., object], *args: object) -> object:
        return target(*args)

    recorder = MagicMock()
    recorder.async_add_executor_job = AsyncMock(side_effect=run_job)

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=recorder,
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            side_effect=fake_scdp,
        ),
    ):
        await resume_button.async_press()

    # A single entity id string must be passed, not the whole list.
    assert captured["ent"] == entity_id
    # Attributes must be preserved so brightness/color/effect can be restored.
    assert captured["no_attributes"] is False
    # The zero-width window relies on the start-time state being included.
    assert captured["include_start_time_state"] is True
    # The window must be exactly [resume_at, resume_at] (the snapshot instant).
    assert captured["start"] == resume_at
    assert captured["end"] == resume_at


async def test_resume_without_stored_state_errors(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Pressing resume with no stored timestamp sets ERRORED and does nothing."""
    hass.data[DOMAIN] = {
        CONF_ENTITIES: ["light.test"],
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
    }

    turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    await resume_button.async_press()

    assert not turn_on
    assert not turn_off
    assert hass.data[DOMAIN]["status"] == ResumeStatus.ERRORED.value


async def test_resume_status_sensor_updates(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """A successful resume ends in the IDLE status."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    status_sensor = ResumeStatusSensor()
    status_sensor.hass = hass

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        assert status_sensor.native_value == ResumeStatus.STORED.value

        await resume_button.async_press()

        assert status_sensor.native_value == ResumeStatus.IDLE.value


async def test_resume_status_sensor_updates_no_entities(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """With no resumable entities, the status resets to IDLE."""
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    status_sensor = ResumeStatusSensor()
    status_sensor.hass = hass

    assert status_sensor.native_value == ResumeStatus.STORED.value

    await resume_button.async_press()

    assert status_sensor.native_value == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_resume_no_history(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test when state_changes_during_period returns empty."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    historical_states: dict[str, list[State]] = {}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_unsupported_domain(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test when an unsupported domain is in the config."""
    entity_id = "climate.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    await resume_button.async_press()

    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_unsupported_entity_class(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test when build_resumable_entity returns None."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }
    historical_states = {entity_id: [State(entity_id, "on")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.build_resumable_entity",
            return_value=None,
        ),
    ):
        await resume_button.async_press()

    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_exception_during_restore(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test when resumable_entity.resume() raises an exception."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }
    historical_states = {entity_id: [State(entity_id, "on")]}

    mock_entity = AsyncMock()
    mock_entity.resume.side_effect = Exception("Test exception")

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.build_resumable_entity",
            return_value=mock_entity,
        ),
    ):
        await resume_button.async_press()

    assert hass.data[DOMAIN]["status"] == ResumeStatus.ERRORED.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_resume_light_unhandled_state(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test resuming a light that has an unhandled state (not on/off/unavailable)."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    historical_states = {entity_id: [State(entity_id, "foo")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        # Should complete without error and NOT call turn_on or turn_off
        await resume_button.async_press()

    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_button_disabled(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Test that pressing resume when disabled sets status to DISABLED and skips."""
    hass.data[DOMAIN] = {
        CONF_ENTITIES: ["light.test"],
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.STORED.value,
        "enabled": False,
    }

    turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    await resume_button.async_press()

    assert not turn_on
    assert not turn_off
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value


async def test_resume_throttle_waits_after_each_resume(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """The throttle sleeps once after every resumed entity, including the last."""
    entities = ["light.one", "light.two", "light.three"]
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: entities,
        CONF_THROTTLE: 250,  # milliseconds
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    for entity_id in entities:
        hass.states.async_set(entity_id, "on")
    async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")] for entity_id in entities}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep,
    ):
        await resume_button.async_press()

    # Three resumes -> three waits of 250ms expressed in seconds.
    assert mock_sleep.await_count == 3
    assert all(call.args == (0.25,) for call in mock_sleep.await_args_list)


async def test_resume_throttle_only_waits_after_resumed_entities(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """A skipped (history-less) entity is not followed by a throttle wait."""
    entities = ["light.one", "light.two"]
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: entities,
        CONF_THROTTLE: 250,
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
    }

    for entity_id in entities:
        hass.states.async_set(entity_id, "on")
    async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    # Only light.one has recorded history; light.two is skipped entirely.
    historical_states = {"light.one": [State("light.one", "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep,
    ):
        await resume_button.async_press()

    # Only light.one actually resumed, so exactly one wait.
    mock_sleep.assert_awaited_once_with(0.25)


async def test_resume_runs_as_integration_user(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Resume issues its light service calls under the integration user id."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow()
    user_id = "resume-state-user-id"

    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
        "user_id": user_id,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 1
    # The change is attributed to the integration's user in the logbook.
    assert calls[0].context.user_id == user_id


async def test_resume_uses_a_fresh_context_per_entity(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Each resumed entity gets its own context id, all under the same user."""
    entities = ["light.one", "light.two"]
    resume_at = dt_util.utcnow()
    user_id = "resume-state-user-id"

    hass.data[DOMAIN] = {
        CONF_ENTITIES: entities,
        "pressed_at": resume_at,
        "status": ResumeStatus.STORED.value,
        "user_id": user_id,
    }

    for entity_id in entities:
        hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")] for entity_id in entities}

    with (
        patch(
            "custom_components.resume_state.buttons.resume_state.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.buttons.resume_state.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await resume_button.async_press()

    assert len(calls) == 2
    # Same integration user, but an independent context per entity.
    assert {call.context.user_id for call in calls} == {user_id}
    assert calls[0].context.id != calls[1].context.id
