"""Config flow for Finna Library."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import FinnaAuthError, FinnaClient
from .const import CONF_HOST, CONF_PIN, CONF_USERNAME, DEFAULT_HOST, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PIN): str,
    }
)


def normalize_host(raw: str) -> str:
    """Accept 'vaski.finna.fi', a full URL, or one with a trailing slash."""
    host = raw.strip().lower()
    host = host.removeprefix("https://").removeprefix("http://")
    return host.split("/")[0]

REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PIN): str})


class FinnaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add a library card via the UI."""

    VERSION = 1

    async def _async_validate(
        self, username: str, pin: str, host: str
    ) -> str | None:
        """Try to log in; return an error key or None."""
        client = FinnaClient(
            async_create_clientsession(self.hass), username, pin, host
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
            host = normalize_host(user_input[CONF_HOST])
            if not host or "." not in host:
                errors["base"] = "invalid_host"
                return self.async_show_form(
                    step_id="user", data_schema=DATA_SCHEMA, errors=errors
                )
            await self.async_set_unique_id(f"{host}:{username.lower()}")
            self._abort_if_unique_id_configured()
            error = await self._async_validate(username, user_input[CONF_PIN], host)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"{username} ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: username,
                        CONF_PIN: user_input[CONF_PIN],
                    },
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
                entry.data[CONF_USERNAME],
                user_input[CONF_PIN],
                entry.data.get(CONF_HOST, DEFAULT_HOST),
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
