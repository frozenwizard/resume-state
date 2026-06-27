"""Resume State button entity."""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import State, split_entity_id
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.resume_state.config import CONF_ENTITIES
from custom_components.resume_state.const import (
    DOMAIN,
    SIGNAL_UPDATE_RESUME_STATE,
    SUPPORTED_DOMAINS,
)
from custom_components.resume_state.resumable import build_resumable_entity
from custom_components.resume_state.sensor import ResumeStatus

if TYPE_CHECKING:
    from datetime import datetime

    from custom_components.resume_state.resumable import ResumableEntity

_LOGGER = logging.getLogger(__name__)


class ResumeStateButton(ButtonEntity):
    """Resumes the state of the entities from the `resume_state` data."""

    _attr_has_entity_name = True
    _attr_translation_key = "resume_state"
    _attr_unique_id = "button.resume_home_state"
    _attr_icon = "mdi:home-clock"

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

        # Isolate failures per entity: one entity failing to restore should not
        # abort the others, and the snapshot is always cleared afterwards so the
        # timestamp sensor and status sensor never disagree.
        had_error = False
        for entity_id in filtered_entities_to_resume:
            try:
                past_state = await self._async_historical_state(entity_id, resume_at)
                if past_state is None:
                    _LOGGER.info("Entity %s has no history at %s", entity_id, resume_at)
                    continue
                resumable_entity: ResumableEntity | None = build_resumable_entity(
                    self.hass, entity_id, past_state
                )
                if resumable_entity is None:
                    _LOGGER.warning("Entity %s is not yet supported", entity_id)
                    continue
                await resumable_entity.resume()

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
