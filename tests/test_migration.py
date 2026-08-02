"""Config entry migration v1 -> v2 (host-scoped unique IDs)."""

from unittest.mock import patch

from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.finna_library.api import FinnaData
from custom_components.finna_library.const import (
    CONF_HOST,
    CONF_PIN,
    CONF_USERNAME,
    DOMAIN,
)


async def test_migrate_v1_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HEILI0123",
        version=1,
        data={
            CONF_HOST: "heili.finna.fi",
            CONF_USERNAME: "HEILI0123",
            CONF_PIN: "0000",
        },
        unique_id="heili.finna.fi:heili0123",
    )
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)
    old = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "HEILI0123_loans",
        config_entry=entry,
        suggested_object_id="heili_heili0123_loans",
    )
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "HEILI0123")},
    )

    with patch(
        "custom_components.finna_library.FinnaClient.async_get_data",
        return_value=FinnaData(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.version == 2
    migrated = entity_registry.async_get(old.entity_id)
    assert migrated.unique_id == "heili.finna.fi:heili0123_loans"
    assert (
        device_registry.async_get_device(
            identifiers={(DOMAIN, "heili.finna.fi:heili0123")}
        )
        is not None
    )
    assert device_registry.async_get_device(identifiers={(DOMAIN, "HEILI0123")}) is None
