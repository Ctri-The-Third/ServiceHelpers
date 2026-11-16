from serviceHelpers._common import ResponseBlock
from serviceHelpers.habitica import Habitica
from datetime import date
from dotenv import load_dotenv
import pytest
import os
import sys
sys.path.append("")


load_dotenv()

HABITICA_USER_ID = os.environ.get("HABITICA_USER_ID")
HABITICA_API_KEY = os.environ.get("HABITICA_API_KEY")
HABITICA_CLIENT_ID = os.environ.get("HABITICA_CLIENT_ID", "test-client")

TODAY = date.today().isoformat()


@pytest.fixture
def client() -> Habitica:
    return Habitica(HABITICA_USER_ID, HABITICA_API_KEY, HABITICA_CLIENT_ID)


def test_environment_keys():
    assert HABITICA_USER_ID is not None, "HABITICA_USER_ID not set"
    assert HABITICA_API_KEY is not None, "HABITICA_API_KEY not set"


def test_fetch_dailies_returns_response_block(client):
    r = client.fetch_habitica_dailies(TODAY)
    assert isinstance(r, ResponseBlock)


def test_fetch_dailies_success(client):
    r = client.fetch_habitica_dailies(TODAY)
    assert r.okay
    assert isinstance(r.content, list)


def test_fetch_dailies_each_item_is_due(client):
    r = client.fetch_habitica_dailies(TODAY)
    assert r.okay
    for daily in r.content:
        assert daily["isDue"] is True


def test_fetch_dailies_bad_date(client):
    r = client.fetch_habitica_dailies("not-a-date")
    assert isinstance(r, ResponseBlock)


def test_complete_daily_bad_id(client):
    r = client.complete_daily("nonexistent-task-id-00000000")
    assert isinstance(r, ResponseBlock)
    assert not r.okay


def test_fetch_dailies_and_complete_the_first(client):
    r = client.fetch_habitica_dailies()


def test_fetch_tags(client):
    r = client.fetch_habitica_tags()
    assert r
    for tag in r.content:
        assert "id" in tag
        assert "name" in tag
