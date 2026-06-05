"""Tests for the Resume State component."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.resume_state import async_setup
from custom_components.resume_state.const import DOMAIN, SERVICE_HELLO_WORLD


@pytest.mark.asyncio
async def test_async_setup_registers_service() -> None:
    """Test that the hello_world service is registered during setup."""
    hass = AsyncMock()
    hass.services = AsyncMock()

    # Run setup
    result = await async_setup(hass, {})

    assert result is True
    # Check if async_register was called with correct arguments
    # The third argument is the handler function, so we check the first two.
    hass.services.async_register.assert_called_once()
    args, _kwargs = hass.services.async_register.call_args
    assert args[0] == DOMAIN
    assert args[1] == SERVICE_HELLO_WORLD


@pytest.mark.asyncio
async def test_hello_world_service_logs_hello_world() -> None:
    """Test that the hello_world service handler logs 'Hello World'."""
    hass = AsyncMock()
    hass.services = AsyncMock()

    with patch("custom_components.resume_state._LOGGER") as mock_logger:
        await async_setup(hass, {})

        # Get the registered handler
        args, _kwargs = hass.services.async_register.call_args
        handler = args[2]

        # Call the handler
        await handler(AsyncMock())

        # Verify it logged "Hello World"
        mock_logger.info.assert_called_once_with("Hello World")
