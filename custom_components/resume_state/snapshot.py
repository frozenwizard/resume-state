"""Store, resume and clear the Resume State snapshot."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING, Any

import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import Context, State, callback, split_entity_id
from homeassistant.exceptions import ServiceValidationError
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
    async_ensure_not_resuming(hass)
    pressed_at = dt_util.utcnow()
    _LOGGER.debug("Storing state at %s", pressed_at)

    hass.data[DOMAIN]["pressed_at"] = pressed_at
    # Storing the snapshot is allowed while disabled
    if hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
        hass.data[DOMAIN]["status"] = ResumeStatus.STORED.value
    async_dispatcher_send(hass, SIGNAL_UPDATE_RESUME_STATE)


@callback
def async_clear_snapshot(hass: HomeAssistant) -> None:
    """Discard the stored snapshot, aborting any resume in progress."""
    _LOGGER.debug("Clearing state")
    # Clear is the way out of a resume that is stuck or taking too long.
    async_abort_resume(hass)
    hass.data[DOMAIN]["pressed_at"] = None
    # Clearing the snapshot is allowed while disabled
    if hass.data[DOMAIN].get("status") != ResumeStatus.DISABLED.value:
        hass.data[DOMAIN]["status"] = ResumeStatus.IDLE.value
    async_dispatcher_send(hass, SIGNAL_UPDATE_RESUME_STATE)


@callback
def async_abort_resume(hass: HomeAssistant) -> None:
    """Cancel any resume in progress and stop it from settling the snapshot."""
    # A resume only settles while it still owns resume_task, so taking it away
    # leaves the snapshot and status to whoever aborted it.
    resume_task = _running_resume(hass)
    hass.data[DOMAIN].pop("resume_task", None)
    if resume_task is not None:
        _LOGGER.warning("Aborting the resume in progress")
        resume_task.cancel()


@callback
def async_ensure_not_resuming(hass: HomeAssistant) -> None:
    """Raise while a resume is in progress, which only Clear may interrupt."""
    if async_is_resuming(hass):
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="resume_in_progress"
        )


@callback
def async_is_resuming(hass: HomeAssistant) -> bool:
    """Return whether a resume is in progress."""
    return _running_resume(hass) is not None


@callback
def _running_resume(hass: HomeAssistant) -> asyncio.Task[None] | None:
    """Return the resume in progress, if any."""
    # The live task, not the RESUMING status, is what marks a resume as running.
    resume_task: asyncio.Task[None] | None = hass.data[DOMAIN].get("resume_task")
    if resume_task is None or resume_task.done():
        return None
    return resume_task


async def async_resume_snapshot(
    hass: HomeAssistant,
    resume_at: datetime | None = None,
    *,
    parent_context: Context | None = None,
) -> None:
    """
    Restore each configured entity to its state at the snapshot instant.

    Passing ``resume_at`` restores to that instant instead of the stored
    snapshot. Either way the stored snapshot is consumed, so nothing is stored
    once a resume has run.
    ``parent_context`` is the context of whatever triggered the resume (a
    button press or action call) and becomes the parent of each restore.
    Only one resume runs at a time, and Clear aborts one in progress.
    """
    _LOGGER.debug("Resuming state")
    async_ensure_not_resuming(hass)

    if not hass.data[DOMAIN].get("enabled", True):
        _LOGGER.warning("Resume state is disabled, skip resuming state")
        _async_set_status(hass, ResumeStatus.DISABLED)
        return

    stored_at: datetime | None = hass.data[DOMAIN].get("pressed_at")
    # An explicit instant (the resume action's datetime) replaces the stored
    # snapshot, which the resume then gives up.
    discarding = stored_at if resume_at is not None else None
    if resume_at is None:
        resume_at = stored_at
    if resume_at is None:
        _LOGGER.warning("Nothing to resume: no state has been stored")
        _async_set_status(hass, ResumeStatus.ERRORED)
        return

    filtered_entities_to_resume = _filtered_entities(hass)
    if not filtered_entities_to_resume:
        _LOGGER.warning("No entities to resume")
        _warn_if_discarding(resume_at, discarding)
        hass.data[DOMAIN]["pressed_at"] = None
        _async_set_status(hass, ResumeStatus.ERRORED)
        return

    # The restores run as their own task so Clear can abort them without
    # cancelling the caller. As a background task, shutdown cancels it rather
    # than waiting on it. It isn't started eagerly, so it is registered, and
    # RESUMING shown, before any of it runs.
    restore = hass.async_create_background_task(
        _async_restore(
            hass,
            filtered_entities_to_resume,
            resume_at,
            discarding=discarding,
            parent_context=parent_context,
        ),
        "resume_state_restore",
        eager_start=False,
    )
    hass.data[DOMAIN]["resume_task"] = restore
    _async_set_status(hass, ResumeStatus.RESUMING)
    try:
        await asyncio.wait([restore])
    except asyncio.CancelledError:
        # Stopping the caller (e.g. a restarted automation or a stopped script)
        # stops its resume too, settled now so the caller's next run isn't
        # locked out while the restore unwinds.
        restore.cancel()
        _async_settle(hass, restore, resume_at, discarding, had_error=True)
        raise
    if not restore.cancelled():
        # Surface anything unexpected; an abort by Clear is not an error.
        restore.result()


async def _async_restore(
    hass: HomeAssistant,
    entity_ids: list[str],
    resume_at: datetime,
    *,
    discarding: datetime | None,
    parent_context: Context | None,
) -> None:
    """
    Restore each entity to its state at resume_at, then settle the snapshot.

    ``discarding`` is the stored snapshot given up for an explicit
    ``resume_at``, if any.
    """
    # Anything that ends the restores early, short of an abort, is an error.
    had_error = True
    try:
        had_error = await _async_restore_entities(
            hass, entity_ids, resume_at, parent_context
        )
    finally:
        _async_settle(
            hass, asyncio.current_task(), resume_at, discarding, had_error=had_error
        )


@callback
def _async_settle(
    hass: HomeAssistant,
    restore_task: asyncio.Task[Any] | None,
    resume_at: datetime,
    discarding: datetime | None,
    *,
    had_error: bool,
) -> None:
    """Consume the snapshot and settle the status once a resume has ended."""
    # Only a resume that still owns resume_task settles: an abort or an entry
    # reload has handed the snapshot and status to someone else.
    data = hass.data.get(DOMAIN)
    if data is None or data.get("resume_task") is not restore_task:
        return
    del data["resume_task"]
    if had_error:
        _warn_if_discarding(resume_at, discarding)
    data["pressed_at"] = None
    _async_set_status(hass, ResumeStatus.ERRORED if had_error else ResumeStatus.IDLE)


async def _async_restore_entities(
    hass: HomeAssistant,
    entity_ids: list[str],
    resume_at: datetime,
    parent_context: Context | None,
) -> bool:
    """Restore each entity to its state at resume_at; return whether any failed."""
    # Milliseconds to wait after resuming each entity.
    throttle_ms: int = hass.data[DOMAIN].get(CONF_THROTTLE, CONF_THROTTLE_DEFAULT)

    # Restore state as the 'Resume State' user.
    user_id: str = hass.data[DOMAIN].get("user_id")

    # Isolate failures per entity: one entity failing to restore should not
    # abort the others.
    had_error = False
    for entity_id in entity_ids:
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
            # attributed logbook entry instead of one grouped action; the
            # parent links it back to the automation or user that resumed.
            context = Context(
                user_id=user_id,
                parent_id=parent_context.id if parent_context else None,
            )
            await resumable_entity.resume(hass, context)
            await asyncio.sleep(throttle_ms / 1000)

        except Exception:
            _LOGGER.exception("Failed to resume %s", entity_id)
            had_error = True
    return had_error


def _warn_if_discarding(resume_at: datetime, discarding: datetime | None) -> None:
    """Log the stored snapshot a failed explicit resume gives up."""
    # It can't be recovered from anywhere else once it is cleared.
    if discarding is not None:
        _LOGGER.warning(
            "Resume to %s failed; discarding the snapshot stored at %s",
            resume_at,
            discarding,
        )


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
