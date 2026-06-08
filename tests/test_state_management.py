"""Tests for the Resume State state management."""

from unittest.mock import MagicMock

import pytest

from custom_components.resume_state.button import ClearStateButton, StoreStateButton
from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.sensor import ResumeStateSensor


@pytest.mark.asyncio
async def test_store_and_clear_state() -> None:
    """Test storing the state, checking the sensor, and clearing it."""
    hass = MagicMock()
    # Initialize the data structure as the setup would
    hass.data = {DOMAIN: {"pressed_at": None}}

    # Instantiate the components
    sensor = ResumeStateSensor()
    sensor.hass = hass

    store_button = StoreStateButton()
    store_button.hass = hass

    clear_button = ClearStateButton()
    clear_button.hass = hass

    # 1. Initial state check
    assert sensor.native_value is None

    # 2. Store the state
    await store_button.async_press()

    # 3. Check the sensor has updated to a timestamp
    stored_timestamp = sensor.native_value
    assert stored_timestamp is not None
    # We can also verify it's in the hass.data directly
    assert hass.data[DOMAIN]["pressed_at"] == stored_timestamp

    # 4. Clear the state
    await clear_button.async_press()

    # 5. Check the sensor is cleared
    assert sensor.native_value is None
    assert hass.data[DOMAIN]["pressed_at"] is None
