import sys
from datetime import datetime

sys.path.append("")

import os 
import json
import logging
import pytest
from zendesk import zendesk, ZendeskOrganisation, ZendeskTicket, ZendeskUser

ZENDESK_HOST = os.environ.get("ZENDESK_HOST")
ZENDESK_KEY = os.environ.get("ZENDESK_KEY")

def test_init(caplog) -> zendesk:
    """Tests the initialization of a `zendesk` object using values set in environment variables `zendesk_settings.json` file"""

    zd = zendesk(ZENDESK_HOST,ZENDESK_KEY)

    for record in caplog.records:
        assert record.levelno < logging.ERROR
    
    return zd

    
@pytest.mark.skip("Not implemented yet")
def test_get_organisation(caplog):
    """Tests the functionality of the `get_organisation` method"""
    failures = 0

    zd = test_init(caplog)
    zd.get_organisation(361673330791 )
    assert failures == 0

@pytest.mark.skip("Not implemented yet")
def test_org_init():
    """verifies the error handling of a ZendeskOrganisation object's initialisation"""
    
    test_strs = [
        json.dumps({}),
        json.dumps({"user":"not_a_dict"}),
        json.dumps({"user": {"id":"text","name":"text","email":"text","organization_id":"text"}}),
        json.dumps({"user": []}),
        json.dumps({"user": {"id":None,"name":None,"email":None,"organization_id":None}}),
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
    assert isinstance(user,ZendeskUser)

    assert user.name == "test test"
    assert user.email == "test@test.com"
    assert user.userID == 417316391
    assert user.organisationID is None



def test_user_init(caplog):
    """verifies the error handling of a ZendeskUser object's initialisation"""
    
    test_strs = [
        "",
        json.dumps({}),
        json.dumps({"user":"not_a_dict"}),
        json.dumps({"user": {"id":"text","name":"text","email":"text","organization_id":"text"}}),
        json.dumps({"user": []}),
        json.dumps({"user": {"id":None,"name":None,"email":None,"organization_id":None}}),
    ]

    for test_str in test_strs:
        zu = ZendeskUser(test_str)

    
    for entry in caplog.records:
        assert entry.levelno < logging.ERROR
        



def test_search_for_tickets():
    failures = 0
    assert failures == 0




