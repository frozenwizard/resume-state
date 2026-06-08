"""The Resume State sensor."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    _hass: HomeAssistant,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Resume State sensor platform."""
    async_add_entities([ResumeStateSensor()])


class ResumeStateSensor(SensorEntity):
    """The Resume State sensor."""

    _attr_has_entity_name = True
    _attr_unique_id = "sensor.resume_state_at"
    _attr_name = "When to resume"
    _attr_icon = "mdi:clock-time-four-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Returns the timestamp of when to resume state, or None."""
        return self.hass.data[DOMAIN]["pressed_at"]
