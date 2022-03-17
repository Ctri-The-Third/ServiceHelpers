from asyncio.log import logger
import logging

import re
import requests
import json
import urllib



lo = logging.getLogger("TrelloHelper")
lo.setLevel(logging.WARN)

class trello():
    def __init__(self, board_id, key, token) -> None:
        self.board_id = board_id
        self.key = key
        self.token = token
        pass

    def find_trello_card(self, regex):
        cards = self.fetch_trello_cards()
        for card in cards:
            if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
                return card
        return 

    def find_trello_cards(self,regex):
        cards = self.fetch_trello_cards()
        foundCards = []
        for card in cards: 
            if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
                foundCards.append(card)
        return foundCards
    
    def purge_trello_cards(self,titlePattern = "", descPattern = "", targetLists = [] 
    , customFieldIDs = []):
        """ 
        * titlePattern and descPattern are both used for regex searches through title and card descriptions 
        * customFieldIDs and targetLists are  an array of IDs. Cards without those fields populated, or outside of those fields will be deleted.
        * targetLists can have the value `[*]` which will result in all lists being considered valid
        """
        cards = self.fetch_trello_cards()
        
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
                self.deleteTrelloCard(card["id"])
        return

    def fetch_trello_cards(self):
        """returns all visible cards from the board"""    
        url = "https://api.trello.com/1/boards/%s/cards" % (self.board_id)
        params = self._get_trello_params()
        params["filter"] = "visible"
        params["customFieldItems"] = "true"
        
        r = requests.get(url,params=params)
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
            print(r.content)
            return 
        cards = json.loads(r.content)
        
        return cards
    def get_trello_card(self,id):
        url = "https://api.trello.com/1/cards/%s" % (id)
        params = self._get_trello_params()
        r = requests.get(url, params = params)
        card = json.loads(r.content)
        return card 

    def create_card(self,title, list_id, description = None, labelID = None,  dueTimestamp = None) :
    
        params = self._get_trello_params()
        params["name"] =title
        
        if description is not None:
            params["desc"] = description
        if labelID is not None:
            params["idLabels"] =  (labelID)
        if dueTimestamp is not None:
            params["due"] = dueTimestamp
        params["idList"] = list_id

        url = "https://api.trello.com/1/cards/"
        r = requests.post(url,params=params)
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst creating card [%s]" % (r.status_code, title))
            print(r.content)
            return 
        card = json.loads(r.content)
        return card 


    def update_card( self, card_id, title, description = None):
        
        params = self._get_trello_params()
        params["name"] = title
        
        if description is not None:
            params["desc"] =description

        url = "https://api.trello.com/1/cards/%s" % (card_id)
        r = requests.put(url,params=params)
        if r.status_code != 200:
            print("ERROR: %s couldn't update the Gmail Trello card's name" % (r.status_code))
        return


    def create_checklist_on_card(self, cardID, checklistName = "Todo items") -> str:
        "create a checklist on an existing card, returns the ID for use."
        url = "https://api.trello.com/1/checklists"  
        params = self._get_trello_params()
        params["idCard"] = cardID
        params["name"] = checklistName
        
        r = requests.post(url, params=params)
        
        if r.status_code != 200:
            print("ERROR: %s when attempting create a trello checklist (HabiticaMapper) \n%s" % (r.status_code,r.content))
            return 
        checklist = json.loads(r.content)
        return checklist["id"]


    def add_item_to_checklist(self, checklistID, text):
        url = "https://api.trello.com/1/checklists/%s/checkItems" % (checklistID)
        params = self._get_trello_params()
        params["pos"] = "bottom"
        params["name"] = text
        r = requests.post(url,params=params)
        if r.status_code != 200:
            print("ERROR: %s when attempting add to a trello checklist (HabiticaMapper) \n%s" % (r.status_code,r.content))
            return 
        return 

    def delete_checklist_item(self,checklist_id, checklist_item_id):
        url = "https://api.trello.com/1/checklists/%s/checkItems/%s" % (checklist_id,checklist_item_id)
        params = self._get_trello_params()
        r = requests.delete(url,params=params)
        if r.status_code != 200:
            lo.error("ERROR: %s, Couldn't delete trello checklist item %s " % (r.status_code,checklist_item_id))


    def _setCustomFieldValue(self, cardID,value, fieldID):
        url = "https://api.trello.com/1/card/%s/customField/%s/item" % (cardID,fieldID)
        data = json.dumps({"value" : {"text" : "%s"% (value)}})
        params = self._get_trello_params()
        headers = {"Content-type": "application/json"}
        r = requests.put(url = url,  data = data,params = params, headers=headers)
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst updating card  %s's field ID %s" % (r.status_code,cardID,fieldID))
            print(r.content)
        

    def archiveTrelloCard(self,trelloCardID):
        url = "https://api.trello.com/1/card/%s" % (trelloCardID)
        params = self._get_trello_params()
        params["closed"] = True
        r = requests.put(url,params=params)
        if r.status_code != 200:
            print(r)
            print(r.reason)


    def create_custom_field(self,field_name) -> str:
        board_id = self.board_id
        url = "https://api.trello.com/1/customFields/"
        params = self._get_trello_params()
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
        

    def _get_trello_params(self):
        params = {
            'key' : self.key,
            'token' : self.token
            }
        return params


    def deleteTrelloCard(self,trelloCardID):

        url = "https://api.trello.com/1/card/%s" % (trelloCardID)
        r = requests.delete(url, params=self._get_trello_params() )
        if r.status_code != 200:
            print(r)
            print(r.reason)
        


    def fetch_checklist_content(self, checklist_id) ->list:
        url = "https://api.trello.com/1/checklists/%s" % (checklist_id)
        params = self._get_trello_params()
        r = requests.get(url=url,params=params)
        if r.status_code != 200:
            lo.error("Couldn't fetch checklist content %s" % (r.status_code, r.content))
        try:
            content = json.loads(r.content)["checkItems"]
        except Exception as e:
            lo.error(f"Couldn't parse the json from the fetch_checklist_content method for {checklist_id}")
        return content