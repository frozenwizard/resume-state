"""Resume State sensor entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.resume_state.const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE

if TYPE_CHECKING:
    from datetime import datetime


class ResumeStateSensor(SensorEntity):
    """The Resume State sensor."""

    _attr_has_entity_name = True
    _attr_unique_id = "sensor.resume_state_at"
    _attr_translation_key = "resume_at"
    _attr_icon = "mdi:home-clock-outline"
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
