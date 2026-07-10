"""Tests for the Resume State config and options flows."""

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_component,
)

from custom_components.resume_state.const import CONF_ENTITIES, CONF_THROTTLE, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# The flows are resolved through the integration loader, which only scans
# custom_components when this fixture is active.
pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture(autouse=True)
def mock_recorder_dependency(hass: HomeAssistant) -> None:
    """Mark the recorder dependency as set up so entry setup skips it."""
    mock_component(hass, "recorder")


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Test the user flow stores entities and throttle in entry options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "custom_components.resume_state.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENTITIES: ["light.test_light"], CONF_THROTTLE: 5},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Resume State"
    assert result["data"] == {}
    assert result["options"] == {
        CONF_ENTITIES: ["light.test_light"],
        CONF_THROTTLE: 5,
    }
    mock_setup.assert_awaited_once()


async def test_user_flow_requires_entities(hass: HomeAssistant) -> None:
    """Test the user flow rejects an empty entity selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ENTITIES: [], CONF_THROTTLE: 0},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ENTITIES: "no_entities_selected"}


async def test_user_flow_single_instance(hass: HomeAssistant) -> None:
    """Test a second config entry is refused."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_options(hass: HomeAssistant) -> None:
    """Test the options flow rewrites the entry options and reloads."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Resume State",
        data={},
        options={CONF_ENTITIES: ["light.old"], CONF_THROTTLE: 0},
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.resume_state.async_setup_entry", return_value=True),
        patch("custom_components.resume_state.async_unload_entry", return_value=True),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_ENTITIES: ["light.new"], CONF_THROTTLE: 250},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_ENTITIES: ["light.new"], CONF_THROTTLE: 250}


async def test_options_flow_requires_entities(hass: HomeAssistant) -> None:
    """Test the options flow rejects an empty entity selection."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Resume State",
        data={},
        options={CONF_ENTITIES: ["light.old"], CONF_THROTTLE: 0},
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.resume_state.async_setup_entry", return_value=True),
        patch("custom_components.resume_state.async_unload_entry", return_value=True),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_ENTITIES: [], CONF_THROTTLE: 0},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ENTITIES: "no_entities_selected"}
