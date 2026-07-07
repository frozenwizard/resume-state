"""Resumable base entity."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant


class ResumableEntity(ABC):
    """Base class for resumable entities."""

    @abstractmethod
    async def resume(self, hass: HomeAssistant, context: Context) -> None:
        """Resume the entity, attributing the change to the given context."""
