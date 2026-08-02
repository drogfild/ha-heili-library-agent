"""Sensors: loans, next due date, fines, holds."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FinnaConfigEntry, FinnaCoordinator
from .entity import FinnaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FinnaConfigEntry,
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
            LoansThisYearSensor(coordinator),
            SavedSearchesSensor(coordinator),
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


class LoansSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "loans"
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "loans")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.loans)

    @property
    def extra_state_attributes(self) -> dict:
        return {"loans": [_loan_attr(l) for l in self.coordinator.data.loans]}


class NextDueDateSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "next_due_date"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "next_due_date")

    @property
    def native_value(self):
        return self.coordinator.data.next_due_date


class FinesSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "fines"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "fines")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.fines_total


class HoldsSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "holds"
    _attr_icon = "mdi:book-clock"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "holds")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.holds)

    @property
    def extra_state_attributes(self) -> dict:
        return {"holds": [_hold_attr(h) for h in self.coordinator.data.holds]}


class LoansThisYearSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "loans_this_year"
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "loans_this_year")

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.loans_this_year

    @property
    def extra_state_attributes(self) -> dict:
        return {"history_total": self.coordinator.data.history_total}


class SavedSearchesSensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "saved_searches"
    _attr_icon = "mdi:magnify-plus"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "saved_searches")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.saved_searches)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "searches": [
                {
                    "query": s.query,
                    "url": s.url,
                    "results": s.results,
                    "new_results": s.new_results,
                }
                for s in self.coordinator.data.saved_searches
            ],
            "new_results_total": sum(
                s.new_results for s in self.coordinator.data.saved_searches
            ),
        }


class HoldsReadySensor(FinnaEntity, SensorEntity):
    _attr_translation_key = "holds_ready"
    _attr_icon = "mdi:book-check"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "holds_ready")

    @property
    def native_value(self) -> int:
        return sum(1 for h in self.coordinator.data.holds if h.available)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "holds": [_hold_attr(h) for h in self.coordinator.data.holds if h.available]
        }
