"""Config flow for Heili Library."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import FinnaAuthError, FinnaClient
from .const import CONF_PIN, CONF_USERNAME, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PIN): str,
    }
)


class HeiliConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add a library card via the UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()
            client = FinnaClient(
                async_create_clientsession(self.hass), username, user_input[CONF_PIN]
            )
            try:
                await client.async_login()
            except FinnaAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=username,
                    data={CONF_USERNAME: username, CONF_PIN: user_input[CONF_PIN]},
                )
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
