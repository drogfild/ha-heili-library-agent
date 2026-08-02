# Heili Library — Home Assistant integration

[![Validate](https://github.com/talonpoika/ha-heili-library-agent/actions/workflows/validate.yml/badge.svg)](https://github.com/talonpoika/ha-heili-library-agent/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/talonpoika/ha-heili-library-agent)](https://github.com/talonpoika/ha-heili-library-agent/releases)

Home Assistant custom integration for [Heili libraries](https://heili.finna.fi)
(South Karelia, Finland). Logs into the Finna web library with your library
card and brings your loans, holds and fines into Home Assistant — no Selenium,
no browser, just HTTP.

Finna has no public API for user data, so the integration logs in the same way
a browser does (form POST with a CSRF token) and parses the account pages.
Data refreshes every 6 hours. If the PIN stops working, Home Assistant asks
you to re-authenticate.

## Entities (one device per library card)

| Entity | Description |
| --- | --- |
| `sensor.*_loans` | Number of loans; attributes list each book (title, author, due date, renewable) |
| `sensor.*_next_due_date` | Earliest due date (`device_class: date`) |
| `sensor.*_fines` | Outstanding fees in EUR (`device_class: monetary`) |
| `sensor.*_holds` | Number of holds; attributes list pickup location, queue position, expiry |
| `sensor.*_holds_ready` | Holds ready for pickup |
| `sensor.*_loans_this_year` | Loans checked out this calendar year (requires loan history enabled in Finna) |
| `sensor.*_saved_searches` | Saved searches with hit counts; `new_results` attributes flag searches whose hits grew since the last poll |
| `button.*_renew_all` | Renew all renewable loans |
| `calendar.*_due_dates` | All-day events for every due date |

Multiple library cards are supported — add each card as its own config entry.

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → *Custom repositories*
2. Add `https://github.com/talonpoika/ha-heili-library-agent`, category **Integration**
3. Install **Heili Library**, restart Home Assistant

### Manual

Copy `custom_components/heili_library/` into your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

Settings → Devices & Services → **Add Integration** → *Heili Library*.
Enter your library card number (`HEILI...`) and 4-digit PIN — the same
credentials you use at heili.finna.fi.

To refresh on demand, call `homeassistant.update_entity` on any of the
integration's entities.

### Tips

- **Loans this year** stays at 0 until you enable loan history storage in
  Finna (Omat tiedot → Lainaushistorian tallennus).
- **Saved-search watch**: save a search in Finna ("Tallenna haku"); when its
  hit count grows between polls, the sensor's `new_results` attribute shows
  the delta — handy for new-arrival notifications.

## Example automation

```yaml
automation:
  - alias: "Library book due soon"
    triggers:
      - trigger: calendar
        entity_id: calendar.heili_mycard_due_dates
        event: start
        offset: "-48:00:00"   # two days before the due date
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "{{ trigger.calendar_event.summary }} erääntyy pian!"
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install aiohttp beautifulsoup4 pytest homeassistant pytest-homeassistant-custom-component
.venv/bin/python -m pytest tests/
```

Tests parse saved HTML fixtures (`tests/fixtures/`) so they never hit Finna.
`poc/finna_poc.py` is a standalone script that exercises the same login and
parsing flow against the live site; credentials are passed via the
`FINNA_USERNAME` and `FINNA_PIN` environment variables only.

## Security notes

Credentials are stored in Home Assistant's config entry storage and are never
logged. This project interacts with a third-party service; you are responsible
for ensuring your use complies with its terms of use.

## History

This project started as an AppDaemon app scraping the old Arena site
(heilikirjastot.fi) with Selenium. Heili libraries moved to the Finna
platform, and the project was rewritten as a native custom integration
(see git history before v1.0.0 for the old implementation).

## License

MIT License
