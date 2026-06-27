"""The Resume State sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .sensors import ResumeStateSensor, ResumeStatus, ResumeStatusSensor

__all__ = [
    "ResumeStateSensor",
    "ResumeStatus",
    "ResumeStatusSensor",
]


async def async_setup_platform(
    _hass: HomeAssistant,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Resume State sensor platform."""
    async_add_entities([ResumeStateSensor(), ResumeStatusSensor()])
