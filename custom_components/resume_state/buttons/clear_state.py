"""Clear State button entity."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.resume_state.const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE
from custom_components.resume_state.sensor import ResumeStatus

_LOGGER = logging.getLogger(__name__)


class ClearStateButton(ButtonEntity):
    """Clears the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear_state"
    _attr_unique_id = "button.clear_home_state"
    _attr_icon = "mdi:home-off-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Clearing state")
        self.hass.data[DOMAIN]["pressed_at"] = None
        # Clearing the snapshot is allowed while disabled
        if self.hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
            self.hass.data[DOMAIN]["status"] = ResumeStatus.IDLE.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
