"""Tests for the Resume State component."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.resume_state import async_setup
from custom_components.resume_state.const import DOMAIN, SERVICE_HELLO_WORLD


@pytest.mark.asyncio
async def test_async_setup_registers_service() -> None:
    """Test that the hello_world service is registered during setup."""
    hass = MagicMock()
    hass.services = MagicMock()

    # Run setup
    result = await async_setup(hass, {DOMAIN: {}})

    assert result is True
    # Check if async_register was called with correct arguments
    # The third argument is the handler function, so we check the first two.
    hass.services.async_register.assert_called_once()
    args, _kwargs = hass.services.async_register.call_args
    assert args[0] == DOMAIN
    assert args[1] == SERVICE_HELLO_WORLD


@pytest.mark.asyncio
async def test_hello_world_service_logs_config() -> None:
    """Test that the hello_world service handler logs the configuration."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.data = {}

    config = {
        DOMAIN: {
            "entities": ["light.living_room", "switch.fan"],
            "delay": 5,
        }
    }

    with patch("custom_components.resume_state.services._LOGGER") as mock_logger:
        await async_setup(hass, config)

        # Get the registered handler
        args, _kwargs = hass.services.async_register.call_args
        handler = args[2]

        # Call the handler
        mock_call = MagicMock()
        mock_call.hass = hass
        await handler(mock_call)

        # Verify it logged the config correctly
        mock_logger.info.assert_any_call(
            "Config %s %s", ["light.living_room", "switch.fan"], 5
        )
