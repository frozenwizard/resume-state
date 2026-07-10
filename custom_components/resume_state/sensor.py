"""The Resume State sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .sensors import ResumeStateSensor, ResumeStatus, ResumeStatusSensor

__all__ = [
    "ResumeStateSensor",
    "ResumeStatus",
    "ResumeStatusSensor",
]


async def async_setup_entry(
    _hass: HomeAssistant,
    _entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Resume State sensor platform from a config entry."""
    async_add_entities([ResumeStateSensor(), ResumeStatusSensor()])
