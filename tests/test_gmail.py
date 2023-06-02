
import os

import pytest
from serviceHelpers.gmail import make_new_token_from_refresh_bits, load_token, save_token 
from serviceHelpers.gmail import extract_clientid_clientsecret_from_secretjson, InvalidCredentialsException, Gmail

TEST_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN_TEST",None)
TEST_GMAIL_SECRET_JSON = os.environ.get("GMAIL_SECRET_JSON",None)
TEST_EMAIL_ADDRESS = "github-tests@ctri.co.uk"
@pytest.fixture


def test_env_vars():
    assert TEST_REFRESH_TOKEN is not None
    assert TEST_GMAIL_SECRET_JSON is not None   
 
def gmail_service():
    secret_bits = extract_clientid_clientsecret_from_secretjson(TEST_GMAIL_SECRET_JSON)
    token = make_new_token_from_refresh_bits(TEST_REFRESH_TOKEN, secret_bits[0], secret_bits[1])
    gmail = Gmail(TEST_EMAIL_ADDRESS,"test_gmail_service",token)
    return gmail

def test_gmail_fetch_gmail_items(gmail_service:Gmail):
    items = gmail_service.list_threads_matching_query( query="label:UNREAD label:INBOX")
    
    assert items is not None
    
 

