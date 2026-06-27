"""Tests for setup of the sensor platform."""

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from custom_components.resume_state.sensor import async_setup_platform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_sensor_async_setup_platform(hass: HomeAssistant) -> None:
    """Test setting up the sensor platform."""
    mock_async_add_entities = MagicMock()
    config: dict[str, Any] = {}

    await async_setup_platform(hass, config, mock_async_add_entities)

    mock_async_add_entities.assert_called_once()
    entities_added = mock_async_add_entities.call_args[0][0]
    assert len(entities_added) == 2

    classes_added = [type(entity).__name__ for entity in entities_added]
    assert "ResumeStateSensor" in classes_added
    assert "ResumeStatusSensor" in classes_added

    for entity in entities_added:
        entity.hass = hass
        await entity.async_added_to_hass()
