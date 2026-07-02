"""Tests for the resumable package."""

from homeassistant.core import State

from custom_components.resume_state.resumable import build_resumable_entity
from custom_components.resume_state.resumable.resumable_fan import ResumableFan
from custom_components.resume_state.resumable.resumable_light import ResumableLight


def test_build_resumable_entity_unsupported_domain() -> None:
    """Test build_resumable_entity with an unsupported domain."""
    entity_id = "switch.test"
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
