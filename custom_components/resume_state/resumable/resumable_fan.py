"""Resumable fan entity."""

from typing import Any, ClassVar

from homeassistant.components.fan import DOMAIN as FAN_DOMAIN

from custom_components.resume_state.resumable.resumable_attribute_toggle import (
    ResumableAttributeToggle,
)


class ResumableFan(ResumableAttributeToggle):
    """
    A fan entity that is resumable.

    Restores on/off, speed percentage, and preset mode. Restoring
    ``direction`` and ``oscillating`` is not supported: they are set through
    dedicated service calls.
    """

    domain: ClassVar[str] = FAN_DOMAIN

    def _restore_attributes(self) -> dict[str, Any]:
        """
        Select the attributes to replay to fan.turn_on for an 'on' state.

        A fan running in a preset mode still reports a ``percentage``
        alongside it, but how ``fan.turn_on`` reconciles both at once is
        integration-defined, so we replay only the preset when one was
        active and the percentage otherwise.
        """
        preset_mode = self.previous_state.attributes.get("preset_mode")
        if preset_mode is not None:
            return {"preset_mode": preset_mode}

        percentage = self.previous_state.attributes.get("percentage")
        if percentage is not None:
            return {"percentage": percentage}

        return {}
