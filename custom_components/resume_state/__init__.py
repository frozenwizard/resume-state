"""The Resume State component."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv

from .const import CONF_ENTITIES, CONF_THROTTLE, CONF_THROTTLE_DEFAULT, DOMAIN
from .sensor import ResumeStatus
from .services import async_setup_services
from .snapshot import async_abort_resume
from .user import async_get_or_create_user

if TYPE_CHECKING:
    from homeassistant.auth.models import User
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

__all__ = ["CONFIG_SCHEMA", "async_setup", "async_setup_entry", "async_unload_entry"]

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]

# UI-only setup; hassfest requires a config schema once async_setup exists.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up the Resume State service actions."""
    # Registered once for the integration rather than per entry, so the actions
    # exist (and fail clearly) even while the config entry is not loaded.
    async_setup_services(hass)
    return True


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
    # Stop a resume still in progress even if the unload fails: it would
    # otherwise outlive the entry, with no loaded entry left to clear it.
    async_abort_resume(hass)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok
