import sys 
sys.path.append("")
import os 

from serviceHelpers.trello import trello

TEST_BOARD_ID = "5f0dee6c5026590ce300472c"
TEST_LIST_ID = "5f0dee6c5026590ce3004732"
TEST_LIST_ID_TWO = "61d8367af7a2942f50afd468"

def test_trello_sort():
    helper = trello("none","none","none")

    list_to_sort = [
        {"pos":300},
        {"pos":0.304},
        {"pos":20.4},
        {"pos":44.4},
        {"pos":209.30955}
    ]
    list_to_sort = helper._sort_trello_cards_list(list_to_sort)
    last_pos = 0 
    for card in list_to_sort:
        assert card["pos"] > last_pos
        last_pos = card["pos"]

def test_trello_sort_array():
    helper = trello("none","none","none")
    cards = {
        "id_1":{"id":"id_1","pos":300},
        "id_2":{"id":"id_2","pos":0.304},
        "id_5":{"id":"id_5","pos":20.4},
        "id_3":{"id":"id_3","pos":44.4},
        "id_7":{"id":"id_7","pos":209.30955},
        "id_12":{"id":"id_12","pos":4444},
        "id_33":{"id":"id_44","pos":3.5},
        "id_32":{"id":"id_32","pos":2.1},
        
    }
    sorted_cards = helper._sort_trello_cards_dict(cards)
    last_pos = 0
    for _,card in sorted_cards.items():
        assert card["pos"] >= last_pos
        last_pos = card["pos"]


def test_convert_index_to_pos():
    helper = trello("none","none","none")
    helper._cached_cards = {
        "id_1":{"id":"id_1","idList":"main","pos":300},
        "id_2":{"id":"id_2","idList":"main","pos":0.304},
        "id_5":{"id":"id_5","idList":"main","pos":20.4},
        "id_3":{"id":"id_3","idList":"main","pos":44.4},
        "id_7":{"id":"id_7","idList":"main","pos":209.30955},
        "id_12":{"id":"id_12","idList":"main","pos":4444},
        "id_33":{"id":"id_44","idList":"main","pos":3.5},
        "id_32":{"id":"id_32","idList":"main","pos":2.1},
        
    }
    helper.dirty_cache = False
    pos = helper.convert_index_to_pos("main",5)
    assert pos > 44.4
    assert pos < 209.30955
    

def test_keys_present():
    assert "TRELLO_KEY" in os.environ
    assert "TRELLO_TOKEN" in os.environ

def test_trello_get_cards():
    helper = trello(TEST_BOARD_ID,os.environ["TRELLO_KEY"],os.environ["TRELLO_TOKEN"])
    cards = helper.fetch_trello_cards()
    for card in cards:
        assert "id" in card
    
    assert len(cards) == len(helper._cached_cards)

def test_get_list():
    helper = trello("none","none","none")
    helper._cached_cards = {
        "id_1":{"id":"id_1","idList":"not_on_thelist"},
        "id_2":{"id":"id_2","idList":"yes"},
        "id_5":{"id":"id_5","idList":"DEFINITELY_not"},
        "id_3":{"id":"id_3","idList":"not_on_thelist"},
        "id_7":{"id":"id_7","idList":"yes"},
        "id_12":{"id":"id_12","idList":"yes_but_not_really"},
        "id_33":{"id":"id_44","idList":"yes"},
        "id_32":{"id":"id_32","idList":"not_on_thelist"},
        
    }
    helper.dirty_cache = False
    cards = helper.get_all_cards_on_list("yes")
    assert(len(cards) == 3 )


def test_find_cards():
    helper = trello("none","none","none")
    helper._cached_cards = {
        "id_1":{"id":"id_1","name":"match","desc":""},
        "id_2":{"id":"id_2","name":"main","desc":"match"},
        "id_3":{"id":"id_3","name":"skip","desc":""},
        "id_4":{"id":"id_4","name":"main","desc":"different"},
        "id_5":{"id":"id_5","name":"fancy"},
        "id_6":{"id":"id_6","name":"jam","desc":"hello"},
        "id_7":{"id":"id_7","name":"train","desc":"ignore me"},
        
    }
    helper.dirty_cache = False
    found = helper.find_trello_cards("match")
    assert isinstance(found,list)
    assert len(found) == 2


def test_create_card_at_correct_position():
    helper = trello(TEST_BOARD_ID,os.environ["TRELLO_KEY"],os.environ["TRELLO_TOKEN"])
    card = helper.create_card("TEST CARD, PLEASE IGNORE",TEST_LIST_ID,"A temporary card that should get deleted",position=0)
    helper.deleteTrelloCard(card["id"])
    
    card = helper.create_card("TEST CARD, PLEASE IGNORE",TEST_LIST_ID,"A temporary card that should get deleted",position=3)
    helper.deleteTrelloCard(card["id"])
    

    card = helper.create_card("TEST CARD, PLEASE IGNORE",TEST_LIST_ID,"A temporary card that should get deleted",position=-1)
    helper.deleteTrelloCard(card["id"])

def test_move_card_from_list_to_list():
    helper = trello(TEST_BOARD_ID,os.environ["TRELLO_KEY"],os.environ["TRELLO_TOKEN"])
    card = helper.create_card("TEST CARD, PLEASE IGNORE",TEST_LIST_ID)
    helper.update_card(card["id"], card["name"],new_list_id=TEST_LIST_ID_TWO)
    new_card = helper.fetch_trello_card(card["id"])

    helper.deleteTrelloCard(new_card["id"])
    assert card["id"] == new_card["id"]
    assert new_card.get("idList","") == TEST_LIST_ID_TWO



def test_update_card():
    old_ts = "2022-10-01 23:59:00"
    new_ts = "2011-11-11 11:11:00"
    helper = trello(TEST_BOARD_ID,os.environ["TRELLO_KEY"],os.environ["TRELLO_TOKEN"])
    card = helper.create_card("TEST CARD, PLEASE IGNORE",TEST_LIST_ID,dueTimestamp=old_ts)
    helper.update_card(card["id"], card["name"], new_due_timestamp=new_ts)
    new_card = helper.find_trello_card(card["id"])

    helper.deleteTrelloCard(new_card["id"])
    assert new_card["due"] == "2011-11-11T11:11:00.000Z"
    
