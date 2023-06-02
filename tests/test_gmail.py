


import pytest
from serviceHelpers.gmail import make_new_token, load_token, save_token,InvalidCredentialsException, Gmail
TEST_TOKEN_FILE = "oauth_token.secret"
TEST_EMAIL_ADDRESS = "ctri@ctri.co.uk"


@pytest.fixture
def gmail_service():
    token = load_token(TEST_TOKEN_FILE)
    gmail = Gmail(TEST_EMAIL_ADDRESS,"test_gmail_service",token)
    return gmail

def test_gmail_fetch_gmail_items(gmail_service:Gmail):
    items = gmail_service.list_threads_matching_query( query="label:UNREAD label:INBOX")
    gmail_service.list_threads_matching_query()
    assert items is not None


