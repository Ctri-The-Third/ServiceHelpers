import sys
from datetime import datetime

sys.path.append("")

import json
import logging

import pytest
from pytest import LogCaptureFixture
import serviceHelpers.jira
from serviceHelpers.jira import Jira, TIMESTAMP_FORMAT, JiraDetails, JiraTicket

import os

LO = logging.getLogger("jira_tests")


def test_keys():
    "Checks whether environment variables are properly set"
    host = os.environ.get("JIRA_HOST_1")
    assert host is not None

    api_key = os.environ.get("JIRA_KEY_1")
    assert api_key is not None


def get_details() -> JiraDetails:
    "generate the `JiraDetails` object used for endpoint testing"
    deets = JiraDetails()
    deets.host = os.environ.get("JIRA_HOST_1")
    deets.key = os.environ.get("JIRA_KEY_1")
    deets.name = "test_environ"
    return deets


@pytest.mark.skip("Not implemented yet")
def test_details() -> JiraDetails:
    """Check that the jira details class loads things from the json file"""
    failures = 0
    try:
        file = open("tests/jira_settings.json", encoding="utf8")
        loaded_details = json.load(file)
        loaded_details = loaded_details["test_details"]
        file.close()
    except Exception as ex:
        LO.error("Couldn't open the jira_settings.json file, %s", ex)
        failures += 1

    details_object = JiraDetails().from_dict(loaded_details)

    try:
        details_object.host = loaded_details["host"]
        failures = (
            failures + 1 if details_object.host != loaded_details["host"] else failures
        )
    except Exception as ex:
        failures += 1
        LO.error(ex)

    try:
        details_object.key = loaded_details["key"]
        failures = (
            failures + 1 if details_object.key != loaded_details["key"] else failures
        )
    except Exception as ex:
        failures += 1
        LO.error(ex)

    try:
        details_object.name = loaded_details["name"]
        failures = (
            failures + 1 if details_object.name != loaded_details["name"] else failures
        )
    except Exception as ex:
        failures += 1
        LO.error(ex)

    if failures != 0 and details_object.valid:
        failures += 1
        LO.warning("Jira details object is not reporting valid correctly")
    elif failures == 0 and not details_object.valid:
        failures += 1
        LO.warning("Jira details object is not reporting valid correctly")

    assert failures == 0
    return details_object


def test_jira_init() -> Jira:
    """using the output of test_details, check we have access."""
    failures = 0
    details_obj = get_details()

    test_instance = Jira(details_obj)

    if not test_instance.valid:
        failures += 1
        LO.error("Jira isn't valid")

    if test_instance.host != details_obj.host:
        failures += 1

    if test_instance.name != details_obj.name:
        failures += 1

    if test_instance.token != details_obj.key:
        failures += 1

    assert failures == 0
    return test_instance


@pytest.mark.skip("Not implemented yet")
def test_fetch(caplog: LogCaptureFixture) -> JiraTicket:
    """Exceutes a JQL string (expects a single closed ticket return)"""
    failures = 0

    jira_instance = test_jira_init()

    for record in caplog.records:
        assert record.levelname >= "ERROR"
    assert failures == 0
    return


@pytest.mark.skip("Not implemented yet")
def test_ticket_content(caplog: LogCaptureFixture):
    """Checks a supplied ticket against the test config"""
    failures = 0
    try:
        file = open("tests/jira_settings.json", encoding="utf8")
        loaded_details = json.load(file)
        loaded_details = loaded_details["test_ticket_content"]
        file.close()
    except Exception as ex:
        LO.error("Couldn't open the jira_settings.json file, %s", ex)
        failures += 1

    ticket = test_fetch(caplog)
    assert isinstance(ticket, JiraTicket)

    assert ticket.assignee_id == loaded_details["expected_assignee_id"]
    assert ticket.assignee_name == loaded_details["expected_assignee_name"]
    try:
        match = ticket.created == datetime.strptime(
            loaded_details["expected_created_timestamp"], TIMESTAMP_FORMAT
        )
    except (ValueError) as ex:
        LO.error(
            "Couldn't parse the created timestamp of the test string - embarassing. %s",
            ex,
        )
        assert False

    assert match

    try:
        match = ticket.updated == datetime.strptime(
            loaded_details["expected_updated_timestamp"], TIMESTAMP_FORMAT
        )
    except ValueError as ex:
        LO.error(
            "Couldn't parse the updated timestamp of the test string - embarassing"
        )
        assert False

    assert match

    if loaded_details["expected_description"] == "":
        assert ticket.description is None
    else:
        assert ticket.description == loaded_details["expected_description"]
    assert ticket.priority == loaded_details["expected_priority"]
    assert ticket.key == loaded_details["expected_key"]
    assert ticket.status == loaded_details["expected_status"]
    assert ticket.summary == loaded_details["expected_summary"]


def test_fetch_worklogs():
    "Checks the response when fetching worklogs from a known ticket"
    details = get_details()
    instance = Jira(details)

    results = instance.fetch_worklogs_for_jira_ticket("GSDSE-51")
    assert len(results) > 0
