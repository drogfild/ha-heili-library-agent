"""Shared base entity: one device per library card."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HeiliCoordinator
from .const import DOMAIN


class HeiliEntity(CoordinatorEntity[HeiliCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeiliCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.username}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.username)},
            name=f"Heili {coordinator.username}",
            manufacturer="Heili-kirjastot",
            model="Finna account",
            configuration_url="https://heili.finna.fi/MyResearch/CheckedOut",
        )
