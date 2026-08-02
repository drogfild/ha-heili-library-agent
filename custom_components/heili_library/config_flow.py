"""Config flow for Heili Library."""

from __future__ import annotations

from collections.abc import Mapping
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

REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PIN): str})


class HeiliConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add a library card via the UI."""

    VERSION = 1

    async def _async_validate(self, username: str, pin: str) -> str | None:
        """Try to log in; return an error key or None."""
        client = FinnaClient(
            async_create_clientsession(self.hass), username, pin
        )
        try:
            await client.async_login()
        except FinnaAuthError:
            return "invalid_auth"
        except Exception:  # noqa: BLE001
            return "cannot_connect"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()
            error = await self._async_validate(username, user_input[CONF_PIN])
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=username,
                    data={CONF_USERNAME: username, CONF_PIN: user_input[CONF_PIN]},
                )
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Triggered when the PIN stops working (ConfigEntryAuthFailed)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            error = await self._async_validate(
                entry.data[CONF_USERNAME], user_input[CONF_PIN]
            )
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_PIN: user_input[CONF_PIN]},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
        )
