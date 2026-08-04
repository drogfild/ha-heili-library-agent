"""Todo entity builds its items from coordinator loans."""

from datetime import date
from types import SimpleNamespace

from homeassistant.components.todo import TodoItemStatus

from custom_components.finna_library.api import FinnaData, Loan
from custom_components.finna_library.todo import LoansTodoList


def make_entity(loans: list[Loan]) -> LoansTodoList:
    coordinator = SimpleNamespace(
        host="demo.finna.fi",
        username="DEMO123",
        client=SimpleNamespace(base_url="https://demo.finna.fi"),
        data=FinnaData(loans=loans),
    )
    return LoansTodoList(coordinator)


def loan(title, author=None, due=None, record_id=None) -> Loan:
    return Loan(
        title=title,
        author=author,
        due_date=due,
        renewable=True,
        details={},
        record_id=record_id,
    )


def test_items_sorted_by_due_date_with_dateless_last():
    entity = make_entity(
        [
            loan("Myöhempi", due=date(2026, 9, 15), record_id="demo.b-2"),
            loan("Päivätön"),
            loan("Aiempi", author="Amores, Eva", due=date(2026, 8, 31), record_id="demo.a-1"),
        ]
    )
    items = entity.todo_items
    assert [i.summary for i in items] == [
        "Aiempi (Amores, Eva)",
        "Myöhempi",
        "Päivätön",
    ]
    assert items[0].due == date(2026, 8, 31)
    assert items[0].uid == "demo.a-1"
    assert all(i.status == TodoItemStatus.NEEDS_ACTION for i in items)


def test_uid_falls_back_to_index_and_title_to_question_mark():
    entity = make_entity([loan(None)])
    (item,) = entity.todo_items
    assert item.uid == "loan-0"
    assert item.summary == "?"


def test_empty_loans_gives_empty_list():
    assert make_entity([]).todo_items == []


def test_list_is_read_only():
    assert make_entity([]).supported_features in (None, 0)
