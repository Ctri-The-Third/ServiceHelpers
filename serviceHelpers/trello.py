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
        self._cached_cards = {} #listID into list of cards, sorted by their IDs 
        self.dirty_cache = True
        pass

    def find_trello_card(self, regex):
        "uses regexes to search name and description of cached / fetched cards. Returns the first it finds."
        cards = self.fetch_trello_cards() if self.dirty_cache else self._cached_cards
        
        for card in cards:
            if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
                return card
        return 

    def find_trello_cards(self,regex):
        "uses regexes to search name and description of cached / fetched cards. Returns all cards found."

        cards = self.fetch_trello_cards() if self.dirty_cache else self._cached_cards
        foundCards = []
        for card in cards: 
            if re.search(regex,card["name"]) or re.search(regex,card["desc"]):
                foundCards.append(card)
        return foundCards

    def search_trello_cards(self,search_criteria,board_id = None) -> list:
        "uses the trello search criteria, can return archived cards"
        url = "https://api.trello.com/1/search"
        params = self._get_trello_params()
        params['card_fields'] = 'desc, name'
        params['modelTypes'] = 'cards'
        if board_id:
            params["idBoards"] = board_id
        params["query"] = search_criteria
        r = requests.get(url, params = params)
        matching_summaries = json.loads(r.content)["cards"]
        return matching_summaries
        

    def purge_trello_cards(self,titlePattern = "", descPattern = "", targetLists = [] 
    , customFieldIDs = []):
        """ 
        * titlePattern and descPattern are both used for regex searches through title and card descriptions 
        * customFieldIDs and targetLists are  an array of IDs. Cards without those fields populated, or outside of those fields will be deleted.
        * targetLists can have the value `[*]` which will result in all lists being considered valid
        """
        cards = self.fetch_trello_cards() if self.dirty_cache else self._cached_cards
                
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
                self.dirty_cache = True
        return
    def get_all_cards_on_list(self, list_id):
        """Returns all the visible cards on a given list"""
        if self.dirty_cache:
            self.fetch_trello_cards() 
        cards = self._cached_cards
        filtered_cards = {k:v for k,v in cards.items() if v["idList"] == list_id}
        return filtered_cards
        #creates Key:value FOR - (for each Key, value in cards) BUT ONLY IF the list_id matches

    def fetch_trello_cards(self):
        """returns all visible cards from the board"""    
        url = "https://api.trello.com/1/boards/%s/cards" % (self.board_id)
        params = self._get_trello_params()
        params["filter"] = "visible"
        
        #params["customFieldItems"] = "true"
        
        r = requests.get(url,params=params)
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
            print(r.content)
            return 
        
        cards = json.loads(r.content)
        self._populate_cache(cards)
        self.dirty_cache = False
        return cards

    def fetch_trello_card(self,id):
        "returns a single trello card"
        url = "https://api.trello.com/1/cards/%s" % (id)
        params = self._get_trello_params()
        r = requests.get(url, params = params)
        card = json.loads(r.content)
        
        self._populate_cache([card])
        return card 


    def get_trello_card(self,id):
        "gets a card from the cache, or fetches it"
        if id in self._cached_cards:
            return self._cached_cards[id]
        else:
            return self.fetch_trello_card(id)

    def convert_index_to_pos(self, list_id,position) -> float:
        "takes the index of a card, and finds a suitable position float value for it"
        cards = self.get_all_cards_on_list(list_id)
        cards = self._sort_trello_cards_dict(cards)
        

        cards = list(cards.items())
        if len(cards) == 1:
            return cards[0][1].get("pos",0)+1
        if len(cards) == 0:
            return 0 
        if position == 0:
            return (cards[0][1].get("pos",0))/2
        if position == -1:
            return (cards[len(cards)-1][1].get("pos",0)+0.0000001)
        
        try:
            card = cards[position]
            prev_card = cards[position-1]
            pos = (prev_card[1]["pos"] + card[1]["pos"])/2
            return pos
        except IndexError:
            lo.error("got a horrible value when trying to convert index to pos value - index=[%s], len=[%s]")
            return 0 
        
         

    def create_card(self,title, list_id, description = None, labelID = None,  dueTimestamp = None, position:int = None):
        "`position` is the numerical index of the card on the list it's appearing on. 0 = top, 1 = second, -1 = last"

        params = self._get_trello_params()
        params["name"] =title
        
        if description is not None:
            params["desc"] = description
        if labelID is not None:
            params["idLabels"] =  (labelID)
        if dueTimestamp is not None:
            params["due"] = dueTimestamp
        if position is not None and position >= 0:
            #if position is -1 (bottom) then use default behaviour
            params["pos"] = self.convert_index_to_pos(list_id,position)
        params["idList"] = list_id

        url = "https://api.trello.com/1/cards/"
        r = requests.post(url,params=params)
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst creating card [%s]" % (r.status_code, title))
            print(r.content)
            return 
        card = json.loads(r.content)
        self.dirty_cache = True
        return card 


    def update_card( self, card_id, title, description = None, pos = None):
        
        params = self._get_trello_params()
        params["name"] = title
        
        if description is not None:
            params["desc"] =description
        if pos is not None:
            params["pos"] = pos
        url = "https://api.trello.com/1/cards/%s" % (card_id)
        r = requests.put(url,params=params)
        if r.status_code != 200:
            print("ERROR: %s couldn't update the Gmail Trello card's name" % (r.status_code))
        self.dirty_cache = True
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
        self.dirty_cache = True 
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
        self.dirty_cache = True  
        return 

    def delete_checklist_item(self,checklist_id, checklist_item_id):
        url = "https://api.trello.com/1/checklists/%s/checkItems/%s" % (checklist_id,checklist_item_id)
        params = self._get_trello_params()
        r = requests.delete(url,params=params)
        if r.status_code != 200:
            lo.error("ERROR: %s, Couldn't delete trello checklist item %s " % (r.status_code,checklist_item_id))
        self.dirty_cache = True 

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
        self.dirty_cache = True 
 

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
            return 
        self.dirty_cache = True
        


    def fetch_checklist_content(self, checklist_id) ->list:
        url = "https://api.trello.com/1/checklists/%s" % (checklist_id)
        params = self._get_trello_params()
        r = requests.get(url=url,params=params)
        if r.status_code != 200:
            lo.error("Couldn't fetch checklist content %s - %s", r.status_code, r.content)
        try:
            content = json.loads(r.content)["checkItems"]
        except Exception as e:
            lo.error(f"Couldn't parse the json from the fetch_checklist_content method for {checklist_id}")
        return content


    def _sort_trello_cards_list(self, array_of_cards:list) -> list:
        "Takes an arbitrary list of cards and sorts them by their position value if present"
        array_of_cards = sorted(array_of_cards,key=lambda card:card.get("pos",0))
        
        return array_of_cards

    def _sort_trello_cards_dict(self,dict_of_cards:dict) -> dict:
        sorted_dict =  {k:v for k,v in sorted(dict_of_cards.items(), key=lambda x:x[1].get("pos"))}
        #note for future C'tri reading this - the part that does the sorting is this:
        #key=lambda x:x[1].get("pos")
        #in this case, x is a tuple comprised of K and V
        #x[1] is the card - a dict, and x[0] is the id, a string.
        return sorted_dict

    def _populate_cache(self,array_of_cards:list) -> None:
        "takes a list of cards and puts them into the _cached_cards dict"
        for card in array_of_cards:
            card:dict
            if "id" not in card:
                lo.warn("skipped adding a card to the cache, no id present")
                continue

            self._cached_cards[card.get("id")] = card 