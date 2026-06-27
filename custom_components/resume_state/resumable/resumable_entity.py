"""Resumable base entity."""

from abc import ABC, abstractmethod
from typing import Any


class ResumableEntity(ABC):
    """Base class for resumable entities."""

    @abstractmethod
    async def resume(self) -> None:
        """Resume the entity."""

    def _normalize(self, value: Any) -> Any:
        """Normalize a value for comparison (recorder lists vs live tuples)."""
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value
