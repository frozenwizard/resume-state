"""Config flow for the Resume State component."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import CONF_ENTITIES, CONF_THROTTLE, CONF_THROTTLE_DEFAULT, DOMAIN
from .resumable import SUPPORTED_DOMAINS

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

# Shared by the config and options flows: both edit the same two options.
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITIES): EntitySelector(
            EntitySelectorConfig(domain=sorted(SUPPORTED_DOMAINS), multiple=True)
        ),
        # Milliseconds to wait between resuming each entity. NumberSelector
        # emits a float, so coerce back to the int the resume loop expects.
        vol.Required(CONF_THROTTLE, default=CONF_THROTTLE_DEFAULT): vol.All(
            NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="ms",
                )
            ),
            vol.Coerce(int),
        ),
    }
)


class ResumeStateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Resume State config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_ENTITIES]:
                # Entities and throttle live in options (not data) so the
                # options flow can edit them later.
                return self.async_create_entry(
                    title="Resume State", data={}, options=user_input
                )
            errors[CONF_ENTITIES] = "no_entities_selected"

        return self.async_show_form(
            step_id="user", data_schema=OPTIONS_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(_config_entry: ConfigEntry) -> ResumeStateOptionsFlow:
        """Return the options flow handler."""
        return ResumeStateOptionsFlow()


class ResumeStateOptionsFlow(OptionsFlowWithReload):
    """Edit the configured entities and throttle; reloads the entry on save."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_ENTITIES]:
                return self.async_create_entry(data=user_input)
            errors[CONF_ENTITIES] = "no_entities_selected"

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
            errors=errors,
        )
