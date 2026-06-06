"""The Resume State component."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .config import CONF_DELAY, CONF_ENTITIES
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant import core

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: core.HomeAssistant, _config: dict[str, Any]) -> bool:
    """Set up the Resume State component."""
    conf = _config.get(DOMAIN)

    if conf is None:
        _LOGGER.error("No configuration found for Resume State")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        CONF_ENTITIES: conf.get(CONF_ENTITIES),
        CONF_DELAY: conf.get(CONF_DELAY),
    }

    await async_setup_services(hass)

    return True
