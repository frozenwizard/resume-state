"""Tests for the resumable package."""

from homeassistant.core import State

from custom_components.resume_state.resumable import build_resumable_entity


def test_build_resumable_entity_unsupported_domain() -> None:
    """Test build_resumable_entity with an unsupported domain."""
    entity_id = "switch.test"
    state = State(entity_id, "on")

    entity = build_resumable_entity(entity_id, state)

    assert entity is None
