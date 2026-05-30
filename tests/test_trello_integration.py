import sys

sys.path.append("")
import os

from serviceHelpers.trello import trello, ResponseBlock

TEST_BOARD_ID = "5f0dee6c5026590ce300472c"
TEST_LIST_ID = "5f0dee6c5026590ce3004732"
TEST_LIST_ID_TWO = "61d8367af7a2942f50afd468"
TRELLO_KEY = os.environ.get("TRELLO_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")


def test_trello_get_cards():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    cards = helper.fetch_trello_cards()
    assert isinstance(cards,ResponseBlock)
    
    for  card in cards.content.get("results",[]):
        assert "id" in card

    assert len(cards.content) == len(helper._cached_cards)


def test_create_card_at_correct_position():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    r = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=0,
    )
    assert r 
    card = r.content
    
    r = helper.delete_trello_card(card["id"])
    assert r 

    r = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=3,
    )
    assert r 
    card = r.content
    helper.delete_trello_card(card["id"])

    r = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=-1,
    )
    assert r 
    card = r.content
    helper.delete_trello_card(card["id"])


def test_move_card_from_list_to_list():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    r1  = helper.create_card("TEST CARD, PLEASE IGNORE", TEST_LIST_ID)
    assert r1 
    card = r1.content

    r2 = helper.update_card(card["id"], card["name"], new_list_id=TEST_LIST_ID_TWO)
    assert r2 

    r3 = helper.fetch_trello_card(card["id"])
    new_card = r3.content

    r4 = helper.delete_trello_card(new_card["id"])
    assert r4 
    assert card["id"] == new_card["id"]
    assert new_card.get("idList", "") == TEST_LIST_ID_TWO


def test_update_card():
    old_ts = "2022-10-01 23:59:00"
    new_ts = "2011-11-11 11:11:00"
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    card = helper.create_card(
        "TEST CARD, PLEASE IGNORE", TEST_LIST_ID, dueTimestamp=old_ts
    ).content
    helper.update_card(card["id"], card["name"], new_due_timestamp=new_ts)
    new_card = helper.find_trello_card(card["id"])

    r = helper.delete_trello_card(new_card["id"])
    assert r 
    assert new_card["due"] == "2011-11-11T11:11:00.000Z"


def test_fetch_all_actions():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    r = helper.fetch_actions_for_board()
    actions = r.content
    assert r 
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert "id" in actions[0]
    return actions


def test_actions_since():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)

    actions = test_fetch_all_actions()
    since = actions[2]["id"]
    new_actions = helper.fetch_actions_for_board(since=since).content

    assert isinstance(new_actions, list)
    assert len(new_actions) < len(actions)


def test_list_fetching_and_getting():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)

    lists = helper.fetch_lists()
    assert isinstance(lists, dict)
    assert len(lists) > 0
    for list_id, list_inst in lists.items():
        assert isinstance(list_inst, dict)
        list_inst:dict 
        assert list_id == list_inst.get("id")

    other_lists = helper.get_lists()
    assert isinstance (other_lists,dict)
    for id, other_list_inst in other_lists.items():
        assert id in lists


def test_list_getting_without_cache():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)

    lists = helper.fetch_lists().content
    assert isinstance(lists, dict)
    assert len(lists) > 0
    for list_id, list_inst in lists.items():
        assert isinstance(list_inst, dict)
        list_inst:dict 
        assert list_id == list_inst.get("id")



def test_list_labels():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)
    r = helper.fetch_labels_on_board()
    assert r
    labels = r.content
    assert len(labels) > 0 

    return labels


def test_add_label_to_card():
    helper = trello(TEST_BOARD_ID, TRELLO_KEY, TRELLO_TOKEN)

    r = helper.create_card(
        "TEST CARD, PLEASE IGNORE",
        TEST_LIST_ID,
        "A temporary card that should get deleted",
        position=0,
    )
    assert r 
    card = r.content
    
    r = helper.fetch_labels_on_board()
    labels = r.content 

    target_labels = len(labels)
    for label in labels:
        helper.add_label_to_card(card["id"], label)
    new_card = helper.get_trello_card(card["id"])
    assert len(new_card["idLabels"]) == len(labels)
    new_card = helper.fetch_trello_card(card["id"]).content
    assert len(new_card["idLabels"]) == len(labels)

    helper.delete_trello_card(card["id"])
    

