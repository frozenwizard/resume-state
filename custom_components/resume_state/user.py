"""The Home Assistant system user that Resume State acts as."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.auth.const import GROUP_ID_USER

from custom_components.resume_state.const import INTEGRATION_USER_NAME

if TYPE_CHECKING:
    from homeassistant.auth.models import User
    from homeassistant.core import HomeAssistant


async def async_get_or_create_user(hass: HomeAssistant) -> User:
    """Return the integration's system user, creating it once if absent."""
    for user in await hass.auth.async_get_users():
        if user.system_generated and user.name == INTEGRATION_USER_NAME:
            return user
    # In the users group so it can control (but not administer) entities: HA
    # enforces that on any service call carrying a user id.
    return await hass.auth.async_create_system_user(
        INTEGRATION_USER_NAME, group_ids=[GROUP_ID_USER]
    )
