"""Tests for the resumable package."""

from homeassistant.core import State

from custom_components.resume_state.resumable import build_resumable_entity
from custom_components.resume_state.resumable.resumable_fan import ResumableFan
from custom_components.resume_state.resumable.resumable_input_boolean import (
    ResumableInputBoolean,
)
from custom_components.resume_state.resumable.resumable_input_select import (
    ResumableInputSelect,
)
from custom_components.resume_state.resumable.resumable_light import ResumableLight
from custom_components.resume_state.resumable.resumable_select import ResumableSelect
from custom_components.resume_state.resumable.resumable_switch import ResumableSwitch


def test_build_resumable_entity_unsupported_domain() -> None:
    """Test build_resumable_entity with an unsupported domain."""
    entity_id = "climate.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert entity is None


def test_build_resumable_entity_light() -> None:
    """Test build_resumable_entity with a light."""
    entity_id = "light.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableLight)


def test_build_resumable_entity_fan() -> None:
    """Test build_resumable_entity with a fan."""
    entity_id = "fan.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableFan)


def test_build_resumable_entity_switch() -> None:
    """Test build_resumable_entity with a switch."""
    entity_id = "switch.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableSwitch)


def test_build_resumable_entity_input_boolean() -> None:
    """Test build_resumable_entity with an input boolean."""
    entity_id = "input_boolean.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableInputBoolean)


def test_build_resumable_entity_select() -> None:
    """Test build_resumable_entity with a select."""
    entity_id = "select.test"
    state = State(entity_id, "cool")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableSelect)


def test_build_resumable_entity_input_select() -> None:
    """Test build_resumable_entity with an input select."""
    entity_id = "input_select.test"
    state = State(entity_id, "cool")

    entity = build_resumable_entity(entity_id, state)

    assert isinstance(entity, ResumableInputSelect)
