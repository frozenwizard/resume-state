"""The Resume State component."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.discovery import async_load_platform

from .config import CONF_ENTITIES, CONF_THROTTLE, CONFIG_SCHEMA
from .sensor import ResumeStatus

if TYPE_CHECKING:
    from homeassistant import core

from .const import DOMAIN

__all__ = ["CONFIG_SCHEMA", "async_setup"]

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
        CONF_THROTTLE: conf.get(CONF_THROTTLE),
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
        "enabled": True,
    }

    hass.async_create_task(async_load_platform(hass, "sensor", DOMAIN, {}, _config))
    hass.async_create_task(async_load_platform(hass, "button", DOMAIN, {}, _config))
    hass.async_create_task(async_load_platform(hass, "switch", DOMAIN, {}, _config))

    return True
