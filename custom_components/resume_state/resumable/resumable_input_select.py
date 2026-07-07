"""Resumable input select entity."""

from typing import ClassVar

from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN

from custom_components.resume_state.resumable.resumable_select_base import (
    ResumableSelectBase,
)


class ResumableInputSelect(ResumableSelectBase):
    """An input select entity that is resumable. Restores the selected option."""

    domain: ClassVar[str] = INPUT_SELECT_DOMAIN
