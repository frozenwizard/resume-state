"""Tests for setup of the button platform."""

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from custom_components.resume_state.button import async_setup_platform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_button_async_setup_platform(hass: HomeAssistant) -> None:
    """Test setting up the button platform."""
    mock_async_add_entities = MagicMock()
    config: dict[str, Any] = {}

    await async_setup_platform(hass, config, mock_async_add_entities)

    mock_async_add_entities.assert_called_once()
    entities_added = mock_async_add_entities.call_args[0][0]
    assert len(entities_added) == 3

    classes_added = [type(entity).__name__ for entity in entities_added]
    assert "ResumeStateButton" in classes_added
    assert "StoreStateButton" in classes_added
    assert "ClearStateButton" in classes_added
