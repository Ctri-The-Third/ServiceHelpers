import sys

sys.path.append("")

import os
import logging
from serviceHelpers.freshdesk import FreshDesk, FreshdeskTicket


FRESHDESK_HOST = os.environ.get("FRESHDESK_HOST")
FRESHDESK_KEY = os.environ.get("FRESHDESK_KEY")
TARGET_EMAIL = os.environ.get("TEST_EMAIL")
TARGET_ID = 11019533812


def test_env_host():
    "check the host environment variable is set"
    assert FRESHDESK_HOST is not None


def test_env_key():
    "check the key environment variable is set"
    assert FRESHDESK_KEY is not None


def test_env_email():
    "check the email environment variable is set"
    assert TARGET_EMAIL is not None


def test_init():
    "check the classes can start up"

    FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    FreshdeskTicket()


def test_search(caplog):
    "fetch a ticket and check it matches expected values"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    tickets = fresh.search_fd_tickets(f"agent_id:{TARGET_ID}")

    assert len(tickets) > 1

    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_fetch_comments(caplog):
    "retrieve comments for a specific ID"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    comments = fresh.get_comments(24535)

    assert len(comments) > 0
    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_fetch_worklogs(caplog):
    "retrieve worklogs for a specific ID"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    worklogs = fresh.get_worklogs(24535)

    assert len(worklogs) > 0
    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_user_id(caplog):
    "fetch a user by ID, see how it performs"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    agent = fresh._get_agent_by_id(TARGET_ID)
    assert isinstance(agent.id, int) and agent.id > 0
    assert isinstance(agent.email, str) and agent.email != ""
    assert isinstance(agent.name, str) and agent.name != ""

    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_user_email(caplog):
    "fetch a user by email, see how it performs"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    agent = fresh._get_agent_by_email(TARGET_EMAIL)
    assert isinstance(agent.id, int) and agent.id > 0
    assert isinstance(agent.email, str) and agent.email != ""
    assert isinstance(agent.name, str) and agent.name != ""

    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_user_invalid_email(caplog):
    "fetch a user by email, with invalid items. Will"
    fresh = FreshDesk(FRESHDESK_HOST, FRESHDESK_KEY)
    emails = ["", 5, "not-real@test.com"]
    for email in emails:
        agent = fresh._get_agent_by_email(email)
