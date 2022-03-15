from asyncio.log import logger
import logging

import re
import requests
import json
import urllib

import helpers.cfg  as cfg

cfg = cfg.getCfgHelper()

logger = logging.getLogger("TrelloHelper")
logger.setLevel(logging.WARN)

def findTrelloCard(regex):
    cards = getTrelloCards()
    for card in cards:
        if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
            return card
    return 

def findTrelloCards(regex):
    cards = getTrelloCards()
    foundCards = []
    for card in cards: 
        if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
            foundCards.append(card)
    return foundCards
    
def purgeTrelloCards(titlePattern = "", descPattern = "", targetLists = [cfg.trelloListForNewCards,] 
, customFieldIDs = []):
    """ 
    * titlePattern and descPattern are both used for regex searches through title and card descriptions 
    * customFieldIDs and targetLists are  an array of IDs. Cards without those fields populated, or outside of those fields will be deleted.
    * targetLists can have the value `[*]` which will result in all lists being considered valid
    """
    cards = getTrelloCards()
    
    for card in cards:
        #search through all cards, attempt to DQ from list. If all checks pass and not DQd, delete
        continueSearch = True
        if targetLists[0] != "*" and card["idList"] not in targetLists:
            continueSearch = False
        if continueSearch and customFieldIDs != []:
            #if we're clear to continue, and there is an ID, scruitinse ID
            continueSearch = False
            for field in card["customFieldItems"]:
                if field["idCustomField"] in customFieldIDs:
                    #card has the right ID 
                    continueSearch = True
        if continueSearch and titlePattern != "" and re.search(titlePattern, card["name"]) == None:
            #no objections found so far, there is a regex for the title, and it missed
            continueSearch = False
        if continueSearch and descPattern != "" and re.search(descPattern, card["desc"]) == None:
            #no objections found so far, there is a regex for the description
            continueSearch = False

        if continueSearch == True:
            #we found no disqualifiers.
            deleteTrelloCard(card["id"])
    return

def getTrelloCards():
    """returns all visible cards from the board"""    
    url = "https://api.trello.com/1/boards/%s/cards" % (cfg.trelloBoardID)
    params = _getTrelloParams()
    params["filter"] = "visible"
    params["customFieldItems"] = "true"
    
    r = requests.get(url,params=params)
    if r.status_code != 200:
        print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
        print(r.content)
        return 
    cards = json.loads(r.content)
    
    return cards
def getTrelloCard(id):
    url = "https://api.trello.com/1/cards/%s" % (id)
    params = _getTrelloParams()
    r = requests.get(url, params = params)
    card = json.loads(r.content)
    return card 

def makeTrelloCard(title, description = None, labelID = None, jiraCustomFieldValue = None, freshdeskCustomFieldValue = None, zendeskCustomFieldValue = None, dueTimestamp = None) :
 
    params = _getTrelloParams()
    params["name"] =title
    
    if description is not None:
        params["desc"] = description
    if labelID is not None:
        params["idLabels"] =  (labelID)
    if dueTimestamp is not None:
        params["due"] = dueTimestamp
    params["idList"] = cfg.trelloListForNewCards

    url = "https://api.trello.com/1/cards/"
    r = requests.post(url,params=params)
    if r.status_code != 200:
        print("Unexpected response code [%s], whilst creating card [%s]" % (r.status_code, title))
        print(r.content)
        return 
    card = json.loads(r.content)
    cardID = card["id"]

    if freshdeskCustomFieldValue is not None: 
        _setFDcustomFieldValue(cardID, freshdeskCustomFieldValue)

    if jiraCustomFieldValue is not None:
        _setJiraCustomFieldValue(cardID,jiraCustomFieldValue)
    
    if zendeskCustomFieldValue is not None:
        _setZDcustomFieldValue(cardID,zendeskCustomFieldValue)

    return card 
def updateTrelloCard( cardid, title, description = None):
    
    params = _getTrelloParams()
    params["name"] = title
    
    if description is not None:
        params["desc"] =description

    url = "https://api.trello.com/1/cards/%s" % (cardid)
    r = requests.put(url,params=params)
    if r.status_code != 200:
        print("ERROR: %s couldn't update the Gmail Trello card's name" % (r.status_code))
    return


def createChecklist(cardID, checklistName = "Todo items"):

    url = "https://api.trello.com/1/checklists"  
    params = _getTrelloParams()
    params["idCard"] = cardID
    params["name"] = checklistName
    
    r = requests.post(url, params=params)
    
    if r.status_code != 200:
        print("ERROR: %s when attempting create a trello checklist (HabiticaMapper) \n%s" % (r.status_code,r.content))
        return 
    checklist = json.loads(r.content)
    return checklist["id"]
def addItemToChecklist(checklistID,text):

    url = "https://api.trello.com/1/checklists/%s/checkItems" % (checklistID)
    params = _getTrelloParams()
    params["pos"] = "bottom"
    params["name"] = text
    r = requests.post(url,params=params)
    if r.status_code != 200:
        print("ERROR: %s when attempting add to a trello checklist (HabiticaMapper) \n%s" % (r.status_code,r.content))
        return 

    return 


def _setFDcustomFieldValue(cardID, value):
    _setCustomFieldValue(cardID,value, cfg.trelloCustomFieldIDforFD)    
    

def _setZDcustomFieldValue(cardID, value):
    _setCustomFieldValue(cardID,value, cfg.trelloCustomFieldIDforZD)


def _setJiraCustomFieldValue(cardID,value):
    _setCustomFieldValue(cardID,value, cfg.trelloCustomFieldIDforJira)

def _setCustomFieldValue(cardID,value, fieldID):
    url = "https://api.trello.com/1/card/%s/customField/%s/item" % (cardID,fieldID)
    data = json.dumps({"value" : {"text" : "%s"% (value)}})
    params = _getTrelloParams()
    headers = {"Content-type": "application/json"}
    r = requests.put(url = url,  data = data,params = params, headers=headers)
    if r.status_code != 200:
        print("Unexpected response code [%s], whilst updating card  %s's field ID %s" % (r.status_code,cardID,fieldID))
        print(r.content)
        
def archiveTrelloCard(trelloCardID):
    url = "https://api.trello.com/1/card/%s" % (trelloCardID)
    params = _getTrelloParams()
    params["closed"] = True
    r = requests.put(url,params=params)
    if r.status_code != 200:
        print(r)
        print(r.reason)

def create_custom_field(field_name) -> str:
    board_id = cfg.trelloBoardID
    url = "https://api.trello.com/1/customFields/"
    params = _getTrelloParams()
    data = {
        "idModel":board_id,
        "modelType":"board",
        "name":field_name,
        "type":"text",
        "pos":"bottom"
    }
    result = requests.post(url,data=data,params=params)
    if result.status_code != 200:
        logger.warn("Creation of a custom field failed!") 
        return ""
    try:
        new_field = json.loads(result.content)["id"]
        return new_field
    except Exception as e:
        logger.warn("Couldn't parse JSON of new field? this shouldn't happen")
    return ""
        

def maybeRemoveTrelloCard(card):
    ### deletes cards that are in the "inbox" field. Leaves cards that are elsewhere.
    try:
        trelloCardID = card["id"]


        if card["idList"] == cfg.trelloListForNewCards:
            #Is it in the inbox? If so, continue
            safeToDeleteFields = []
            safeToDeleteFields.append(cfg.trelloCustomFieldIDforFD)
            safeToDeleteFields.append(cfg.trelloCustomFieldIDforZD)
            safeToDeleteFields.append(cfg.trelloCustomFieldIDforJira)
            for field in card["customFieldItems"]:
                if field["idCustomField"] in safeToDeleteFields:
                #check, is it a FD ticket? if so, this is unclaimed and can be deleted.
                    logging.info("Preparing to remove trello card [%s]" % trelloCardID)
                    deleteTrelloCard(trelloCardID)
    except Exception as e:
        logging.error("Unexpected input whilst pondering whether to remove a trello card\n %s" % card)


def _getTrelloParams():
    params = {
        'key' : cfg.trelloKey,
        'token' : cfg.trelloToken
        }
    return params


def deleteTrelloCard(trelloCardID):

    url = "https://api.trello.com/1/card/%s" % (trelloCardID)
    r = requests.delete(url, params=_getTrelloParams() )
    if r.status_code != 200:
        print(r)
        print(r.reason)
    

if __name__ == "__main__":
    import FreshdeskMapper
    FreshdeskMapper.executeMap()
    FreshdeskMapper.executePurge(0)
    FreshdeskMapper.executePurge(1)