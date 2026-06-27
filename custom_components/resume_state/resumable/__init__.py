"""resumable package."""

from typing import TYPE_CHECKING

from custom_components.resume_state.resumable.resumable_light import ResumableLight

if TYPE_CHECKING:
    from homeassistant.core import State

    from custom_components.resume_state.resumable.resumable_entity import (
        ResumableEntity,
    )


def build_resumable_entity(
    entity_id: str, previous_state: State
) -> ResumableEntity | None:
    """Build a resumable entity from a previous state."""
    if entity_id.startswith("light."):
        return ResumableLight(entity_id, previous_state)
    return None
