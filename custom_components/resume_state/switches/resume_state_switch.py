"""Resume State switch entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.resume_state.const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE
from custom_components.resume_state.sensor import ResumeStatus

_LOGGER = logging.getLogger(__name__)


class ResumeStateSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable or disable this integration."""

    _attr_has_entity_name = True
    _attr_translation_key = "resume_state_enabled"
    _attr_unique_id = "switch.resume_home_state_enabled"
    _attr_icon = "mdi:toggle-switch"

    def __init__(self) -> None:
        """Initialize the switch."""
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.hass.data[DOMAIN]["enabled"] = self._attr_is_on
        _LOGGER.debug("Restored enabled state: %s", self._attr_is_on)

        if not self._attr_is_on:
            self.hass.data[DOMAIN]["status"] = ResumeStatus.DISABLED.value

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Enable resuming state and sets status to IDLE."""
        _LOGGER.debug("Enabling resume state")
        self._attr_is_on = True
        self.hass.data[DOMAIN]["enabled"] = True
        if self.hass.data[DOMAIN].get("status") == ResumeStatus.DISABLED.value:
            self.hass.data[DOMAIN]["status"] = ResumeStatus.IDLE.value
            async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
        self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Disable resuming state and sets status to DISABLED."""
        _LOGGER.debug("Disabling resume state")
        self._attr_is_on = False
        self.hass.data[DOMAIN]["enabled"] = False
        self.hass.data[DOMAIN]["status"] = ResumeStatus.DISABLED.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
        self.async_write_ha_state()
