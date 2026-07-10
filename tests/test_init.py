"""Tests for setup of the Resume State component."""

from typing import TYPE_CHECKING
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.resume_state import (
    PLATFORMS,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.resume_state.const import CONF_ENTITIES, CONF_THROTTLE, DOMAIN
from custom_components.resume_state.sensor import ResumeStatus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _mock_entry() -> MockConfigEntry:
    """Build a config entry as the config flow would create it."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Resume State",
        data={},
        options={CONF_ENTITIES: ["light.test_light"], CONF_THROTTLE: 5},
    )


async def test_async_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up a config entry seeds shared state and loads platforms."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries, "async_forward_entry_setups"
    ) as mock_forward:
        assert await async_setup_entry(hass, entry) is True

    assert hass.data[DOMAIN][CONF_ENTITIES] == ["light.test_light"]
    assert hass.data[DOMAIN][CONF_THROTTLE] == 5
    assert hass.data[DOMAIN]["pressed_at"] is None
    assert hass.data[DOMAIN]["status"] == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["enabled"] is True
    assert hass.data[DOMAIN]["user_id"] is not None

    mock_forward.assert_awaited_once_with(entry, PLATFORMS)


async def test_async_unload_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry clears the shared state."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {"status": ResumeStatus.IDLE.value}

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_unload:
        assert await async_unload_entry(hass, entry) is True

    assert DOMAIN not in hass.data
    mock_unload.assert_awaited_once_with(entry, PLATFORMS)


async def test_async_unload_entry_failure_keeps_state(hass: HomeAssistant) -> None:
    """Test a failed platform unload leaves the shared state in place."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {"status": ResumeStatus.IDLE.value}

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ):
        assert await async_unload_entry(hass, entry) is False

    assert DOMAIN in hass.data
