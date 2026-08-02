#!/usr/bin/env python3
"""Standalone proof-of-concept: read loans, holds and fines from heili.finna.fi.

Usage:
    FINNA_USERNAME=HEILIxxxxxx FINNA_PIN=1234 python finna_poc.py [--renew-all]

Credentials are read from the environment only; never hardcode or log them.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys

import aiohttp
from bs4 import BeautifulSoup

BASE = "https://heili.finna.fi"
UA = "Mozilla/5.0 (X11; Linux x86_64) HomeAssistant-heili-poc"

DUE_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


async def fetch(session: aiohttp.ClientSession, path: str, **kw) -> str:
    async with session.get(BASE + path, **kw) as resp:
        resp.raise_for_status()
        return await resp.text()


def parse_login_form(html: str) -> dict:
    form = soup_of(html).find("form", attrs={"name": "loginForm"})
    if form is None:
        raise RuntimeError("login form not found")
    return {
        inp["name"]: inp.get("value", "")
        for inp in form.find_all("input", attrs={"type": "hidden"})
    }


async def login(session: aiohttp.ClientSession, username: str, pin: str) -> None:
    html = await fetch(session, "/MyResearch/UserLogin")
    fields = parse_login_form(html)
    fields.update({"username": username, "password": pin, "processLogin": "Kirjaudu"})
    async with session.post(BASE + "/MyResearch/Home", data=fields) as resp:
        resp.raise_for_status()
        body = await resp.text()
    if "loginForm" in body and "authcontainer" in body:
        raise RuntimeError("login failed (login form still present)")


def text_pairs(status_col) -> dict:
    """Extract '<strong>Label:</strong> value' style pairs plus bare strong texts."""
    pairs = {}
    for strong in status_col.find_all("strong"):
        text = strong.get_text(" ", strip=True)
        if ":" in text:
            label, _, value = text.partition(":")
            value = value.strip()
            if not value:
                nxt = strong.next_sibling
                value = str(nxt).strip() if nxt else ""
            pairs[label.strip()] = value
        else:
            pairs.setdefault("_flags", []).append(text)
    return pairs


def parse_checked_out(html: str) -> dict:
    doc = soup_of(html)
    loans = []
    for row in doc.select("tr.myresearch-row"):
        title_el = row.select_one("h3.record-title")
        status = row.select_one(".status-column")
        entry = {
            "title": title_el.get_text(" ", strip=True) if title_el else None,
            "status_text": status.get_text(" | ", strip=True) if status else "",
            "details": text_pairs(status) if status else {},
            "renewable": bool(row.select_one("input.checkbox-select-item")),
        }
        m = DUE_DATE_RE.search(entry["status_text"])
        if m:
            d, mo, y = m.groups()
            entry["due_date"] = f"{y}-{int(mo):02d}-{int(d):02d}"
        loans.append(entry)
    form = doc.find("form", attrs={"name": "renewals"})
    renew_ids = [
        inp.get("value")
        for inp in (form.find_all("input", attrs={"name": "renewAllIDS[]"}) if form else [])
    ]
    csrf_el = form.find("input", attrs={"name": "csrf"}) if form else None
    return {
        "loans": loans,
        "renew_all_ids": renew_ids,
        "csrf": csrf_el.get("value") if csrf_el else None,
    }


def parse_holds(html: str) -> list[dict]:
    doc = soup_of(html)
    holds = []
    for row in doc.select("tr.myresearch-row"):
        title_el = row.select_one("h3.record-title")
        info = row.select_one(".holds-status-information") or row
        holds.append(
            {
                "title": title_el.get_text(" ", strip=True) if title_el else None,
                "available": info.select_one(".alert-success") is not None,
                "in_transit": info.select_one(".text-success") is not None,
                "details": text_pairs(info),
                "status_text": info.get_text(" | ", strip=True),
            }
        )
    return holds


def parse_fines(html: str) -> dict:
    doc = soup_of(html)
    total_el = doc.select_one(".js-payment-total-due[data-raw]")
    total = int(total_el["data-raw"]) / 100 if total_el else None
    rows = []
    for tr in doc.select("table.fines-table tbody tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if cells:
            rows.append(cells)
    if total is None:
        # No online payment block; try summing amount spans.
        amounts = [a.get_text(strip=True) for a in doc.select("span.amount")]
        rows.append({"raw_amounts": amounts})
    return {"total_eur": total, "rows": rows}


async def renew_all(session: aiohttp.ClientSession, checked_out: dict) -> str:
    if not checked_out["renew_all_ids"]:
        return "nothing to renew"
    data = [("renewAll", "1"), ("csrf", checked_out["csrf"])]
    data += [("renewAllIDS[]", i) for i in checked_out["renew_all_ids"]]
    async with session.post(BASE + "/MyResearch/CheckedOut", data=data) as resp:
        resp.raise_for_status()
        body = await resp.text()
    doc = soup_of(body)
    ok = len(doc.select(".status-column .alert-success"))
    fail = len(doc.select(".status-column .alert-danger"))
    return f"renewed ok={ok} failed={fail}"


async def main() -> None:
    username = os.environ.get("FINNA_USERNAME")
    pin = os.environ.get("FINNA_PIN")
    if not username or not pin:
        sys.exit("Set FINNA_USERNAME and FINNA_PIN environment variables.")

    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        await login(session, username, pin)
        print("login: OK", file=sys.stderr)

        checked_out = parse_checked_out(await fetch(session, "/MyResearch/CheckedOut"))
        holds = parse_holds(await fetch(session, "/Holds/List"))
        fines = parse_fines(await fetch(session, "/MyResearch/Fines"))

        result = {
            "loans": checked_out["loans"],
            "renewable_ids_count": len(checked_out["renew_all_ids"]),
            "holds": holds,
            "fines": fines,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if "--renew-all" in sys.argv:
            print(await renew_all(session, checked_out), file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
