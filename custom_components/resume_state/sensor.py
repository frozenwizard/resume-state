"""The Resume State sensor."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE

_LOGGER = logging.getLogger(__name__)


class ResumeStatus(StrEnum):
    """Status options for the resume state integration."""

    CLEARED = "cleared"
    STORED = "stored"
    RESUMING = "resuming"
    ERRORED = "errored"


async def async_setup_platform(
    _hass: HomeAssistant,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Resume State sensor platform."""
    async_add_entities([ResumeStateSensor(), ResumeStatusSensor()])


class ResumeStateSensor(SensorEntity):
    """The Resume State sensor."""

    _attr_has_entity_name = True
    _attr_unique_id = "sensor.resume_state_at"
    _attr_translation_key = "resume_at"
    _attr_icon = "mdi:clock-time-four-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE_RESUME_STATE,
                self.async_write_ha_state,
            )
        )

    @property
    def native_value(self) -> datetime | None:
        """Returns the timestamp of when to resume state, or None."""
        pressed_at: datetime | None = self.hass.data[DOMAIN]["pressed_at"]
        return pressed_at


class ResumeStatusSensor(SensorEntity):
    """A sensor that outputs the current status as an Enum."""

    _attr_has_entity_name = True
    _attr_unique_id = "sensor.resume_state_status"
    _attr_icon = "mdi:information-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_translation_key = "resume_status"

    def __init__(self) -> None:
        """Initialize the sensor."""
        self._attr_options = [status.value for status in ResumeStatus]

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE_RESUME_STATE,
                self.async_write_ha_state,
            )
        )

    @property
    def native_value(self) -> str:
        """Return the current status."""
        status: str = self.hass.data[DOMAIN].get("status", ResumeStatus.CLEARED.value)
        return status
