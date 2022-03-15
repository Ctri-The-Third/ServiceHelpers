
import json
import logging 
import requests
import re 
import helpers.TrelloHelper as TrelloHelper
import helpers.cfg as cfg



cfg = cfg.getCfgHelper() 
lo = logging.getLogger("ZendeskMapper")

class ZendeskMapper:
    def __init__(self):
        self.ticketObj = []
        self.trelloCards = []
        self._URL = cfg.zendeskURL
        self._headers =  {"Authorization" : "Basic %s" % (cfg.zendeskKey)}
        self._customFieldID = cfg.trelloCustomFieldIDforZD
        self._labelID = cfg.trelloLabelforZDcards
        self._myAssigneeID = cfg.zendeskAgentID
        
        
    def _getTickets(self): #gets the most recently 100 Zendesk tickets.
        url = str.format("{0}/api/v2/search.json?query=form%3A360001936712&sort_by=created_at&sort_order=desc", self._URL)
        response = requests.get(url,headers=self._headers)
        responseObj = {}
        if response.status_code != 200:
            lo.warn("couldn't retrieve zendesk tickets [%s]\n%s" % (response.status_code, response.content))

        try:
            tickets = json.loads(response.content)["results"]
        except:
            lo.warn("Couldn't parse zendesk tickets as json! \n%s" % (response.content))
            return []
        for ticket in tickets: #tickets are now indexed by ID
            if ticket["status"] in ["new","open","pending"]:
                if ticket["assignee_id"] == self._myAssigneeID or ticket["assignee_id"] is None:
                    responseObj["%s" % (ticket["id"])] = ticket
        return responseObj


    def executeMap(self):
        lo.info("beginning zendesk map")
        self.trelloCards = self._getTrelloCards()
        self.ticketObj = self._getTickets()
        self._linkTicketsToCards()
        self._createCardsForUnlinked()
        lo.info("completed zendesk map, existing cards[%i]  tickets[%i]",len(self.trelloCards),len(self.ticketObj))
        
    def executePurge(self,level = 0 ):
        """level 0 = only purge ones in the inbox \n 
        level 1 = purge all of the ones in the board"""
        targetLists = "*" if level == 1 else [cfg.trelloListForNewCards]
        targetFields = [cfg.trelloCustomFieldIDforZD,]

        TrelloHelper.purgeTrelloCards(targetLists=targetLists,customFieldIDs=targetFields)     
        return


    def _linkTicketsToCards(self):
        for cardID in self.trelloCards:
            card = self.trelloCards[cardID]
            
                
            
            for field in card["customFieldItems"]:
                if field["idCustomField"] == self._customFieldID: #this is a ZD card
                    self.trelloCards[card["id"]] = card  #now you can do trelloCards[ID]

                    try: 
                        ticket = self.ticketObj[field["value"]["text"]]
                        ticket["TrelloCardID"] = card["id"]
                    except:
                        #couldn't find matching ticket - the trello card is obsolete if still in untriaged inbox.
                        TrelloHelper.maybeRemoveTrelloCard(card)
            

    def _createCardsForUnlinked(self):
        for ticket in self.ticketObj.values():
            ticketID = ticket["id"]
            if 'TrelloCardID' not in ticket.keys():
                if ticket["assignee_id"] is not None and ticket["assignee_id"] > 0:
                    emoji = "🔥"
                else:
                    emoji = "👋"

                cardName = 'ZD#%s %s - %s' % (ticketID,emoji, ticket["subject"])
                cardDesc = "[Link to ticket](%s/agent/tickets/%s)" %(self._URL,ticketID)
                
                cardObj = TrelloHelper.makeTrelloCard(cardName, description = cardDesc, labelID = self._labelID, zendeskCustomFieldValue= "%s" % (ticketID))
                ticket = self._linkIDs(ticket,cardObj)
        pass
    
    def _linkIDs(self,ticket,TrelloCard):
        try:
            ticket["TrelloCardID"] = TrelloCard["id"]
        except:
            pass
        return ticket

    def _getTrelloCards(self):
        cardObj = {}
        cards = TrelloHelper.getTrelloCards()
        for card in cards:
            cardObj[card["id"]] = card
        return cardObj
    
    def getAssignedUserID(self,ticketID):
        """helper method to get the userID assigned to a ticket. Helpful for when the user doesn't know their own ID"""

        
if __name__ == "__main__":
    zdm = ZendeskMapper()
    zdm.executeMap()