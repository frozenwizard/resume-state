"""The Resume State button entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .buttons import ClearStateButton, ResumeStateButton, StoreStateButton


async def async_setup_entry(
    _hass: HomeAssistant,
    _entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Resume State button platform from a config entry."""
    async_add_entities(
        [
            StoreStateButton(),
            ResumeStateButton(),
            ClearStateButton(),
        ]
    )
