import pytest
from serviceHelpers.gmail import make_new_token, load_token, save_token,InvalidCredentialsException
import os

 
@pytest.mark.interactive    
def test_make_new_token():
    token = make_new_token("gcloud_secrets.secret")
    
    assert token is not None 

@pytest.mark.interactive
def test_save_token():
    token = make_new_token("gcloud_secrets.secret")
    save_token(token, "oauth_token.secret")
    assert os.path.exists("oauth_token.secret")

def test_load_token():
    try:
        token = load_token("oauth_token.secret")
    except (InvalidCredentialsException, FileNotFoundError) as err:
        assert False
    assert token is not None