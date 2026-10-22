"""Tests for the Resume State service actions."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context, HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.resume_state.const import (
    ATTR_DATETIME,
    CONF_ENTITIES,
    DOMAIN,
    SERVICE_CLEAR,
    SERVICE_RESUME,
    SERVICE_STORE,
)
from custom_components.resume_state.sensor import ResumeStatus
from custom_components.resume_state.services import async_setup_services

if TYPE_CHECKING:
    from contextlib import AbstractContextManager


@pytest.fixture(autouse=True)
def register_services(hass: HomeAssistant) -> None:
    """Register the service actions as async_setup would."""
    async_setup_services(hass)


@pytest.fixture(autouse=True)
def loaded_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add a loaded config entry, which the actions require."""
    entry = MockConfigEntry(domain=DOMAIN, state=ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    return entry


def _mock_recorder(historical_states: dict) -> MagicMock:
    """Build a recorder mock whose executor job returns historical_states."""
    recorder = MagicMock()
    recorder.async_add_executor_job = AsyncMock(return_value=historical_states)
    return recorder


def _patch_history(past_state: State) -> AbstractContextManager[AsyncMock]:
    """Patch the recorder lookup to return past_state for any instant."""
    return patch(
        "custom_components.resume_state.snapshot._async_historical_state",
        AsyncMock(return_value=past_state),
    )


async def test_store_service(hass: HomeAssistant) -> None:
    """The store action records the snapshot instant."""
    hass.data[DOMAIN] = {"pressed_at": None, "status": ResumeStatus.IDLE.value}

    await hass.services.async_call(DOMAIN, SERVICE_STORE, blocking=True)

    assert hass.data[DOMAIN]["pressed_at"] is not None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.STORED.value


async def test_clear_service(hass: HomeAssistant) -> None:
    """The clear action discards the snapshot."""
    hass.data[DOMAIN] = {
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.STORED.value,
    }

    await hass.services.async_call(DOMAIN, SERVICE_CLEAR, blocking=True)

    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_service(hass: HomeAssistant) -> None:
    """The resume action restores entities before the call returns."""
    entity_id = "light.test"
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    historical_states = {entity_id: [State(entity_id, "off")]}

    with (
        patch(
            "custom_components.resume_state.snapshot.get_instance",
            return_value=_mock_recorder(historical_states),
        ),
        patch(
            "custom_components.resume_state.snapshot.state_changes_during_period",
            return_value=historical_states,
        ),
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RESUME, blocking=True)

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": entity_id}
    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_service_while_disabled(hass: HomeAssistant) -> None:
    """The enable switch gates the resume action without raising."""
    entity_id = "light.test"
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.DISABLED.value,
        "enabled": False,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    await hass.services.async_call(DOMAIN, SERVICE_RESUME, blocking=True)

    assert not calls
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value


@pytest.mark.parametrize("service", [SERVICE_STORE, SERVICE_RESUME, SERVICE_CLEAR])
@pytest.mark.parametrize(
    "entry_state",
    [
        ConfigEntryState.NOT_LOADED,
        # Mid-setup (e.g. an options reload), hass.data already exists but the
        # enable switch has not yet restored `enabled`.
        ConfigEntryState.SETUP_IN_PROGRESS,
        ConfigEntryState.SETUP_ERROR,
    ],
)
async def test_service_raises_when_not_loaded(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    service: str,
    entry_state: ConfigEntryState,
) -> None:
    """Each action fails clearly unless the config entry is fully loaded."""
    loaded_entry.mock_state(hass, entry_state)
    stored_at = dt_util.utcnow() - timedelta(hours=1)
    hass.data[DOMAIN] = {
        CONF_ENTITIES: ["light.test"],
        "pressed_at": stored_at,
        "status": ResumeStatus.STORED.value,
        "enabled": True,
    }

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, service, blocking=True)

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "not_loaded"
    assert hass.data[DOMAIN]["pressed_at"] == stored_at
    assert hass.data[DOMAIN]["status"] == ResumeStatus.STORED.value


@pytest.mark.parametrize("service", [SERVICE_STORE, SERVICE_CLEAR])
async def test_service_rejects_unexpected_fields(
    hass: HomeAssistant, service: str
) -> None:
    """Store and clear take no fields, so passing one fails instead of being ignored."""
    stored_at = dt_util.utcnow() - timedelta(hours=1)
    hass.data[DOMAIN] = {"pressed_at": stored_at, "status": ResumeStatus.STORED.value}

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, service, {ATTR_DATETIME: dt_util.utcnow()}, blocking=True
        )

    assert hass.data[DOMAIN]["pressed_at"] == stored_at
    assert hass.data[DOMAIN]["status"] == ResumeStatus.STORED.value


async def test_resume_service_at_datetime_clears_stored_snapshot(
    hass: HomeAssistant,
) -> None:
    """An explicit datetime is resumed instead of the snapshot, which is cleared."""
    entity_id = "light.test"
    stored_at = dt_util.utcnow()
    resume_at = stored_at - timedelta(hours=1)
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": stored_at,
        "status": ResumeStatus.STORED.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    with _patch_history(State(entity_id, "off")) as history:
        await hass.services.async_call(
            DOMAIN, SERVICE_RESUME, {ATTR_DATETIME: resume_at}, blocking=True
        )

    history.assert_awaited_once_with(hass, entity_id, resume_at)
    assert len(calls) == 1
    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_service_at_datetime_without_stored_snapshot(
    hass: HomeAssistant,
) -> None:
    """An explicit datetime resumes even when nothing has been stored."""
    entity_id = "light.test"
    resume_at = dt_util.utcnow() - timedelta(hours=1)
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
    }

    hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    with _patch_history(State(entity_id, "off")):
        await hass.services.async_call(
            DOMAIN, SERVICE_RESUME, {ATTR_DATETIME: resume_at}, blocking=True
        )

    assert len(calls) == 1
    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_service_naive_datetime_uses_local_time_zone(
    hass: HomeAssistant,
) -> None:
    """A datetime without an offset, as the UI sends it, is in HA's time zone."""
    entity_id = "light.test"
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
    }
    expected = datetime(2020, 1, 1, 12, tzinfo=dt_util.get_default_time_zone())
    # Only meaningful when the test instance is not already on UTC.
    assert expected.utcoffset() != timedelta(0)

    hass.states.async_set(entity_id, "off")

    with _patch_history(State(entity_id, "off")) as history:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESUME,
            {ATTR_DATETIME: "2020-01-01 12:00:00"},
            blocking=True,
        )

    # A naive datetime never equals an aware one, so this also proves the
    # value was localized rather than passed through as-is.
    history.assert_awaited_once_with(hass, entity_id, expected)


async def test_resume_service_at_datetime_with_no_entities_clears_snapshot(
    hass: HomeAssistant,
) -> None:
    """An explicit-datetime resume with nothing to resume errors and clears."""
    stored_at = dt_util.utcnow()
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [],
        "pressed_at": stored_at,
        "status": ResumeStatus.STORED.value,
    }

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESUME,
        {ATTR_DATETIME: stored_at - timedelta(hours=1)},
        blocking=True,
    )

    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.ERRORED.value


async def test_resume_service_at_datetime_error_logs_and_clears_snapshot(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed explicit-datetime resume errors, clears, and logs the discarded time."""
    entity_id = "light.test"
    stored_at = dt_util.utcnow()
    resume_at = stored_at - timedelta(hours=1)
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": stored_at,
        "status": ResumeStatus.STORED.value,
    }

    # light.turn_off is not registered, so restoring the light raises.
    hass.states.async_set(entity_id, "on")

    with (
        _patch_history(State(entity_id, "off")),
        caplog.at_level(logging.WARNING),
    ):
        await hass.services.async_call(
            DOMAIN, SERVICE_RESUME, {ATTR_DATETIME: resume_at}, blocking=True
        )

    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.ERRORED.value
    assert f"Failed to resume {entity_id}" in caplog.text
    assert f"discarding the snapshot stored at {stored_at}" in caplog.text


async def test_resume_service_future_datetime_raises(hass: HomeAssistant) -> None:
    """A datetime in the future is rejected before anything is resumed."""
    entity_id = "light.test"
    hass.data[DOMAIN] = {
        CONF_ENTITIES: [entity_id],
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
    }

    with (
        _patch_history(State(entity_id, "off")) as history,
        pytest.raises(ServiceValidationError) as err,
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESUME,
            {ATTR_DATETIME: dt_util.utcnow() + timedelta(hours=1)},
            blocking=True,
        )

    assert err.value.translation_key == "datetime_in_future"
    history.assert_not_awaited()
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value


async def test_resume_service_parents_restores_to_the_call(hass: HomeAssistant) -> None:
    """Each restore gets its own context, parented to the action call's context."""
    entities = ["light.one", "light.two"]
    user_id = "resume-state-user-id"
    hass.data[DOMAIN] = {
        CONF_ENTITIES: entities,
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.STORED.value,
        "user_id": user_id,
    }

    for entity_id in entities:
        hass.states.async_set(entity_id, "on")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    caller = Context()

    with patch(
        "custom_components.resume_state.snapshot._async_historical_state",
        AsyncMock(side_effect=lambda _hass, entity_id, _at: State(entity_id, "off")),
    ):
        await hass.services.async_call(
            DOMAIN, SERVICE_RESUME, blocking=True, context=caller
        )

    assert len(calls) == 2
    # Still attributed to the integration user, with independent contexts that
    # the logbook can trace back to whatever called the action.
    assert {call.context.user_id for call in calls} == {user_id}
    assert {call.context.parent_id for call in calls} == {caller.id}
    assert len({call.context.id for call in calls} | {caller.id}) == 3
