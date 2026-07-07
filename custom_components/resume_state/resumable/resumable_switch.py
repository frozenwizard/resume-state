"""Resumable switch entity."""

from typing import ClassVar

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN

from custom_components.resume_state.resumable.resumable_toggle import ResumableToggle


class ResumableSwitch(ResumableToggle):
    """A switch entity that is resumable. Restores on/off."""

    domain: ClassVar[str] = SWITCH_DOMAIN
