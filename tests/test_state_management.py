"""Tests for the Resume State state management."""

from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from custom_components.resume_state.button import ClearStateButton, StoreStateButton
from custom_components.resume_state.const import DOMAIN
from custom_components.resume_state.sensor import (
    ResumeStateSensor,
    ResumeStatus,
    ResumeStatusSensor,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_store_and_clear_state(hass: HomeAssistant) -> None:
    """Test storing the state, checking the sensor, and clearing it."""
    # Initialize the data structure as the setup would
    hass.data[DOMAIN] = {"pressed_at": None, "status": ResumeStatus.IDLE.value}

    # Instantiate the components, ensuring they share the same hass instance
    sensor = ResumeStateSensor()
    sensor.hass = hass

    status_sensor = ResumeStatusSensor()
    status_sensor.hass = hass

    store_button = StoreStateButton()
    store_button.hass = hass

    clear_button = ClearStateButton()
    clear_button.hass = hass

    # 1. Initial state check
    assert sensor.native_value is None
    assert status_sensor.native_value == ResumeStatus.IDLE.value

    # 2. Store the state
    await store_button.async_press()

    # 3. Check the sensors have updated
    stored_timestamp = hass.data[DOMAIN]["pressed_at"]
    assert stored_timestamp is not None
    assert status_sensor.native_value == ResumeStatus.STORED.value

    # We can also verify it's in the hass.data directly
    assert sensor.native_value == stored_timestamp

    # 4. Clear the state
    await clear_button.async_press()

    # 5. Check the sensors are cleared
    assert sensor.native_value is None
    assert status_sensor.native_value == ResumeStatus.IDLE.value
    assert hass.data[DOMAIN]["pressed_at"] is None


async def test_store_while_disabled_keeps_disabled_status(hass: HomeAssistant) -> None:
    """Storing while disabled records the timestamp but keeps the status DISABLED."""
    hass.data[DOMAIN] = {
        "pressed_at": None,
        "status": ResumeStatus.DISABLED.value,
        "enabled": False,
    }

    store_button = StoreStateButton()
    store_button.hass = hass

    await store_button.async_press()

    # Storing the snapshot is still allowed...
    assert hass.data[DOMAIN]["pressed_at"] is not None
    # ...but the status must not change away from DISABLED.
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value


async def test_clear_while_disabled_keeps_disabled_status(hass: HomeAssistant) -> None:
    """Clearing while disabled clears the timestamp but keeps the status DISABLED."""
    hass.data[DOMAIN] = {
        "pressed_at": dt_util.utcnow(),
        "status": ResumeStatus.DISABLED.value,
        "enabled": False,
    }

    clear_button = ClearStateButton()
    clear_button.hass = hass

    await clear_button.async_press()

    # Clearing the snapshot is still allowed...
    assert hass.data[DOMAIN]["pressed_at"] is None
    # ...but the status must not change away from DISABLED.
    assert hass.data[DOMAIN]["status"] == ResumeStatus.DISABLED.value
