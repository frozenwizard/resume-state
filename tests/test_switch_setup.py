"""Tests for setup of the switch platform."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.switch import async_setup_entry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_switch_async_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the switch platform from a config entry."""
    mock_async_add_entities = MagicMock()

    await async_setup_entry(hass, MagicMock(), mock_async_add_entities)

    mock_async_add_entities.assert_called_once()
    entities_added = mock_async_add_entities.call_args[0][0]
    assert len(entities_added) == 1

    classes_added = [type(entity).__name__ for entity in entities_added]
    assert "ResumeStateSwitch" in classes_added

    hass.data.setdefault(DOMAIN, {})

    for entity in entities_added:
        entity.hass = hass
        with patch(
            "custom_components.resume_state.switches.resume_state_switch.RestoreEntity.async_get_last_state",
            return_value=None,
        ):
            await entity.async_added_to_hass()
