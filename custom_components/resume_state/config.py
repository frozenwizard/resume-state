"""Configuration for the Resume State component."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN

CONF_ENTITIES = "entities"
CONF_THROTTLE = "throttle"
CONF_THROTTLE_DEFAULT = 0
CONF_ENTITIES_DEFAULT: list[str] = []

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # Expects a list of strings, validates they look like entity IDs
                vol.Required(CONF_ENTITIES): cv.entity_ids,
                # Milliseconds to wait between resuming each entity; defaults to 0
                vol.Optional(
                    CONF_THROTTLE, default=CONF_THROTTLE_DEFAULT
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
