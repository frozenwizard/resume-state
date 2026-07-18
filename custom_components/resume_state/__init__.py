"""The Resume State component."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .const import CONF_ENTITIES, CONF_THROTTLE, CONF_THROTTLE_DEFAULT, DOMAIN
from .sensor import ResumeStatus
from .user import async_get_or_create_user

if TYPE_CHECKING:
    from homeassistant.auth.models import User
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

__all__ = ["async_setup_entry", "async_unload_entry"]

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Resume State from a config entry."""
    # Act as a dedicated syste m user so restored changes are attributed to the
    # integration in the logbook, distinct from the user's own actions.
    user: User = await async_get_or_create_user(hass)

    hass.data[DOMAIN] = {
        CONF_ENTITIES: entry.options.get(CONF_ENTITIES, []),
        CONF_THROTTLE: entry.options.get(CONF_THROTTLE, CONF_THROTTLE_DEFAULT),
        "pressed_at": None,
        "status": ResumeStatus.IDLE.value,
        "enabled": True,
        "user_id": user.id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Resume State config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok
