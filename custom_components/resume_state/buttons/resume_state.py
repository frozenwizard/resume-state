"""Resume State button entity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from custom_components.resume_state.snapshot import async_resume_snapshot


class ResumeStateButton(ButtonEntity):
    """Resumes the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "resume_state"
    _attr_unique_id = "button.resume_home_state"
    _attr_icon = "mdi:home-clock"

    async def async_press(self) -> None:
        """Handle the button press."""
        await async_resume_snapshot(self.hass)
