import json
import requests
import urllib.parse
import time
import datetime
import numpy 
import re
import math
import logging
import helpers.TrelloHelper as TrelloHelper
import helpers.cfg as cfg

#get all open FD tickets
#get all open trello cards

#cross reference all Trello Cards with a custom field to their FD ticket brethren
#turn unaffilliated tickets into cards.

cfg = cfg.configHelper()
lo = logging.getLogger("FreshdeskMapper")
def fetchFDtickets(nestedObj):
    ticketObj = nestedObj['ticketObj']
    
    #returns all tickets associated with me, or unassigned
    url = '%sapi/v2/search/tickets?query="((agent_id:%s OR agent_id:null) AND (status:2 OR status:3))"' % (cfg.FreshdeskURL,cfg.FreshDeskAgentID)
    AuthString = "Basic %s" % (cfg.FreshdeskKey)
    r = requests.get (
        url,
        headers = {'Authorization':AuthString,
        'Content-Type':'application/json'}
        )
 
    if r.status_code != 200:
        logging.warn("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
        print(r.content)
        return 
    
    tickets = json.loads(r.content)
    for ticket in tickets["results"]:
        if ticket["id"] not in ticketObj and ( ticket["status"] == 2 or ticket["status"] == 3):
            ticketObj['%s' % (ticket["id"])] = ticket
    
    nestedObj['ticketObj'] = ticketObj
    return nestedObj



def fetchTrelloCards(nestedObj):
    cardObj = nestedObj['cardObj']
    ticketObj = nestedObj['ticketObj']

    cards = TrelloHelper.getTrelloCards()    

    for card in cards:
        for field in card["customFieldItems"]:
            if field["idCustomField"] ==  cfg.trelloCustomFieldIDforFD:
                cardObj[card["id"]] = card
                try: 
                    ticket = ticketObj[field["value"]["text"]]
                    #take the FD ticket value from the Card's custom field, and put the cardID into the ticketObject
                    ticketObj[field["value"]["text"]] = linkIDs(field["value"]["text"],ticket,card)
                    
                except: 
                    #card exists but not ticket? feed it to the deletion checker!
                    maybeRemoveTrelloCard(card)
                    #stop tracking this trello card - either it's deleted, or deliberately being preserved.
                    del cardObj[card["id"]] 
                    pass

                
                
        #print(json.dumps(card,indent=2))
    nestedObj['cardObj'] = cardObj
    nestedObj['ticketObj'] = ticketObj
    return nestedObj
        
def linkIDs(FreshDeskID, ticket, TrelloCard  ):
    ticket["TrelloCardID"] = TrelloCard["id"]
    return ticket



def createCardsForUnlinked(nestedObj):
    ticketObj = nestedObj['ticketObj']
    cardObj = nestedObj['cardObj']

    #run through all our tickets
    #if they don't have cardIDs, create.


    for ticketID in ticketObj:
        ticket = ticketObj[ticketID]
        
        
        if 'TrelloCardID' not in ticket.keys(): #no trello key!  create c:
            if ticket["responder_id"] is not None and ticket["responder_id"] > 0:
                emoji = "🔥"
            else:
                emoji = "👋"

            cardName = 'FD#%s %s - %s' % (ticketID,emoji, ticket["subject"])
            cardDesc = "[Link to ticket](%sa/tickets/%s)" %(cfg.FreshdeskURL,ticketID)
            
            cardObj = TrelloHelper.makeTrelloCard(cardName, description = cardDesc, labelID = cfg.getCfgString("TrelloLabelForFDcards"), freshdeskCustomFieldValue=  "%s" % (ticketID))
            
            ticket = linkIDs(ticketID,ticket,cardObj)
            

def UpdateTrelloWorkLogSummary(numMissing, strings):
    cardID = _getTrelloWorklogSummary()
    if cardID == None:
        cardID = _createTrelloWorklogSummary(numMissing, strings)
    else: 
        _updateTrelloWorklogSummary(cardID,numMissing, strings)

def _getTrelloWorklogSummary():
    

    card = TrelloHelper.findTrelloCards("^Missing \[[0-9]*\] worklogs for Freshdesk") 
    if len(card) > 1:
        card = card[0]
    else:
        logging
        return
    if card is not None and "id" in card: 
        return card["id"]
    return None
def _updateTrelloWorklogSummary(cardID, countOfMissing, strings): 
    outputString = ""
    for string in strings: 
        outputString += "%s\n" % (string)
    TrelloHelper.updateTrelloCard(cardID,"Missing [%s] worklogs for Freshdesk" % (countOfMissing), description= outputString )

def _createTrelloWorklogSummary(countOfMissing, strings):

    outputString = ""
    for string in strings: 
        outputString += "%s\n" % (string)
    card = TrelloHelper.makeTrelloCard("Missing [%s] worklogs for Freshdesk" % (countOfMissing), description= outputString )
    return card["id"]

def maybeRemoveTrelloCard(card):
    TrelloHelper.maybeRemoveTrelloCard(card)


def executeMap():
    lo.info("Beginning Freshdesk map")
    #use of globals wasn't smart, Should've stuck to parameter passing
    FDMap = {"cardObj" : {},"ticketObj":{}}
    _cardObj= {} #keys = cards. Contents = ticket reference
    _ticketObj = {} #keys = IDs


    FDMap = fetchFDtickets(FDMap)
    FDMap = fetchTrelloCards(FDMap)
    createCardsForUnlinked(FDMap)
    lo.info("Freshdesk map complete cards [%s] tickets[%s]",len(FDMap["cardObj"]),len(FDMap["ticketObj"]))

def executeWorklogsRefresh():
    lo.info("Starting worklog refresh")
    targetDate = datetime.datetime.now()
    ticketsMissingFields = []
    tickets = []
    for i in range(0,7):
        targetDate = datetime.datetime.now()
        targetDate = targetDate - datetime.timedelta(days=i)
        
        tickets_updated_onDate = _getFDTickets_updated_on(targetDate.strftime(r"%Y-%m-%d"))
        for ticket in tickets_updated_onDate:
            tickets.append(ticket["id"])
            if (ticket["type"] == None or ticket["custom_fields"]["category"] == None) and( ticket["responder_id"] == cfg.FreshDeskAgentID):
                ticketsMissingFields.append(ticket["id"])
    lo.info("completed worklog refresh, [%i] tickets", len(tickets_updated_onDate))
    
    
    
    strings = []
    totalTime = 0 
    totalMissing = 0
    
    for ticketID in tickets:
        logs = _getWorklogs(ticketID)
        
        comments = _getCountcomments(ticketID)
        totalTime += sum(logs)
        if len(logs) < comments:
            totalMissing += 1 
            strings.append(" [#%s](%sa/tickets/%s) - %sm, missing [**%s**] worklogs" % (ticketID,cfg.FreshdeskURL,ticketID,sum(logs), (comments - len(logs)) ))
    for ticketID in ticketsMissingFields:
        strings.append(" [#%s](%sa/tickets/%s) - missing expected fields" % (ticketID,cfg.FreshdeskURL,ticketID ))
    strings.append("\n")
    strings.append("total time logged = %sh:%sm" % (math.floor(totalTime/60), int(abs(math.remainder(totalTime,60)))))
    if totalMissing > 0:
        UpdateTrelloWorkLogSummary(totalMissing,strings)

    
    #get tickets by filter
    #for each ticket
    #   get comments
    #   get worklogs
    
    #generate summary trello ticket if needed


def _getWorklogs(ticketID):
     #/api/v2/tickets/[id]/time_entries
    #returns all tickets associated with me, or unassigned

    returnObj = []
    getNextPage = True
    oldResponse = ""
    countOfMessages = 0
    currentPage = 0
    while getNextPage == True:
        currentPage = currentPage + 1


        url = '%sapi/v2/tickets/%s/time_entries' % (cfg.FreshdeskURL,ticketID)
        AuthString = "Basic %s" % (cfg.FreshdeskKey) 
        r = requests.get (
            url,
            headers = {'Authorization':AuthString,
            'Content-Type':'application/json'}
            )
    
        if r.status_code != 200:
            logging.warn("Unexpected response code [%s], whilst getting worklogs for %s" % (r.status_code,ticketID))
            print(r.content)
            return 


        if r.content == oldResponse:
            getNextPage = False
        else :
            oldResponse = r.content

        
        response = json.loads(r.content)
        
        for worklog in response:
            if "agent_id" in worklog and "time_spent" in worklog:
                if worklog["agent_id"] == cfg.FreshDeskAgentID and re.match(r"[0-9]{2}:[0-9]{2}",worklog["time_spent"]): #it's mine
                    hours = int(worklog["time_spent"][0:2])
                    minutes = int(worklog["time_spent"][-2:])
                    minutes = minutes + (hours * 60)
                    returnObj.append(minutes)
                 
    if len(returnObj) > 0:
        logging.debug(returnObj)
    
    
    return returnObj

def _getCountcomments(ticket):
    #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
    getNextPage = True
    oldResponse = ""
    countOfMessages = 0
    currentPage = 0
    while getNextPage == True:
        currentPage = currentPage + 1
        url = '%sapi/v2/tickets/%s/conversations?page=%s' % (cfg.FreshdeskURL,ticket,currentPage)
        AuthString = "Basic %s" % (cfg.FreshdeskKey)
        try:
            r = requests.get (
                url,
                headers = {'Authorization':AuthString,
                'Content-Type':'application/json'}
            )
            conversation = json.loads(r.content)
            if len(conversation) < 30:
                getNextPage = False
        except Exception as e:
            return []
        
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
            print(r.content)
            return 
        if r.content == oldResponse:
            getNextPage = False
            
        else :
            oldResponse = r.content
            maybeJSON = r.content

     
            for message in conversation:
                
                if message["user_id"] == cfg.FreshDeskAgentID:
                    countOfMessages += 1 
    if countOfMessages > 0:
        logging.debug("[%s]" % countOfMessages)    
    return countOfMessages

def executePurge(level):
    fieldID = cfg.trelloCustomFieldIDforFD
    
    if level == 0:
        targetLists = [cfg.trelloListForNewCards,] 
    elif level == 1: 
        targetLists = ["*",] 
    else: 
        return 
    
    TrelloHelper.purgeTrelloCards(targetLists = targetLists, customFieldIDs = [fieldID,])

def _getFDTickets_updated_on(targetdate):

    getNextPage = True
    oldResponse = ""
    collatedTickets = []
    currentPage = 0
    while getNextPage == True:
        currentPage = currentPage + 1
        
        url = '%sapi/v2/search/tickets?page=%s&query="updated_at:\'%s\'"' % ( cfg.FreshdeskURL,currentPage,targetdate)
        
        AuthString = "Basic %s" % (cfg.FreshdeskKey)
        try:
            r = requests.get (
                url,
                headers = {'Authorization':AuthString,
                'Content-Type':'application/json'}
            )
            tickets = json.loads(r.content)
        except Exception as e:
            return []
        
        if r.status_code != 200:
            print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
            print(r.content)
            return 
        if r.content == oldResponse:
            getNextPage = False
            
        else :
            oldResponse = r.content
            maybeJSON = r.content

            if "results" in tickets: 
                for ticket in tickets["results"]:
                    collatedTickets.append(ticket)
    return collatedTickets



if __name__ == "__main__":
    #cardID = _getTrelloWorklogSummary()
    
    executePurge()
    #23358