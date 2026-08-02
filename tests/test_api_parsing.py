"""Parser tests against saved/hand-built Finna HTML fixtures."""

from datetime import date
from pathlib import Path

import pytest

from custom_components.heili_library.api import (
    FinnaData,
    parse_checked_out,
    parse_fines_total,
    parse_finnish_date,
    parse_holds,
    parse_login_form,
)

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_finnish_date():
    assert parse_finnish_date("Eräpäivä: 31.8.2026") == date(2026, 8, 31)
    assert parse_finnish_date("9.12.2025") == date(2025, 12, 9)
    assert parse_finnish_date(None) is None
    assert parse_finnish_date("ei päivämäärää") is None


def test_parse_checked_out():
    loans, renew_ids, csrf = parse_checked_out(fixture("checkedout.html"))
    assert len(loans) == 2  # header row skipped

    loan = loans[0]
    assert loan.title == "Kiikissä"
    assert loan.author == "Amores, Eva"
    assert loan.due_date == date(2026, 8, 31)
    assert loan.renewable is True
    assert loan.details["Lainauspaikka"] == "Pontuksen kirjasto"
    assert loan.details["Uusintakertoja jäljellä"] == "5"

    assert loans[1].title == "Ei-uusittava kirja"
    assert loans[1].renewable is False
    assert loans[1].due_date == date(2026, 7, 15)

    assert renew_ids == ["renewid-1"]
    assert csrf == "testcsrf-123"


def test_parse_checked_out_no_renewals_form():
    # Live Heili omits the whole renewals form when nothing is renewable.
    html = fixture("checkedout.html").replace('name="renewals"', 'name="other"')
    loans, renew_ids, csrf = parse_checked_out(html)
    assert len(loans) == 2
    assert renew_ids == []
    assert csrf is None


def test_parse_holds():
    holds = parse_holds(fixture("holds.html"))
    assert len(holds) == 3

    transit = holds[0]
    assert transit.title == "Korppien kehä"
    assert transit.in_transit is True
    assert transit.available is False
    assert transit.pickup_location == "Pontuksen kirjasto"
    assert transit.expires == date(2029, 7, 11)

    queued = holds[1]
    assert queued.queue_position == "4 (10 kappaletta)"
    assert queued.in_transit is False

    ready = holds[2]
    assert ready.available is True


def test_parse_fines():
    assert parse_fines_total(fixture("fines.html")) == 2.5


def test_parse_fines_empty():
    assert parse_fines_total("<html><body></body></html>") == 0.0


def test_parse_login_form():
    html = """
    <form method="post" action="/MyResearch/Home" name="loginForm" id="loginForm">
      <input type="hidden" name="target" value="heili">
      <input id="u" type="text" name="username" value="">
      <input id="p" type="password" name="password">
      <input type="hidden" name="auth_method" value="MultiILS">
      <input type="hidden" name="csrf" value="abc-def">
    </form>
    """
    fields = parse_login_form(html)
    assert fields == {"target": "heili", "auth_method": "MultiILS", "csrf": "abc-def"}


def test_next_due_date():
    loans, _, _ = parse_checked_out(fixture("checkedout.html"))
    data = FinnaData(loans=loans)
    assert data.next_due_date == date(2026, 7, 15)
    assert FinnaData().next_due_date is None
