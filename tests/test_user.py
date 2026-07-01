"""Tests for the Resume State integration user."""

from typing import TYPE_CHECKING

from custom_components.resume_state.const import INTEGRATION_USER_NAME
from custom_components.resume_state.user import async_get_or_create_user

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_get_or_create_user_creates_system_user(hass: HomeAssistant) -> None:
    """The helper creates a named, system-generated user."""
    user = await async_get_or_create_user(hass)

    assert user.name == INTEGRATION_USER_NAME
    assert user.system_generated is True


async def test_get_or_create_user_is_idempotent(hass: HomeAssistant) -> None:
    """Calling twice reuses the same user instead of creating a duplicate."""
    first = await async_get_or_create_user(hass)
    second = await async_get_or_create_user(hass)

    assert first.id == second.id
    matching = [
        user
        for user in await hass.auth.async_get_users()
        if user.name == INTEGRATION_USER_NAME
    ]
    assert len(matching) == 1
