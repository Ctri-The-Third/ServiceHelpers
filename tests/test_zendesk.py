import sys
from datetime import datetime

sys.path.append("")

import json
import logging

from pytest import LogCaptureFixture
from zendesk import zendesk, ZendeskOrganisation, ZendeskTicket, ZendeskUser



def test_init():
    """Tests the initialization of a `zendesk` object using values set in a `zendesk_settings.json` file"""
    failures = 0
    assert failures == 0
    

def test_get_organisation():
    """Tests the functionality of the `get_organisation` method"""
    failures = 0
    assert failures == 0


def test_org_init():
    """Verifies the error handling of an organisation object's initialisation"""
    failures = 0
    assert failures == 0

def test_get_user():
    """Tests the functionality of the `get_user` method"""
    failures = 0
    assert failures == 0

def test_user_init():
    """verifies the error handling of a ZendeskUser object's initialisation"""
    failures = 0
    assert failures == 0


def test_search_for_tickets():
    failures = 0
    assert failures == 0




