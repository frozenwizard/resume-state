"""The Resume State button entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    _hass: HomeAssistant,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Resume State button platform."""
    async_add_entities(
        [
            StoreStateButton(),
            ResumeStateButton(),
            ClearStateButton(),
        ]
    )


class StoreStateButton(ButtonEntity):
    """Stores the current state of the entities in the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "store_state"
    _attr_unique_id = "button.store_home_state"
    _attr_icon = "mdi:led-strip-variant"

    async def async_press(self) -> None:
        """Handle the button press."""
        pressed_at = dt_util.utcnow()
        _LOGGER.info("Button pressed at %s", pressed_at)

        self.hass.data[DOMAIN]["pressed_at"] = pressed_at
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)


class ResumeStateButton(ButtonEntity):
    """Resumes the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "resume_state"
    _attr_unique_id = "button.resume_home_state"
    _attr_icon = "mdi:play-circle-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Resuming State")

        # Here we would resume the state
        # For now we just clear it
        self.hass.data[DOMAIN]["pressed_at"] = None
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)


class ClearStateButton(ButtonEntity):
    """Clears the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear_state"
    _attr_unique_id = "button.clear_home_state"
    _attr_icon = "mdi:delete-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Clearing State")
        self.hass.data[DOMAIN]["pressed_at"] = None
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
