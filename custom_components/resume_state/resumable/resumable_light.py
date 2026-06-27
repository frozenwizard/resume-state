"""Resumable light entity."""

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.light.const import DOMAIN as LIGHT_DOMAIN

from custom_components.resume_state.resumable.resumable_entity import ResumableEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, State

_LOGGER = logging.getLogger(__name__)
# Maps a light's recorded ``color_mode`` to the single attribute that should be
# replayed to ``light.turn_on``. Home Assistant exposes every color
# representation simultaneously (with ``None`` for the inactive ones, and even a
# derived ``rgb_color`` while in ``color_temp`` mode), but ``light.turn_on``
# rejects more than one color from its exclusive group, so we restore only the
# representation that was actually active.
COLOR_MODE_ATTR: dict[str, str] = {
    "color_temp": "color_temp_kelvin",
    "hs": "hs_color",
    "rgb": "rgb_color",
    "rgbw": "rgbw_color",
    "rgbww": "rgbww_color",
    "xy": "xy_color",
}


class ResumableLight(ResumableEntity):
    """A light entity that is resumable."""

    def __init__(
        self, hass: HomeAssistant, entity_id: str, previous_state: State
    ) -> None:
        """Initialize the resumable light."""
        self.hass = hass
        self.entity_id = entity_id
        self.previous_state = previous_state

    async def resume(self) -> None:
        """Handle resuming the light with its previous attributes."""
        # Skip if the historical state was an error state
        if self.previous_state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Skipping resume for %s: historical state was %s",
                self.entity_id,
                self.previous_state.state,
            )
            return

        _LOGGER.info(
            "Resuming state for %s to %s", self.entity_id, self.previous_state.state
        )

        # Skip the service call if the light is already in the target state.
        current_state = self.hass.states.get(self.entity_id)

        if self.previous_state.state == "off":
            if current_state and current_state.state == "off":
                _LOGGER.info("State for %s already matches", self.entity_id)
                return
            await self.hass.services.async_call(
                domain=LIGHT_DOMAIN,
                service="turn_off",
                service_data={"entity_id": self.entity_id},
                blocking=True,
            )
            return

        if self.previous_state.state == "on":
            desired = self._restore_attributes()
            if (
                current_state
                and current_state.state == "on"
                and all(
                    self._normalize(current_state.attributes.get(attr))
                    == self._normalize(value)
                    for attr, value in desired.items()
                )
            ):
                _LOGGER.info(
                    "State and attributes for %s already match", self.entity_id
                )
                return

            service_data: dict[str, Any] = {"entity_id": self.entity_id, **desired}
            _LOGGER.debug(
                "Resuming light with service data for %s: %s",
                self.entity_id,
                service_data,
            )
            await self.hass.services.async_call(
                domain=LIGHT_DOMAIN,
                service="turn_on",
                service_data=service_data,
                blocking=True,
            )
            return

        _LOGGER.warning(
            "Unhandled historical state %s for %s; skipping",
            self.previous_state.state,
            self.entity_id,
        )

        return

    def _restore_attributes(self) -> dict[str, Any]:
        """
        Select the attributes to replay to light.turn_on for an 'on' state.

        Skips ``None`` values (Home Assistant exposes the full attribute set,
        using ``None`` for inactive ones) and includes only the single color
        attribute matching the recorded ``color_mode`` so the mutually
        exclusive color group in ``light.turn_on`` is never violated.
        """
        attrs: dict[str, Any] = {}
        for attr in ("brightness", "effect"):
            value = self.previous_state.attributes.get(attr)
            if value is not None:
                attrs[attr] = value

        color_mode = self.previous_state.attributes.get("color_mode")
        color_attr = (
            COLOR_MODE_ATTR.get(color_mode) if isinstance(color_mode, str) else None
        )
        if color_attr is not None:
            value = self.previous_state.attributes.get(color_attr)
            if value is not None:
                attrs[color_attr] = value
        return attrs
