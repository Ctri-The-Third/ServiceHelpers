import pytest
from serviceHelpers.gmail import make_new_token,make_new_token_from_refresh_bits, load_pickled_credentials,   save_token,InvalidCredentialsException
import os
import json
from dotenv import load_dotenv

load_dotenv()

 
TEST_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN",None)
TEST_GMAIL_SECRET_JSON = os.environ.get("GMAIL_SECRET_JSON",None)

def save_secret_json_to_file():
    with open("gcloud_secrets.secret", "w") as f:
        f.write(TEST_GMAIL_SECRET_JSON)
 

def test_env_vars():
    assert TEST_REFRESH_TOKEN is not None
    assert TEST_GMAIL_SECRET_JSON is not None   

@pytest.mark.interactive    
def test_make_new_token():
    token = make_new_token("gcloud_secrets.secret")
    
    assert token is not None 

def test_save_token():
    token = test_make_new_token_from_refresh_bits()
    save_token(token, "oauth_token.secret")
    assert os.path.exists("oauth_token.secret")

def test_load_token():
    save_secret_json_to_file()
    try:
        token = load_pickled_credentials("oauth_token.secret")
    except (InvalidCredentialsException, FileNotFoundError) as err:
        assert False
    assert token is not None



def test_make_new_token_from_refresh_bits():
    secret = json.loads(TEST_GMAIL_SECRET_JSON)
    client_id = secret["installed"]["client_id"]
    client_secret = secret["installed"]["client_secret"]
    token = make_new_token_from_refresh_bits(TEST_REFRESH_TOKEN, client_id, client_secret)
    assert token is not None
    assert token.valid is True
    return token