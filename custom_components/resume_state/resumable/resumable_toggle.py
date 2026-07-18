"""Resumable toggle entity."""

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from custom_components.resume_state.resumable.resumable_entity import ResumableEntity

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


class ResumableToggle(ResumableEntity):
    """
    Base class for on/off entities restored via their domain's turn_on/turn_off.

    Restores the on/off state only. Subclasses set ``domain``; entities with
    extra attributes to replay build on ``ResumableAttributeToggle`` instead.
    """

    domain: ClassVar[str]

    def __init__(self, entity_id: str, previous_state: State) -> None:
        """Initialize the resumable toggle."""
        self.entity_id = entity_id
        self.previous_state = previous_state

    async def resume(self, hass: HomeAssistant, context: Context) -> None:
        """Handle resuming the entity to its previous state."""
        # Skip if the historical state was an error state
        if self.previous_state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Skipping resume for %s: historical state was %s",
                self.entity_id,
                self.previous_state.state,
            )
            return

        _LOGGER.debug(
            "Resuming state for %s to %s", self.entity_id, self.previous_state.state
        )

        # Skip the service call if the entity is already in the target state.
        current_state = hass.states.get(self.entity_id)

        if self.previous_state.state == "off":
            if current_state and current_state.state == "off":
                _LOGGER.debug("State for %s already matches", self.entity_id)
                return
            await hass.services.async_call(
                domain=self.domain,
                service="turn_off",
                service_data={"entity_id": self.entity_id},
                blocking=True,
                context=context,
            )
            return

        if self.previous_state.state == "on":
            if current_state and self._matches_on(current_state):
                _LOGGER.debug("State for %s already matches", self.entity_id)
                return

            service_data = self._turn_on_data()
            _LOGGER.debug(
                "Resuming %s with service data: %s",
                self.entity_id,
                service_data,
            )
            await hass.services.async_call(
                domain=self.domain,
                service="turn_on",
                service_data=service_data,
                blocking=True,
                context=context,
            )
            return

        _LOGGER.warning(
            "Unhandled historical state %s for %s; skipping",
            self.previous_state.state,
            self.entity_id,
        )

        return

    def _turn_on_data(self) -> dict[str, Any]:
        """Build the service data to replay to turn_on for an 'on' state."""
        return {"entity_id": self.entity_id}

    def _matches_on(self, current_state: State) -> bool:
        """Check whether the current state already matches the recorded 'on'."""
        return current_state.state == "on"
