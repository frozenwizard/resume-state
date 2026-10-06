"""Store State button entity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from custom_components.resume_state.snapshot import async_store_snapshot


class StoreStateButton(ButtonEntity):
    """Stores the current state of the entities in the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "store_state"
    _attr_unique_id = "button.store_home_state"
    _attr_icon = "mdi:home-import-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        async_store_snapshot(self.hass)
