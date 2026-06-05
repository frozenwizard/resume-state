"""The Resume State component."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant import core

from .const import DOMAIN, SERVICE_HELLO_WORLD

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: core.HomeAssistant, _config: dict[str, Any]) -> bool:
    """Set up the Resume State component."""

    async def async_hello_world(_call: core.ServiceCall) -> None:
        """Handle the hello_world service call."""
        _LOGGER.info("Hello World")

    hass.services.async_register(DOMAIN, SERVICE_HELLO_WORLD, async_hello_world)

    return True
