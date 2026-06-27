"""Tests for setup of the Resume State component."""

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from custom_components.resume_state import async_setup
from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.sensor import ResumeStatus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_async_setup_valid_config(hass: HomeAssistant) -> None:
    """Test setting up the integration with a valid config."""
    config: dict[str, Any] = {
        DOMAIN: {
            "entities": ["light.test_light"],
            "delay": 5,
        }
    }

    with patch(
        "custom_components.resume_state.async_load_platform"
    ) as mock_load_platform:
        result = await async_setup(hass, config)
        await hass.async_block_till_done()

        assert result is True
        assert DOMAIN in hass.data
        assert hass.data[DOMAIN]["entities"] == ["light.test_light"]
        assert hass.data[DOMAIN]["delay"] == 5
        assert hass.data[DOMAIN]["pressed_at"] is None
        assert hass.data[DOMAIN]["status"] == ResumeStatus.CLEARED.value

        assert mock_load_platform.call_count == 2
        calls = mock_load_platform.call_args_list
        platforms = [call[0][1] for call in calls]
        assert "sensor" in platforms
        assert "button" in platforms


async def test_async_setup_missing_config(hass: HomeAssistant) -> None:
    """Test setting up the integration with missing config."""
    config: dict[str, Any] = {}

    result = await async_setup(hass, config)
    assert result is False
    assert DOMAIN not in hass.data
