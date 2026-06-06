"""Services definitions."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

from .config import CONF_DELAY, CONF_ENTITIES
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_hello_world(_call: ServiceCall) -> None:
    """Handle the hello_world service call."""
    _LOGGER.info("Hello World")

    entities: list[str] = _call.hass.data[DOMAIN][CONF_ENTITIES]
    delay: int = _call.hass.data[DOMAIN][CONF_DELAY]

    _LOGGER.info("Config %s %s", entities, delay)


async def async_setup_services(_hass: HomeAssistant) -> None:
    """Set up the services."""
    _hass.services.async_register(DOMAIN, "hello_world", async_hello_world)
