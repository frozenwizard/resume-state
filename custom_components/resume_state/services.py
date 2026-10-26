"""The Resume State service actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.core import callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from custom_components.resume_state.const import (
    ATTR_DATETIME,
    DOMAIN,
    SERVICE_CLEAR,
    SERVICE_RESUME,
    SERVICE_STORE,
)
from custom_components.resume_state.snapshot import (
    async_clear_snapshot,
    async_resume_snapshot,
    async_store_snapshot,
)

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant, ServiceCall

# Rejects any data, so a misplaced field fails loudly instead of being ignored.
NO_FIELDS_SCHEMA = vol.Schema({})
RESUME_SCHEMA = vol.Schema({vol.Optional(ATTR_DATETIME): cv.datetime})


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the store, resume and clear service actions."""
    hass.services.async_register(
        DOMAIN, SERVICE_STORE, _async_handle_store, schema=NO_FIELDS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESUME, _async_handle_resume, schema=RESUME_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR, _async_handle_clear, schema=NO_FIELDS_SCHEMA
    )


@callback
def _async_handle_store(call: ServiceCall) -> None:
    """Handle the store service action."""
    _async_ensure_loaded(call.hass)
    async_store_snapshot(call.hass)


async def _async_handle_resume(call: ServiceCall) -> None:
    """Handle the resume service action."""
    _async_ensure_loaded(call.hass)

    resume_at: datetime | None = call.data.get(ATTR_DATETIME)
    if resume_at is not None:
        # A datetime without an offset (as the UI sends) is in HA's time zone.
        resume_at = dt_util.as_utc(resume_at)
        if resume_at > dt_util.utcnow():
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="datetime_in_future"
            )

    await async_resume_snapshot(call.hass, resume_at)


@callback
def _async_handle_clear(call: ServiceCall) -> None:
    """Handle the clear service action."""
    _async_ensure_loaded(call.hass)
    async_clear_snapshot(call.hass)


@callback
def _async_ensure_loaded(hass: HomeAssistant) -> None:
    """Raise unless the config entry holding the snapshot state is loaded."""
    # The actions are registered for the integration's lifetime, but the
    # snapshot state only exists while the config entry is loaded.
    if DOMAIN not in hass.data:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="not_loaded"
        )
