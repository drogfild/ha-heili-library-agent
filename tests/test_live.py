"""Live end-to-end test against heili.finna.fi.

Skipped unless FINNA_USERNAME and FINNA_PIN are set in the environment.
Run manually: FINNA_USERNAME=... FINNA_PIN=... pytest tests/test_live.py -s
"""

import os

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.finna_library.const import CONF_PIN, CONF_USERNAME, DOMAIN

pytestmark = pytest.mark.skipif(
    not (os.environ.get("FINNA_USERNAME") and os.environ.get("FINNA_PIN")),
    reason="live credentials not provided",
)


@pytest.fixture(autouse=True)
def allow_network():
    """Lift the test harness's network block for this live test."""
    import pytest_socket

    pytest_socket._remove_restrictions()
    yield


@pytest.mark.asyncio
async def test_setup_against_live_finna(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="live",
        data={
            CONF_USERNAME: os.environ["FINNA_USERNAME"],
            CONF_PIN: os.environ["FINNA_PIN"],
        },
        unique_id="live-test",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    username = os.environ["FINNA_USERNAME"].lower()
    states = {
        s.entity_id: s for s in hass.states.async_all() if s.entity_id != "person.test"
    }
    print("\nEntities:")
    for entity_id, state in sorted(states.items()):
        print(f"  {entity_id} = {state.state}")
        for k, v in state.attributes.items():
            if k in ("loans", "holds"):
                print(f"    {k}: {v}")

    loans = next(s for e, s in states.items() if e.endswith("_loans"))
    assert loans.state.isdigit()
    next_due = next(s for e, s in states.items() if e.endswith("_next_due_date"))
    assert next_due.state not in ("unknown", "unavailable") or loans.state == "0"
