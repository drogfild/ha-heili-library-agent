"""Read-only todo list of current loans (shows titles in the more-info dialog)."""

from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FinnaConfigEntry, FinnaCoordinator
from .entity import FinnaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FinnaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([LoansTodoList(entry.runtime_data)])


class LoansTodoList(FinnaEntity, TodoListEntity):
    _attr_translation_key = "loaned_books"
    _attr_icon = "mdi:bookshelf"
    # No TodoListEntityFeature flags: the list can't be edited from the UI.

    def __init__(self, coordinator: FinnaCoordinator) -> None:
        super().__init__(coordinator, "loaned_books")

    @property
    def todo_items(self) -> list[TodoItem]:
        items = []
        for index, loan in enumerate(self.coordinator.data.loans):
            summary = loan.title or "?"
            if loan.author:
                summary += f" ({loan.author})"
            items.append(
                TodoItem(
                    summary=summary,
                    uid=loan.record_id or f"loan-{index}",
                    status=TodoItemStatus.NEEDS_ACTION,
                    due=loan.due_date,
                )
            )
        return sorted(items, key=lambda i: (i.due is None, i.due))
