import sys
sys.path.append("")

import os 
import json
import logging
import pytest
from serviceHelpers.freshdesk import FreshDesk, FreshdeskTicket 


FRESHDESK_HOST = os.environ.get("FRESHDESK_HOST")
FRESHDESK_KEY = os.environ.get("FRESHDESK_KEY")

def test_init():
    "check the classes can start up"
    assert FRESHDESK_HOST is not None
    assert FRESHDESK_KEY is not None
    FreshDesk(FRESHDESK_HOST,FRESHDESK_KEY)
    FreshdeskTicket()


def test_search(caplog):
    "fetch a ticket and check it matches expected values"
    fresh = FreshDesk(FRESHDESK_HOST,FRESHDESK_KEY)
    tickets = fresh.search_fd_tickets("agent_id:12345")

    assert len(tickets) == 1

    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_user_id(caplog):
    "fetch a user by ID, see how it performs"
    fresh = FreshDesk(FRESHDESK_HOST,FRESHDESK_KEY)
    fresh._get_agent_by_id(11019533812)

    