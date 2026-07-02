"""Resumable light entity."""

from typing import Any, ClassVar

from homeassistant.components.light.const import DOMAIN as LIGHT_DOMAIN

from custom_components.resume_state.resumable.resumable_toggle import ResumableToggle

# The single color attribute to replay to light.turn_on for each color_mode.
# HA reports every color representation at once, but turn_on accepts only one,
# so we restore just the one matching the recorded color_mode.
COLOR_MODE_ATTR: dict[str, str] = {
    "color_temp": "color_temp_kelvin",
    "hs": "hs_color",
    "rgb": "rgb_color",
    "rgbw": "rgbw_color",
    "rgbww": "rgbww_color",
    "xy": "xy_color",
}


class ResumableLight(ResumableToggle):
    """A light entity that is resumable."""

    domain: ClassVar[str] = LIGHT_DOMAIN

    def _restore_attributes(self) -> dict[str, Any]:
        """
        Select the attributes to replay to light.turn_on for an 'on' state.

        Skips ``None`` values (Home Assistant exposes the full attribute set,
        using ``None`` for inactive ones) and includes only the single color
        attribute matching the recorded ``color_mode`` so the mutually
        exclusive color group in ``light.turn_on`` is never violated.
        """
        attrs: dict[str, Any] = {}
        for attr in ("brightness", "effect"):
            value = self.previous_state.attributes.get(attr)
            if value is not None:
                attrs[attr] = value

        color_mode = self.previous_state.attributes.get("color_mode")
        color_attr = (
            COLOR_MODE_ATTR.get(color_mode) if isinstance(color_mode, str) else None
        )
        if color_attr is not None:
            value = self.previous_state.attributes.get(color_attr)
            if value is not None:
                attrs[color_attr] = value
        return attrs
