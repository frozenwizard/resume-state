"""Store State button entity."""

from __future__ import annotations

import logging

import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.resume_state.const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE
from custom_components.resume_state.sensor import ResumeStatus

_LOGGER = logging.getLogger(__name__)


class StoreStateButton(ButtonEntity):
    """Stores the current state of the entities in the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "store_state"
    _attr_unique_id = "button.store_home_state"
    _attr_icon = "mdi:home-import-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        pressed_at = dt_util.utcnow()
        _LOGGER.info("Storing state at %s", pressed_at)

        self.hass.data[DOMAIN]["pressed_at"] = pressed_at
        # Storing the snapshot is allowed while disabled
        if self.hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
            self.hass.data[DOMAIN]["status"] = ResumeStatus.STORED.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
