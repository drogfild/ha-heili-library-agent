"""Sensors: loans, next due date, fines, holds."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HeiliConfigEntry, HeiliCoordinator
from .entity import HeiliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeiliConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            LoansSensor(coordinator),
            NextDueDateSensor(coordinator),
            FinesSensor(coordinator),
            HoldsSensor(coordinator),
            HoldsReadySensor(coordinator),
        ]
    )


def _loan_attr(loan) -> dict:
    return {
        "title": loan.title,
        "author": loan.author,
        "due_date": loan.due_date.isoformat() if loan.due_date else None,
        "renewable": loan.renewable,
    }


def _hold_attr(hold) -> dict:
    return {
        "title": hold.title,
        "available": hold.available,
        "in_transit": hold.in_transit,
        "pickup_location": hold.pickup_location,
        "queue_position": hold.queue_position,
        "expires": hold.expires.isoformat() if hold.expires else None,
    }


class LoansSensor(HeiliEntity, SensorEntity):
    _attr_translation_key = "loans"
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: HeiliCoordinator) -> None:
        super().__init__(coordinator, "loans")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.loans)

    @property
    def extra_state_attributes(self) -> dict:
        return {"loans": [_loan_attr(l) for l in self.coordinator.data.loans]}


class NextDueDateSensor(HeiliEntity, SensorEntity):
    _attr_translation_key = "next_due_date"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: HeiliCoordinator) -> None:
        super().__init__(coordinator, "next_due_date")

    @property
    def native_value(self):
        return self.coordinator.data.next_due_date


class FinesSensor(HeiliEntity, SensorEntity):
    _attr_translation_key = "fines"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator: HeiliCoordinator) -> None:
        super().__init__(coordinator, "fines")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.fines_total


class HoldsSensor(HeiliEntity, SensorEntity):
    _attr_translation_key = "holds"
    _attr_icon = "mdi:book-clock"

    def __init__(self, coordinator: HeiliCoordinator) -> None:
        super().__init__(coordinator, "holds")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.holds)

    @property
    def extra_state_attributes(self) -> dict:
        return {"holds": [_hold_attr(h) for h in self.coordinator.data.holds]}


class HoldsReadySensor(HeiliEntity, SensorEntity):
    _attr_translation_key = "holds_ready"
    _attr_icon = "mdi:book-check"

    def __init__(self, coordinator: HeiliCoordinator) -> None:
        super().__init__(coordinator, "holds_ready")

    @property
    def native_value(self) -> int:
        return sum(1 for h in self.coordinator.data.holds if h.available)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "holds": [_hold_attr(h) for h in self.coordinator.data.holds if h.available]
        }
