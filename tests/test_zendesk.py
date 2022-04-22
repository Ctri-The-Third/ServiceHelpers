import sys
from datetime import datetime


sys.path.append("")
import os
import json
import logging
import pytest
from serviceHelpers.zendesk import (
    zendesk,
    ZendeskOrganisation,
    ZendeskUser,
    ZendeskWorklog,
)

ZENDESK_HOST = os.environ.get("ZENDESK_HOST")
ZENDESK_KEY = os.environ.get("ZENDESK_KEY")
TARGET_EMAIL = os.environ.get("TEST_EMAIL")
WORKLOG_FIELD_ID = 360028226411


def test_init(caplog) -> zendesk:
    """Tests the initialization of a `zendesk` object using values set in environment variables `zendesk_settings.json` file"""

    zd = zendesk(ZENDESK_HOST, ZENDESK_KEY)

    for record in caplog.records:
        assert record.levelno < logging.ERROR

    return zd


@pytest.mark.skip("Not implemented yet")
def test_get_organisation(caplog):
    """Tests the functionality of the `get_organisation` method"""
    failures = 0

    zd = test_init(caplog)
    zd.get_organisation(361673330791)
    assert failures == 0


@pytest.mark.skip("Not implemented yet")
def test_org_init():
    """verifies the error handling of a ZendeskOrganisation object's initialisation"""

    test_strs = [
        json.dumps({}),
        json.dumps({"user": "not_a_dict"}),
        json.dumps(
            {
                "user": {
                    "id": "text",
                    "name": "text",
                    "email": "text",
                    "organization_id": "text",
                }
            }
        ),
        json.dumps({"user": []}),
        json.dumps(
            {"user": {"id": None, "name": None, "email": None, "organization_id": None}}
        ),
    ]

    for test_str in test_strs:
        zo = ZendeskOrganisation(test_str)

    failures = 0
    assert failures == 0


def test_get_user(caplog):
    """Tests the functionality of the `get_user` method"""

    zd = test_init(caplog)

    user = zd.get_user(417316391)
    for entry in caplog.records:
        assert entry.levelno < logging.ERROR
    assert isinstance(user, ZendeskUser)

    assert user.name == "Mat Perry"
    assert user.email == "test@test.com"
    assert user.user_id == 417316391
    assert user.organisationID is None


def test_search_user(caplog):
    "check for users"
    zd = test_init(caplog)
    users = zd.search_for_users("type:user email:test@test.com")

    assert len(users) > 0
    for user_key in users:

        assert isinstance(users[user_key], ZendeskUser)


def test_user_init_and_invalid_handling(caplog):
    """verifies the error handling of a ZendeskUser object's initialisation"""

    test_strs = [
        "",
        json.dumps({}),
        json.dumps({"user": "not_a_dict"}),
        json.dumps(
            {
                "user": {
                    "id": "text",
                    "name": "text",
                    "email": "text",
                    "organization_id": "text",
                }
            }
        ),
        json.dumps({"user": []}),
        json.dumps(
            {"user": {"id": None, "name": None, "email": None, "organization_id": None}}
        ),
    ]

    for test_str in test_strs:
        zu = ZendeskUser(test_str)

    for entry in caplog.records:
        assert entry.levelno < logging.ERROR


def test_search_for_tickets(caplog):
    "Check for tickets belonging to a specific group"
    zend = zendesk(ZENDESK_HOST, ZENDESK_KEY)
    search_str = "requester:ctri.goudie@unity3d.com"

    tickets = zend.search_for_tickets(search_string=search_str)
    assert len(tickets) > 0

    for entry in caplog.records:
        assert entry.levelno < logging.ERROR


def test_worklog_parse():
    "check that if missing fields aren't supplied, the worklog is not reported as valid"
    log = ZendeskWorklog()
    log.from_json({"author_id": 123456789}, WORKLOG_FIELD_ID)
    assert not log.is_valid


def test_worklog_parse_invalid_ts_format():
    "Bad TS format should return invalid"
    log = ZendeskWorklog()
    js_obj = {
        "author_id": 123456789,
        "events": [
            {
                "field_name": f"{WORKLOG_FIELD_ID}",
                "created_at": "2022-04-04 01:33:50",
                "value": "120",
            }
        ],
    }
    log.from_json(js_obj, WORKLOG_FIELD_ID)
    assert not log.is_valid


def test_get_worklogs_from_audit(caplog):
    "Check that there are no errors when retrieving worklogs via the audit endpoint"
    zend = zendesk(ZENDESK_HOST, ZENDESK_KEY)
    logs = zend.get_worklogs(1223656, WORKLOG_FIELD_ID)
    assert len(logs) > 0
    for entry in caplog.records:
        assert entry.levelno < logging.ERROR
