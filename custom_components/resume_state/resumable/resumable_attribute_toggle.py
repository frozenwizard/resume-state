"""Resumable toggle entity that also replays attributes."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from custom_components.resume_state.resumable.resumable_toggle import ResumableToggle

if TYPE_CHECKING:
    from homeassistant.core import State


class ResumableAttributeToggle(ResumableToggle, ABC):
    """
    An on/off entity that also replays selected recorded attributes.

    Subclasses pick which recorded attributes to replay to
    ``<domain>.turn_on`` in ``_restore_attributes``.
    """

    @abstractmethod
    def _restore_attributes(self) -> dict[str, Any]:
        """Select the attributes to replay to turn_on for an 'on' state."""

    def _turn_on_data(self) -> dict[str, Any]:
        """Build the turn_on service data, including the replayed attributes."""
        return {**super()._turn_on_data(), **self._restore_attributes()}

    def _matches_on(self, current_state: State) -> bool:
        """Check whether the current state and attributes already match."""
        return super()._matches_on(current_state) and all(
            self._normalize(current_state.attributes.get(attr))
            == self._normalize(value)
            for attr, value in self._restore_attributes().items()
        )

    def _normalize(self, value: Any) -> Any:
        """Normalize a value for comparison (recorder lists vs live tuples)."""
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value
