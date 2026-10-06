"""Clear State button entity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from custom_components.resume_state.snapshot import async_clear_snapshot


class ClearStateButton(ButtonEntity):
    """Clears the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear_state"
    _attr_unique_id = "button.clear_home_state"
    _attr_icon = "mdi:home-off-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        async_clear_snapshot(self.hass)
