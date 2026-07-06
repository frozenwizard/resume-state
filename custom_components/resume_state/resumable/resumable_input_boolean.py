"""Resumable input boolean entity."""

from typing import ClassVar

from homeassistant.components.input_boolean import DOMAIN as INPUT_BOOLEAN_DOMAIN

from custom_components.resume_state.resumable.resumable_toggle import ResumableToggle


class ResumableInputBoolean(ResumableToggle):
    """An input boolean entity that is resumable. Restores on/off."""

    domain: ClassVar[str] = INPUT_BOOLEAN_DOMAIN
