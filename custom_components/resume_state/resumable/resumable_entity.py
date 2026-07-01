"""Resumable base entity."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant


class ResumableEntity(ABC):
    """Base class for resumable entities."""

    @abstractmethod
    async def resume(self, hass: HomeAssistant, context: Context) -> None:
        """Resume the entity, attributing the change to the given context."""

    def _normalize(self, value: Any) -> Any:
        """Normalize a value for comparison (recorder lists vs live tuples)."""
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value
