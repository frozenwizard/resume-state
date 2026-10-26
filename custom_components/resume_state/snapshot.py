"""Store, resume and clear the Resume State snapshot."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING

import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import Context, State, callback, split_entity_id
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.resume_state.const import (
    CONF_ENTITIES,
    CONF_THROTTLE,
    CONF_THROTTLE_DEFAULT,
    DOMAIN,
    SIGNAL_UPDATE_RESUME_STATE,
)
from custom_components.resume_state.resumable import (
    SUPPORTED_DOMAINS,
    build_resumable_entity,
)
from custom_components.resume_state.sensor import ResumeStatus

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from custom_components.resume_state.resumable import ResumableEntity

_LOGGER = logging.getLogger(__name__)


@callback
def async_store_snapshot(hass: HomeAssistant) -> None:
    """Mark the current moment as the snapshot to resume to."""
    pressed_at = dt_util.utcnow()
    _LOGGER.debug("Storing state at %s", pressed_at)

    hass.data[DOMAIN]["pressed_at"] = pressed_at
    # Storing the snapshot is allowed while disabled
    if hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
        hass.data[DOMAIN]["status"] = ResumeStatus.STORED.value
    async_dispatcher_send(hass, SIGNAL_UPDATE_RESUME_STATE)


@callback
def async_clear_snapshot(hass: HomeAssistant) -> None:
    """Discard the stored snapshot."""
    _LOGGER.debug("Clearing state")
    hass.data[DOMAIN]["pressed_at"] = None
    # Clearing the snapshot is allowed while disabled
    if hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
        hass.data[DOMAIN]["status"] = ResumeStatus.IDLE.value
    async_dispatcher_send(hass, SIGNAL_UPDATE_RESUME_STATE)


async def async_resume_snapshot(
    hass: HomeAssistant, resume_at: datetime | None = None
) -> None:
    """
    Restore each configured entity to its state at the snapshot instant.

    Passing ``resume_at`` restores to that instant instead and leaves any
    stored snapshot in place; otherwise the stored snapshot is consumed.
    """
    _LOGGER.debug("Resuming state")

    if not hass.data[DOMAIN].get("enabled", True):
        _LOGGER.warning("Resume state is disabled, skip resuming state")
        _async_set_status(hass, ResumeStatus.DISABLED)
        return

    # An explicit instant overrides the stored snapshot for this resume only.
    consume_snapshot = resume_at is None
    if resume_at is None:
        resume_at = hass.data[DOMAIN].get("pressed_at")
    if resume_at is None:
        _LOGGER.warning("Nothing to resume: no state has been stored")
        _async_set_status(hass, ResumeStatus.ERRORED)
        return

    filtered_entities_to_resume = _filtered_entities(hass)
    if not filtered_entities_to_resume:
        _LOGGER.warning("No entities to resume")
        if consume_snapshot:
            hass.data[DOMAIN]["pressed_at"] = None
        _async_set_status(hass, ResumeStatus.ERRORED)
        return

    _async_set_status(hass, ResumeStatus.RESUMING)

    # Milliseconds to wait after resuming each entity.
    throttle_ms: int = hass.data[DOMAIN].get(CONF_THROTTLE, CONF_THROTTLE_DEFAULT)

    # Restore state as the 'Resume State' user.
    user_id: str = hass.data[DOMAIN].get("user_id")

    # Isolate failures per entity: one entity failing to restore should not
    # abort the others, and a consumed snapshot is always cleared afterwards
    # so the timestamp sensor and status sensor never disagree.
    had_error = False
    for entity_id in filtered_entities_to_resume:
        try:
            past_state = await _async_historical_state(hass, entity_id, resume_at)
            if past_state is None:
                _LOGGER.warning(
                    "Entity %s has no history at %s; skipping", entity_id, resume_at
                )
                continue
            resumable_entity: ResumableEntity | None = build_resumable_entity(
                entity_id, past_state
            )
            if resumable_entity is None:
                _LOGGER.warning("Entity %s is not yet supported", entity_id)
                continue

            # A fresh context per entity keeps each restore an independent,
            # attributed logbook entry instead of one grouped action.
            context = Context(user_id=user_id)
            await resumable_entity.resume(hass, context)
            await asyncio.sleep(throttle_ms / 1000)

        except Exception:
            _LOGGER.exception("Failed to resume %s", entity_id)
            had_error = True

    if consume_snapshot:
        hass.data[DOMAIN]["pressed_at"] = None
    _async_set_status(hass, _settled_status(hass, had_error=had_error))


def _settled_status(hass: HomeAssistant, *, had_error: bool) -> ResumeStatus:
    """Return the status to settle on once a resume has run."""
    if had_error:
        return ResumeStatus.ERRORED
    if hass.data[DOMAIN].get("pressed_at") is not None:
        # An explicit resume_at left the stored snapshot ready to resume.
        return ResumeStatus.STORED
    return ResumeStatus.IDLE


@callback
def _async_set_status(hass: HomeAssistant, status: ResumeStatus) -> None:
    """Update the stored status and notify the sensors."""
    hass.data[DOMAIN]["status"] = status.value
    async_dispatcher_send(hass, SIGNAL_UPDATE_RESUME_STATE)


def _filtered_entities(hass: HomeAssistant) -> list[str]:
    """Return configured entities whose domain is supported."""
    entities_to_resume: list[str] = hass.data[DOMAIN].get(CONF_ENTITIES, [])
    filtered: list[str] = []
    for entity_id in entities_to_resume:
        domain, _ = split_entity_id(entity_id)
        if domain in SUPPORTED_DOMAINS:
            filtered.append(entity_id)
        else:
            _LOGGER.warning("Domain %s not supported for entity %s", domain, entity_id)
    return filtered


async def _async_historical_state(
    hass: HomeAssistant, entity_id: str, resume_at: datetime
) -> State | None:
    """Fetch a single entity's recorded state as of resume_at."""
    # state_changes_during_period takes a single entity_id (not a list), and
    # no_attributes must be False so brightness/color/effect survive the lookup.
    # include_start_time_state returns the state as of resume_at for the
    # zero-width window.
    historical_states: dict[str, list[State]] = await get_instance(
        hass
    ).async_add_executor_job(
        partial(
            state_changes_during_period,
            hass,
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
