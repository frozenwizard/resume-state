"""resumable package."""

from typing import TYPE_CHECKING

from homeassistant.core import split_entity_id

from custom_components.resume_state import const
from custom_components.resume_state.resumable.resumable_fan import ResumableFan
from custom_components.resume_state.resumable.resumable_input_boolean import (
    ResumableInputBoolean,
)
from custom_components.resume_state.resumable.resumable_light import ResumableLight
from custom_components.resume_state.resumable.resumable_switch import ResumableSwitch

if TYPE_CHECKING:
    from homeassistant.core import State

    from custom_components.resume_state.resumable.resumable_entity import (
        ResumableEntity,
    )


def build_resumable_entity(
    entity_id: str, previous_state: State
) -> ResumableEntity | None:
    """Build a resumable entity from a previous state."""
    domain, _ = split_entity_id(entity_id)
    match domain:
        case const.FAN_DOMAIN:
            return ResumableFan(entity_id, previous_state)
        case const.INPUT_BOOLEAN_DOMAIN:
            return ResumableInputBoolean(entity_id, previous_state)
        case const.LIGHT_DOMAIN:
            return ResumableLight(entity_id, previous_state)
        case const.SWITCH_DOMAIN:
            return ResumableSwitch(entity_id, previous_state)
        case _:
            return None
