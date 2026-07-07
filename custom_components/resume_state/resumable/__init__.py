"""resumable package."""

from typing import TYPE_CHECKING

from homeassistant.core import split_entity_id

from custom_components.resume_state import const
from custom_components.resume_state.resumable.resumable_fan import ResumableFan
from custom_components.resume_state.resumable.resumable_input_boolean import (
    ResumableInputBoolean,
)
from custom_components.resume_state.resumable.resumable_input_select import (
    ResumableInputSelect,
)
from custom_components.resume_state.resumable.resumable_light import ResumableLight
from custom_components.resume_state.resumable.resumable_select import ResumableSelect
from custom_components.resume_state.resumable.resumable_switch import ResumableSwitch

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import State

    from custom_components.resume_state.resumable.resumable_entity import (
        ResumableEntity,
    )

# Maps a supported entity domain to the resumable that restores it. Domains
# absent here are unsupported and yield ``None``.
_RESUMABLE_BY_DOMAIN: dict[str, Callable[[str, State], ResumableEntity]] = {
    const.FAN_DOMAIN: ResumableFan,
    const.INPUT_BOOLEAN_DOMAIN: ResumableInputBoolean,
    const.INPUT_SELECT_DOMAIN: ResumableInputSelect,
    const.LIGHT_DOMAIN: ResumableLight,
    const.SELECT_DOMAIN: ResumableSelect,
    const.SWITCH_DOMAIN: ResumableSwitch,
}

# The domains this integration can resume, derived from the dispatch table so
# it always matches the resumables actually registered above. Used to filter
# configured entities before attempting a resume.
SUPPORTED_DOMAINS: frozenset[str] = frozenset(_RESUMABLE_BY_DOMAIN)


def build_resumable_entity(
    entity_id: str, previous_state: State
) -> ResumableEntity | None:
    """Build a resumable entity from a previous state."""
    domain, _ = split_entity_id(entity_id)
    resumable_cls = _RESUMABLE_BY_DOMAIN.get(domain)
    if resumable_cls is None:
        return None
    return resumable_cls(entity_id, previous_state)
