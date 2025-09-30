import sys
from datetime import datetime

sys.path.append("")


import logging
from serviceHelpers.slack import slack
from pytest import LogCaptureFixture
import pytest
from dotenv import load_dotenv

import os

load_dotenv()


### Initialise Slack Helper ###
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
SLACK_TOKEN = os.environ.get("SLACK_TOKEN_TEST")
TEST_SLACK_CHANNEL_ID = os.environ.get("SLACK_TEST_CHANNEL_ID", "C0393FK01EE")
SLACK_TEST_USER_ID = os.environ.get("SLACK_USERID_TEST")

def test_environment_key():
    "Test whether or not the token is configured."
    assert SLACK_TOKEN is not None


def test_init_slack_helper_success():
    "Tests whether or not the slack class initialises"
    # config = cfg.ConfigHelper("tests/unitTest_config.json")
    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    assert helper.token is not None


@pytest.mark.xfail(reason="Expected action not yet implemented")
def test_init_slack_helper_incorrect_token_format():
    "Checks how the helper responds to an invalid token"
    bad_slack_token = "abcd-1234-sssssA|ZZZZZZZZZZZZZzzz][][6"

    for bad_token in [bad_slack_token, 5, None]:
        helper = slack(bad_token, "")

    ### Post Slack Message ###


def test_post_to_slack_successful(caplog):
    "Tries to post to a test channel. Won't work in production."
    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    att = [
        {
            "color": "#2EB67D",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<google.com|*Ticket 999*> : Test Ticket:\n*Description*\nSending in a test ticket.",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Requester*"},
                        {"type": "mrkdwn", "text": "*Agent*"},
                        {"type": "mrkdwn", "text": "testUser@testOrg.com"},
                        {"type": "mrkdwn", "text": "%s" % ("TestAgent")},
                        {"type": "mrkdwn", "text": "*Status*"},
                        {"type": "mrkdwn", "text": "Priority"},
                        {"type": "mrkdwn", "text": "new"},
                        {"type": "mrkdwn", "text": "urgent"},
                    ],
                },
            ],
        }
    ]
    text = "new ticket from testUser at testOrg\nURL: google.com\n\nTest Ticket"

    helper.post_to_slack_via_token(text, TEST_SLACK_CHANNEL_ID, attachment=att)

    errorMessageCounter = 0

    for record in caplog.records:
        if record.levelname >= "ERROR":
            errorMessageCounter += 1

    assert errorMessageCounter == 0


def test_post_to_slack_no_channel(caplog):
    "Tries to post when there's no channel specified"
    att = [
        {
            "color": "#2EB67D",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<google.com|*Ticket 999*> : Test Ticket:\n*Description*\nSending in a test ticket.",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Requester*"},
                        {"type": "mrkdwn", "text": "*Agent*"},
                        {"type": "mrkdwn", "text": "testUser@testOrg.com"},
                        {"type": "mrkdwn", "text": "%s" % ("TestAgent")},
                        {"type": "mrkdwn", "text": "*Status*"},
                        {"type": "mrkdwn", "text": "Priority"},
                        {"type": "mrkdwn", "text": "new"},
                        {"type": "mrkdwn", "text": "urgent"},
                    ],
                },
            ],
        }
    ]
    text = "new ticket from testUser at testOrg\nURL: google.com\n\nTest Ticket"

    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)
    helper.post_to_slack_via_token(text, None, attachment=att)

    for record in caplog.records:
        assert record.levelname >= "ERROR"


def test_post_to_slack_no_attachment(caplog):
    "test post without an attachment."

    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    text = "new ticket from testUser at testOrg\nURL: google.com\n\nTest Ticket"

    resp = helper.post_to_slack_via_token(text, TEST_SLACK_CHANNEL_ID)

    for record in caplog.records:
        assert record.levelno < logging.WARNING


@pytest.mark.skip(reason="test token doesn't have proper permissions to test at the moent.")
def test_fetch_user_profile(caplog):
    "Checks a user profile from the test server"
    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    good_profile_id = SLACK_TEST_USER_ID

    profile = helper.fetch_user_profile(good_profile_id)

    assert isinstance(profile["email"], str)
    assert isinstance(profile["display_name_normalized"], str)
    assert isinstance(profile["email"], str)
    assert isinstance(profile["status_emoji"], str)
    assert isinstance(profile["status_text"], str)
    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_fetch_bad_user_id(caplog):
    "Checks what happens when we miss"

    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    bad_profile_ids = [None, 5, "hello world"]

    for id in bad_profile_ids:
        _ = helper.fetch_user_profile(id)
    for record in caplog.records:
        assert record.levelno >= logging.WARNING




def test_update_message_integration(caplog):
    "Integration test for updating a message - requires a real message to edit"
    helper = slack(SLACK_TOKEN, SLACK_WEBHOOK)

    ts = helper.post_to_slack_via_token("TEST MESSAGE FOR EDITING - PLEASE IGNORE", TEST_SLACK_CHANNEL_ID)
    assert ts 
    response = helper.update_message(TEST_SLACK_CHANNEL_ID, ts, "UPDATED TEST MESSAGE ✅ - PLEASE IGNORE")
    assert response  


    
    # This would require:
    # 1. Posting a test message first
    # 2. Getting its timestamp
    # 3. Updating that message
    # 4. Verifying the update worked
    # 5. Cleaning up the test message
    
    # Example implementation (commented out for safety):
    # original_text = "TEST MESSAGE - PLEASE IGNORE"
    # updated_text = "UPDATED TEST MESSAGE - PLEASE IGNORE"
    # test_channel = "C0393FK01EE"  # Replace with actual test channel
    # 
    # # Post original message
    # message_ts = helper.post_to_slack_via_token(original_text, test_channel)
    # assert message_ts != ""
    # 
    # # Update the message
    # update_result = helper.update_message(test_channel, message_ts, updated_text)
    # assert update_result != ""
    # 
    # # Verify the message was updated
    # message_info = helper.get_message_info(test_channel, message_ts)
    # assert message_info.get("text") == updated_text
    
    pass


