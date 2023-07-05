import sys

sys.path.append("")
import os

from serviceHelpers.trello import trello

TEST_BOARD_ID = "5f0dee6c5026590ce300472c"
TEST_LIST_ID = "5f0dee6c5026590ce3004732"
TEST_LIST_ID_TWO = "61d8367af7a2942f50afd468"
TRELLO_KEY = os.environ.get("TRELLO_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")


def test_trello_get_cards():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    cards = helper.fetch_trello_cards()
    for card in cards:
        assert "id" in card

    assert len(cards) == len(helper._cached_cards)


def test_create_card_at_correct_position():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    card = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=0,
    )
    helper.delete_trello_card(card["id"])

    card = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=3,
    )
    helper.delete_trello_card(card["id"])

    card = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=-1,
    )
    helper.delete_trello_card(card["id"])


def test_move_card_from_list_to_list():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    card = helper.create_card("TEST CARD, PLEASE IGNORE", TEST_LIST_ID)
    helper.update_card(card["id"], card["name"], new_list_id=TEST_LIST_ID_TWO)
    new_card = helper.fetch_trello_card(card["id"])

    helper.delete_trello_card(new_card["id"])
    assert card["id"] == new_card["id"]
    assert new_card.get("idList", "") == TEST_LIST_ID_TWO


def test_update_card():
    old_ts = "2022-10-01 23:59:00"
    new_ts = "2011-11-11 11:11:00"
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    card = helper.create_card(
        "TEST CARD, PLEASE IGNORE", TEST_LIST_ID, dueTimestamp=old_ts
    )
    helper.update_card(card["id"], card["name"], new_due_timestamp=new_ts)
    new_card = helper.find_trello_card(card["id"])

    helper.delete_trello_card(new_card["id"])
    assert new_card["due"] == "2011-11-11T11:11:00.000Z"


def test_fetch_all_actions():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    actions = helper.fetch_actions_for_board(limit=500)

    assert isinstance(actions, list)
    assert len(actions) > 0
    assert "id" in actions[0]
    return actions


def test_actions_since():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)

    actions = test_fetch_all_actions()
    since = actions[2]["id"]
    new_actions = helper.fetch_actions_for_board(since=since)

    assert isinstance(new_actions, list)
    assert len(new_actions) < len(actions)
