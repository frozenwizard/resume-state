"""Configuration for the Resume State component."""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN

CONF_ENTITIES = "entities"
CONF_DELAY = "delay"
CONF_DELAY_DEFAULT = 0
CONF_ENTITIES_DEFAULT: list[str] = []

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # Expects a list of strings, validates they look like entity IDs
                vol.Required(CONF_ENTITIES): cv.entity_ids,
                # Expects an integer, defaults to 0 if missing
                vol.Optional(CONF_DELAY, default=CONF_DELAY_DEFAULT): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
