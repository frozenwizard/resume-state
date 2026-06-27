"""Resumable base entity."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class ResumableEntity(ABC):
    """Base class for resumable entities."""

    @abstractmethod
    async def resume(self, hass: HomeAssistant) -> None:
        """Resume the entity."""

    def _normalize(self, value: Any) -> Any:
        """Normalize a value for comparison (recorder lists vs live tuples)."""
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value
