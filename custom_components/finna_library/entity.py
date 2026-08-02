"""Shared base entity: one device per library card."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FinnaCoordinator
from .const import DOMAIN


class FinnaEntity(CoordinatorEntity[FinnaCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FinnaCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.username}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.username)},
            name=f"{coordinator.host.split('.')[0].capitalize()} {coordinator.username}",
            manufacturer="Finna",
            model="Finna account",
            configuration_url=f"{coordinator.client.base_url}/MyResearch/CheckedOut",
        )
