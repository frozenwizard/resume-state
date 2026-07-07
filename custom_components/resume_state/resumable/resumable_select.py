"""Resumable select entity."""

from typing import ClassVar

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN

from custom_components.resume_state.resumable.resumable_select_base import (
    ResumableSelectBase,
)


class ResumableSelect(ResumableSelectBase):
    """A select entity that is resumable. Restores the selected option."""

    domain: ClassVar[str] = SELECT_DOMAIN
