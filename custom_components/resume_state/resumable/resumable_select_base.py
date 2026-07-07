"""Resumable select entity."""

import logging
from typing import TYPE_CHECKING, ClassVar

from custom_components.resume_state.resumable.resumable_entity import ResumableEntity

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


class ResumableSelectBase(ResumableEntity):
    """
    Base class for entities restored by replaying their selected option.

    The entity's state *is* the option, restored via the domain's
    ``select_option`` service. Subclasses set ``domain``.
    """

    domain: ClassVar[str]

    def __init__(self, entity_id: str, previous_state: State) -> None:
        """Initialize the resumable select."""
        self.entity_id = entity_id
        self.previous_state = previous_state

    async def resume(self, hass: HomeAssistant, context: Context) -> None:
        """Handle resuming the entity to its previously selected option."""
        # Skip if the historical state was an error state
        if self.previous_state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Skipping resume for %s: historical state was %s",
                self.entity_id,
                self.previous_state.state,
            )
            return

        option = self.previous_state.state
        _LOGGER.info("Resuming state for %s to %s", self.entity_id, option)

        current_state = hass.states.get(self.entity_id)

        # Skip the service call if the entity already has the target option.
        if current_state is not None and current_state.state == option:
            _LOGGER.info("State for %s already matches", self.entity_id)
            return

        # Only proceed if the live entity can currently accept the option;
        # otherwise select_option would raise and fail the batch. An entity
        # that is unavailable reports no options, and options can change
        # between snapshot and resume, so guard against both.
        if current_state is not None:
            options = current_state.attributes.get("options")
            if options is None:
                _LOGGER.warning(
                    "Skipping resume for %s: entity reports no options to select",
                    self.entity_id,
                )
                return
            if option not in options:
                _LOGGER.warning(
                    "Skipping resume for %s: option %s is no longer available",
                    self.entity_id,
                    option,
                )
                return

        await hass.services.async_call(
            domain=self.domain,
            service="select_option",
            service_data={"entity_id": self.entity_id, "option": option},
            blocking=True,
            context=context,
        )
