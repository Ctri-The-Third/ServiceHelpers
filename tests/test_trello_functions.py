import sys

sys.path.append("")
import os

from serviceHelpers.trello import trello

TEST_BOARD_ID = "5f0dee6c5026590ce300472c"
TEST_LIST_ID = "5f0dee6c5026590ce3004732"
TEST_LIST_ID_TWO = "61d8367af7a2942f50afd468"
TRELLO_KEY = os.environ.get("TRELLO_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")


def test_trello_sort():
    helper = trello("none", "none", "none")

    list_to_sort = [
        {"pos": 300},
        {"pos": 0.304},
        {"pos": 20.4},
        {"pos": 44.4},
        {"pos": 209.30955},
    ]
    list_to_sort = helper._sort_trello_cards_list(list_to_sort)
    last_pos = 0
    for card in list_to_sort:
        assert card["pos"] > last_pos
        last_pos = card["pos"]


def test_trello_sort_array():
    helper = trello("none", "none", "none")
    cards = {
        "id_1": {"id": "id_1", "pos": 300},
        "id_2": {"id": "id_2", "pos": 0.304},
        "id_5": {"id": "id_5", "pos": 20.4},
        "id_3": {"id": "id_3", "pos": 44.4},
        "id_7": {"id": "id_7", "pos": 209.30955},
        "id_12": {"id": "id_12", "pos": 4444},
        "id_33": {"id": "id_44", "pos": 3.5},
        "id_32": {"id": "id_32", "pos": 2.1},
    }
    sorted_cards = helper._sort_trello_cards_dict(cards)
    last_pos = 0
    for _, card in sorted_cards.items():
        assert card["pos"] >= last_pos
        last_pos = card["pos"]


def test_convert_index_to_pos():
    helper = trello("none", "none", "none")
    helper._cached_cards = {
        "id_1": {"id": "id_1", "idList": "main", "pos": 300},
        "id_2": {"id": "id_2", "idList": "main", "pos": 0.304},
        "id_5": {"id": "id_5", "idList": "main", "pos": 20.4},
        "id_3": {"id": "id_3", "idList": "main", "pos": 44.4},
        "id_7": {"id": "id_7", "idList": "main", "pos": 209.30955},
        "id_12": {"id": "id_12", "idList": "main", "pos": 4444},
        "id_33": {"id": "id_44", "idList": "main", "pos": 3.5},
        "id_32": {"id": "id_32", "idList": "main", "pos": 2.1},
    }
    helper.dirty_cache = False
    pos = helper.convert_index_to_pos("main", 5)
    assert pos > 44.4
    assert pos < 209.30955


def test_keys_present():
    assert "TRELLO_KEY" in os.environ
    assert "TRELLO_TOKEN" in os.environ


def test_get_list():
    helper = trello("none", "none", "none")
    helper._cached_cards = {
        "id_1": {"id": "id_1", "idList": "not_on_thelist"},
        "id_2": {"id": "id_2", "idList": "yes"},
        "id_5": {"id": "id_5", "idList": "DEFINITELY_not"},
        "id_3": {"id": "id_3", "idList": "not_on_thelist"},
        "id_7": {"id": "id_7", "idList": "yes"},
        "id_12": {"id": "id_12", "idList": "yes_but_not_really"},
        "id_33": {"id": "id_44", "idList": "yes"},
        "id_32": {"id": "id_32", "idList": "not_on_thelist"},
    }
    helper.dirty_cache = False
    cards = helper.get_all_cards_on_list("yes")
    assert len(cards) == 3


def test_find_cards():
    helper = trello("none", "none", "none")
    helper._cached_cards = {
        "id_1": {"id": "id_1", "name": "match", "desc": ""},
        "id_2": {"id": "id_2", "name": "main", "desc": "match"},
        "id_3": {"id": "id_3", "name": "skip", "desc": ""},
        "id_4": {"id": "id_4", "name": "main", "desc": "different"},
        "id_5": {"id": "id_5", "name": "fancy"},
        "id_6": {"id": "id_6", "name": "jam", "desc": "hello"},
        "id_7": {"id": "id_7", "name": "train", "desc": "ignore me"},
    }
    helper.dirty_cache = False
    found = helper.find_trello_cards("match")
    assert isinstance(found, list)
    assert len(found) == 2


def test_link_actions_to_cards():
    helper = trello("none", "none", "none")
    cards = [{"id": "card1"}, {"id": "card2"}]
    actions = [
        {"data": {"card": {"id": "card1"}}, "type": "updateCard"},
        {"id": "nothing", "type": "updateCard"},
    ]

    expected_result = [
        {
            "id": "card1",
            "actions": [{"data": {}, "type": "updateCard"}],
        },
        {"id": "card2", "actions": []},
    ]
    result = helper.link_actions_to_cards(cards, actions)
    assert result == expected_result
