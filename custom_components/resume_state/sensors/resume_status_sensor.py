"""Resume Status sensor entity."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.resume_state.const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE
from custom_components.resume_state.sensors.resume_status import ResumeStatus


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
