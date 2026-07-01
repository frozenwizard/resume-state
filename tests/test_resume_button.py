"""Tests for the Resume State button."""

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
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
    entity_id = "switch.test"
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


async def test_resume_throttles_between_entities(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """Throttle sleeps between consecutive resumes: N resumes -> N-1 waits."""
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

    # Three resumes -> two gaps, each waiting 250ms expressed in seconds.
    assert mock_sleep.await_count == 2
    assert all(call.args == (0.25,) for call in mock_sleep.await_args_list)


async def test_resume_no_throttle_when_zero(
    hass: HomeAssistant, resume_button: ResumeStateButton
) -> None:
    """A throttle of 0 (the default) never sleeps between resumes."""
    entities = ["light.one", "light.two"]
    resume_at = dt_util.utcnow()

    hass.data[DOMAIN] = {
        CONF_ENTITIES: entities,
        CONF_THROTTLE: 0,
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

    mock_sleep.assert_not_awaited()
