import json
import requests
import logging
import helpers.cfg as cfg
from helpers.cfg import configHelper, jiraDetails
import urllib.parse
import time
import datetime
import helpers.TrelloHelper as TrelloHelper
incomingTickets = {}
existingCards = []

cfg = cfg.configHelper()
lo = logging.getLogger("JiraMapper")

def executeMap():
    lo.info("Beginning jira map")
    global incomingTickets
    global existingCards
    
    
    for target_key in cfg.jiras:
        jira:jiraDetails = cfg.jiras[target_key]
        incomingTickets = incomingTickets | fetchJiraTickets(jira)  #additive dictionary merge.
    existingCards =  fetchTrelloCards(incomingTickets) #must be a dictionary with at least the trello ID as key, and the Jira ID somewhere in the content.
    #if in Incoming, create if necessary.
    #if in existing, but not in incoming, delete if in Inbox.
    createCardsForUnlinked(incomingTickets,existingCards) 
    lo.info("completed jira map, tickets[%i], existing cards[%i]",len(incomingTickets),len(existingCards))
    return


def executePurge(level):
    fieldID =  cfg.trelloCustomFieldIDforJira

    if level == 0:
        targetLists = [cfg.trelloListForNewCards,]
        
    elif level == 1: 
        targetLists = ["*",] 
    else: 
        return 
    
    TrelloHelper.purgeTrelloCards(targetLists = targetLists, customFieldIDs = [fieldID,])
            
        

def fetchJiraTickets(jira_details:jiraDetails):
    
    JiraKey = jira_details.jiraKey
    JiraHost = jira_details.host
    headers = {"Content-Type" : "application/json", "Authorization" : "Basic %s" % JiraKey}
    jql = jira_details.issues_jql
    jql = urllib.parse.quote(jql)
    
    url = "https://%s/rest/api/2/search?jql=%s&fields=key,summary,description,status,priority,assignee" % (JiraHost,jql)
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("ERROR: %s could not fetch Jira tickets\n%s" % (r.status_code, r.content))
        return []
    loadedTickets = json.loads(r.content)
    incomingTickets = {}
    for ticket in loadedTickets["issues"]:
        incomingTickets[ticket["key"]] = ticket
        #print(json.dumps(ticket,indent=2))
    return incomingTickets
        


def createCardsForUnlinked(incomingTickets,existingCards):
    #do asignee check!
    for ticketID in incomingTickets:
        if "TrelloCardID" not in incomingTickets[ticketID]: #no key! create c:
            ticketObj = incomingTickets[ticketID]
            emoji = ""
            if ticketObj["fields"]["assignee"] is None:
                emoji = "👋"
            elif ticketObj["fields"]["assignee"]["accountId"] ==  cfg.jiraUserID:
                emoji = "🔥"
            elif ticketObj["fields"]["assignee"]["accountId"] != cfg.jiraUserID:
                emoji = "👀"
 
            cardName = ('%s %s -  %s' % (ticketID,emoji,   ticketObj["fields"]["summary"]))
            cardDesc = ("https://%s/browse/%s\n\n %s " %(cfg.jiraURL,ticketID,ticketObj["fields"]["description"]))
            
            newCard = TrelloHelper.makeTrelloCard(cardName,description=cardDesc,jiraCustomFieldValue=ticketID,labelID=cfg.trelloLabelForJiraCards)           
            
            
            linkIDs(ticketID,newCard["id"])
            
            try:
                print("Ticket [%s]'s card = [%s]" % (ticketID,ticketObj["TrelloCardID"])) 
            except:
                print("Couldn't find a trello card for [%s]?" % ticketID)



    return





def fetchTrelloCards(incomingTickets):

    cards = TrelloHelper.getTrelloCards()
    global existingCards
    existingCards = {}

    TrelloCustomFieldIDforJira = cfg.trelloCustomFieldIDforJira
    
    for card in cards: #for every trello card 
        for field in card["customFieldItems"]: #loop through its custom fields
            if field["idCustomField"] == TrelloCustomFieldIDforJira: #and if that field is the Jira field (and populated)...
                logging.debug("This is a Jira card! TicketID = %s" % (field["value"]))
                existingCards[card["id"]] = card
                linkIDs(field["value"]["text"],card["id"])
                
        #print(json.dumps(card,indent=2))
    return existingCards
        
def linkIDs(FreshDeskID, TrelloCardID):
    #linking is a local mapping that doesn't extend to Trello or Jira.
    #if an incoming ticket isn't "linked" then we create the card.
    #if an existing trello card isn't "linked" then we delete the card.
    
    #if we get an exception, it can't be linked. If it can't be linked, it might be removed if it's still in the inbox.
    global incomingTickets
    try:
        
        ticketToUpdate = incomingTickets[FreshDeskID]
        ticketToUpdate["TrelloCardID"] = TrelloCardID
        #print ("Linked FD[%s] and Trello[%s]" %(FreshDeskID,TrelloCardID))
    except Exception as e:
        #print(e)
        #print ("Could not link FD[%s] and Trello[%s]. The ticket may be closed/ assigned to someone else?"%(FreshDeskID,TrelloCardID))
        maybeRemoveTrelloCard(TrelloCardID)
        pass
    return

def maybeRemoveTrelloCard(trelloCardID):
    global existingCards
    card = {}
    try:
        card = existingCards[trelloCardID]
    except:
        logging.warn("Something weird went wrong here: Trying to remove a trello card we couldn't link. [%s]" % trelloCardID)
        return
    TrelloHelper.maybeRemoveTrelloCard(card)



def removeTrelloCard(trelloCardID):

    url = "https://api.trello.com/1/card/%s?key=%s&token=%s&closed=true" % (trelloCardID,cfg.getCfgString("TrelloKey"),cfg.getCfgString("TrelloToken"))
    r = requests.put(url)
    if r.status_code != 200:
        print(r)
        print(r.reason)
    