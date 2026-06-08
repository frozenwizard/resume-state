"""The Resume State button entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity

if TYPE_CHECKING:
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
    _attr_name = "Store Home State"
    _attr_unique_id = "button.store_home_state"
    _attr_icon = "mdi:led-strip-variant"

    async def async_press(self) -> None:
        """Handle the button press."""
        pressed_at = dt_util.utcnow()
        _LOGGER.info("Button pressed at %s", pressed_at)

        self.hass.data[DOMAIN]["pressed_at"] = pressed_at


class ResumeStateButton(ButtonEntity):
    """Resumes the state of the entities from the `resume_state` data."""

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Resuming State")

        # Here we would resume the state
        # For now we just clear it
        self.hass.data[DOMAIN]["pressed_at"] = None


class ClearStateButton(ButtonEntity):
    """Clears the state of the entities from the `resume_state` data."""

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Clearing State")
        self.hass.data[DOMAIN]["pressed_at"] = None
