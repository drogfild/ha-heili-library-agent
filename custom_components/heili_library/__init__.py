"""Heili Library (heili.finna.fi) integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FinnaAuthError, FinnaClient, FinnaData, FinnaError
from .const import CONF_PIN, CONF_USERNAME, DOMAIN, UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button", "calendar"]

type HeiliConfigEntry = ConfigEntry[HeiliCoordinator]


class HeiliCoordinator(DataUpdateCoordinator[FinnaData]):
    """Fetches account data from Finna for one library card."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.data[CONF_USERNAME]}",
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        # Own cookie jar per card so multiple accounts don't share a session.
        session = async_create_clientsession(hass)
        self.client = FinnaClient(
            session, entry.data[CONF_USERNAME], entry.data[CONF_PIN]
        )
        self.username: str = entry.data[CONF_USERNAME]

    async def _async_update_data(self) -> FinnaData:
        try:
            return await self.client.async_get_data()
        except FinnaAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except FinnaError as err:
            raise UpdateFailed(err) from err
        except Exception as err:  # noqa: BLE001 - network errors from aiohttp
            raise UpdateFailed(err) from err


async def async_setup_entry(hass: HomeAssistant, entry: HeiliConfigEntry) -> bool:
    coordinator = HeiliCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HeiliConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
