"""The Resume State button entities."""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any

import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity
from homeassistant.components.light.const import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import State, split_entity_id
from homeassistant.helpers.dispatcher import async_dispatcher_send

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .config import CONF_ENTITIES
from .const import DOMAIN, SIGNAL_UPDATE_RESUME_STATE, SUPPORTED_DOMAINS
from .sensor import ResumeStatus

_LOGGER = logging.getLogger(__name__)

# Maps a light's recorded ``color_mode`` to the single attribute that should be
# replayed to ``light.turn_on``. Home Assistant exposes every color
# representation simultaneously (with ``None`` for the inactive ones, and even a
# derived ``rgb_color`` while in ``color_temp`` mode), but ``light.turn_on``
# rejects more than one color from its exclusive group, so we restore only the
# representation that was actually active.
COLOR_MODE_ATTR: dict[str, str] = {
    "color_temp": "color_temp_kelvin",
    "hs": "hs_color",
    "rgb": "rgb_color",
    "rgbw": "rgbw_color",
    "rgbww": "rgbww_color",
    "xy": "xy_color",
}


async def async_setup_platform(
    _hass: HomeAssistant,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Resume State button platform."""
    async_add_entities(
        [
            StoreStateButton(),
            ResumeStateButton(),
            ClearStateButton(),
        ]
    )


class StoreStateButton(ButtonEntity):
    """Stores the current state of the entities in the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "store_state"
    _attr_unique_id = "button.store_home_state"
    _attr_icon = "mdi:led-strip-variant"

    async def async_press(self) -> None:
        """Handle the button press."""
        pressed_at = dt_util.utcnow()
        _LOGGER.info("Storing state at %s", pressed_at)

        self.hass.data[DOMAIN]["pressed_at"] = pressed_at
        self.hass.data[DOMAIN]["status"] = ResumeStatus.STORED.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)


class ResumeStateButton(ButtonEntity):
    """Resumes the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "resume_state"
    _attr_unique_id = "button.resume_home_state"
    _attr_icon = "mdi:play-circle-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Begin resuming state")

        resume_at: datetime | None = self.hass.data[DOMAIN].get("pressed_at")
        if resume_at is None:
            _LOGGER.warning("Nothing to resume: no state has been stored")
            self._set_status(ResumeStatus.ERRORED)
            return

        filtered_entities_to_resume = self._filtered_entities()
        if not filtered_entities_to_resume:
            _LOGGER.warning("No entities to resume")
            self.hass.data[DOMAIN]["pressed_at"] = None
            self._set_status(ResumeStatus.CLEARED)
            return

        self._set_status(ResumeStatus.RESUMING)

        # Isolate failures per entity: one light failing to restore should not
        # abort the others, and the snapshot is always cleared afterwards so the
        # timestamp sensor and status sensor never disagree.
        had_error = False
        for entity_id in filtered_entities_to_resume:
            try:
                past_state = await self._async_historical_state(entity_id, resume_at)
                if past_state is None:
                    _LOGGER.info("Entity %s has no history at %s", entity_id, resume_at)
                    continue
                await self._handle_light(entity_id, past_state)
            except Exception:
                _LOGGER.exception("Failed to resume %s", entity_id)
                had_error = True

        self.hass.data[DOMAIN]["pressed_at"] = None
        self._set_status(ResumeStatus.ERRORED if had_error else ResumeStatus.CLEARED)

    def _set_status(self, status: ResumeStatus) -> None:
        """Update the stored status and notify the sensors."""
        self.hass.data[DOMAIN]["status"] = status.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)

    def _filtered_entities(self) -> list[str]:
        """Return configured entities whose domain is supported."""
        entities_to_resume: list[str] = self.hass.data[DOMAIN].get(CONF_ENTITIES, [])
        filtered: list[str] = []
        for entity_id in entities_to_resume:
            domain, _ = split_entity_id(entity_id)
            if domain in SUPPORTED_DOMAINS:
                filtered.append(entity_id)
            else:
                _LOGGER.warning(
                    "Domain %s not supported for entity %s", domain, entity_id
                )
        return filtered

    async def _async_historical_state(
        self, entity_id: str, resume_at: datetime
    ) -> State | None:
        """Fetch a single entity's recorded state as of resume_at."""
        # state_changes_during_period takes a single entity_id (not a list), and
        # no_attributes must be False so brightness/color/effect survive the lookup.
        # include_start_time_state returns the state as of resume_at for the
        # zero-width window.
        historical_states: dict[str, list[State]] = await get_instance(
            self.hass
        ).async_add_executor_job(
            partial(
                state_changes_during_period,
                self.hass,
                resume_at,
                resume_at,
                entity_id,
                no_attributes=False,
                include_start_time_state=True,
            )
        )
        history = historical_states.get(entity_id)
        if not history:
            return None
        return history[0]

    @staticmethod
    def _restore_attributes(past_state: State) -> dict[str, Any]:
        """
        Select the attributes to replay to light.turn_on for an 'on' state.

        Skips ``None`` values (Home Assistant exposes the full attribute set,
        using ``None`` for inactive ones) and includes only the single color
        attribute matching the recorded ``color_mode`` so the mutually
        exclusive color group in ``light.turn_on`` is never violated.
        """
        attrs: dict[str, Any] = {}
        for attr in ("brightness", "effect"):
            value = past_state.attributes.get(attr)
            if value is not None:
                attrs[attr] = value

        color_mode = past_state.attributes.get("color_mode")
        color_attr = (
            COLOR_MODE_ATTR.get(color_mode) if isinstance(color_mode, str) else None
        )
        if color_attr is not None:
            value = past_state.attributes.get(color_attr)
            if value is not None:
                attrs[color_attr] = value
        return attrs

    @staticmethod
    def _normalize(value: Any) -> Any:
        """Normalize a value for comparison (recorder lists vs live tuples)."""
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value

    async def _handle_light(self, entity_id: str, past_state: State) -> None:
        """Handle resuming the light with its previous attributes."""
        # Skip if the historical state was an error state
        if past_state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Skipping resume for %s: historical state was %s",
                entity_id,
                past_state.state,
            )
            return

        _LOGGER.info("Resuming state for %s to %s", entity_id, past_state.state)

        # Skip the service call if the light is already in the target state.
        current_state = self.hass.states.get(entity_id)

        if past_state.state == "off":
            if current_state and current_state.state == "off":
                _LOGGER.info("State for %s already matches", entity_id)
                return
            await self.hass.services.async_call(
                domain=LIGHT_DOMAIN,
                service="turn_off",
                service_data={"entity_id": entity_id},
                blocking=True,
            )
            return

        if past_state.state == "on":
            desired = self._restore_attributes(past_state)
            if (
                current_state
                and current_state.state == "on"
                and all(
                    self._normalize(current_state.attributes.get(attr))
                    == self._normalize(value)
                    for attr, value in desired.items()
                )
            ):
                _LOGGER.info("State and attributes for %s already match", entity_id)
                return

            service_data: dict[str, Any] = {"entity_id": entity_id, **desired}
            _LOGGER.debug(
                "Resuming light with service data for %s: %s", entity_id, service_data
            )
            await self.hass.services.async_call(
                domain=LIGHT_DOMAIN,
                service="turn_on",
                service_data=service_data,
                blocking=True,
            )
            return

        _LOGGER.warning(
            "Unhandled historical state %s for %s; skipping",
            past_state.state,
            entity_id,
        )


class ClearStateButton(ButtonEntity):
    """Clears the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear_state"
    _attr_unique_id = "button.clear_home_state"
    _attr_icon = "mdi:delete-outline"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Clearing State")
        self.hass.data[DOMAIN]["pressed_at"] = None
        self.hass.data[DOMAIN]["status"] = ResumeStatus.CLEARED.value
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_RESUME_STATE)
