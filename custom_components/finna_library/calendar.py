"""Calendar of loan due dates."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FinnaConfigEntry, FinnaCoordinator
from .entity import FinnaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FinnaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([DueDateCalendar(entry.runtime_data)])


class DueDateCalendar(FinnaEntity, CalendarEntity):
    _attr_translation_key = "due_dates"

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "due_dates")

    def _events(self) -> list[CalendarEvent]:
        events = []
        for loan in self.coordinator.data.loans:
            if loan.due_date is None:
                continue
            summary = f"Eräpäivä: {loan.title or '?'}"
            if loan.author:
                summary += f" ({loan.author})"
            events.append(
                CalendarEvent(
                    start=loan.due_date,
                    end=loan.due_date + timedelta(days=1),
                    summary=summary,
                )
            )
        return sorted(events, key=lambda e: e.start)

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        upcoming = [e for e in self._events() if e.end_datetime_local.date() > today]
        return upcoming[0] if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            e
            for e in self._events()
            if e.start_datetime_local < end_date and e.end_datetime_local > start_date
        ]
