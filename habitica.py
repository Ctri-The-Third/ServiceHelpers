import logging
import json
import requests 
import time 
import datetime
import re


import helpers.cfg as cfg
import helpers.TrelloHelper as TrelloHelper

cfg = cfg.getCfgHelper() 
lo = logging.getLogger("HabiticaMapper")
#on startup and at midnight, do the following
# get today's dailies

# every 5 minutes, commit completed dailies to habitica


# search for existing trello cards, including archived ones.
# if a Trello card for today has been archived, then feedback to habitica it's complete
# get new dailies
# if daily is active today, and has not already been completed today
def fetchHabiticaDailies(dateAsString):
    url =  "https://habitica.com/api/v3/tasks/user?type=dailys&dueDate=%s" % (dateAsString)
    headers = _getHabiticaHeaders()

    r = requests.get(url,headers=headers)
    dailies = json.loads(r.content)
    
    if "error" in dailies:
        lo.error("Couldn't get habitica dailies - %s",dailies["error"])
        return []
    activeDailies = []
    
    
    for daily in dailies["data"]:
        if daily["isDue"]:        
            activeDailies.append(daily)

    return activeDailies
def searchForMatchingCards(activeDailies):
    linkedCards = {}
    url = "https://api.trello.com/1/search"
    headers = _getHabiticaHeaders()
    params = _getTrelloSearchParams()
    
    for daily in activeDailies:
        params["query"] = _generateTrelloIDForDaily(daily)
        r = requests.get(url,headers=headers, params = params)
        matchingCards = json.loads(r.content)
        for matchingCardSummary in matchingCards['cards']:
            linkedCards[daily["id"]] = getTrelloCard(matchingCardSummary["id"])
    return linkedCards

def getTrelloCard(id):
    return TrelloHelper.getTrelloCard(id)

def createTrelloCard(daily):

    due = datetime.datetime.now().strftime("%Y-%m-%d 23:59:00")
    desc= "%s\n\\Habitica Map ID[%s]" % (daily["notes"], _generateTrelloIDForDaily(daily))
    
    newCard = TrelloHelper.makeTrelloCard(daily["text"],description=desc,labelID=cfg.trelloLabelForHabiticaCards,dueTimestamp=due)    
    cardID = newCard["id"]
    
  
    if len(daily["checklist"]) > 0:
        checklistID = TrelloHelper.createChecklist(cardID)
        for checkListItem in daily["checklist"]:
            TrelloHelper.addItemToChecklist(checklistID,checkListItem["text"])
    return 

def completeArchivedDailies(activeDailies, matchingCards):
    #for each matching card -is it archived?
    #is the matching card's habitica task already complete? #daily[completed]

    for habiticaid in matchingCards:
        card = matchingCards[habiticaid]
        if card["closed"]:
            lo.debug("Card is archived, try and complete daily!")
            for daily in activeDailies:
                if daily["id"] == habiticaid:
                    if daily["completed"] == False:
                        completeDaily(daily["id"])
                        
    return 

def completeDaily(dailyID):
    url = "https://habitica.com/api/v3/tasks/%s/score/up" % (dailyID)
    headers = _getHabiticaHeaders()
    r = requests.post(url,headers=headers)
    if r.status_code != 200:
        print ("Unexpected error whilst completing a habitica task! \n%s\t%s" % (r.status_code, r.content))


def createCardsForNewDailies(activeDailies,matchingCards):
    for daily in activeDailies:
        if daily["id"] not in matchingCards:
            #print ("Didn't find a card. Creating! %s" % (daily["text"]))  
            createTrelloCard(daily)
    return 
 
def resetDailies():
    """Call's the endpoint that triggers the end of day process to executes"""
    url = "https://habitica.com/api/v3/cron"
    headers = _getHabiticaHeaders()
    r = requests.post(url,headers=headers)
    if r.status_code != 200:
        lo.warning("Failed to request Habitica reset!!")

def _getHabiticaHeaders():
    headersObj = {
        "x-client" : "d97d7173-7502-405a-89b7-fe58b1a2e967-Presence", #habitica asks app authors to self-report their identity - please change this if you modify the habitica code.
        "x-api-user" : cfg.habitica_user_id,
        "x-api-key" : cfg.habiticaKey
    } 
    return headersObj
def _getTrelloSearchParams():
    params = TrelloHelper._getTrelloParams()
    params['card_fields'] = 'desc, name'
    params['modelTypes'] = 'cards'
    
    return params

def _generateTrelloIDForDaily(daily):
    now = datetime.datetime.now()
    nowStr = now.strftime(r"%Y%m%d")
    dailyIDString = "%s-%s" % (daily["id"][0:8], nowStr)
    return dailyIDString


def executePurge(level = 0 ):
    """level 0 = only purge ones in the inbox \n 
    level 1 = purge all of the ones in the board"""

    descTarget = r"(Habitica Map ID\[[a-f0-9]{8}-[0-9]{4}[01][0-9][0-3][0-9]\])"
    if level == 0 or level == "0":
        targetLists = [cfg.getCfgString("TrelloListForNewCards"),] 
    elif level == 1 or level == "1": 
        targetLists = ["*",] 
    else: 
        return 

    TrelloHelper.purgeTrelloCards(descPattern=  descTarget, targetLists=targetLists)     

    return



def executeMap():
    lo.info("Beginning habitica map")
    resetDailies()
    activeDailies = fetchHabiticaDailies(datetime.datetime.now().strftime(r"%Y-%m-%d"))
    #print("%s active dailies!" % (len(activeDailies)))
    #we've got a list of dailies \0/ 
    matchingCards = searchForMatchingCards(activeDailies)
    #print("%s matching cards!" % (len(matchingCards)))
    #if we find either an active or archived card, the daily has already been created in Trello and we can skip
    #for active dailies without matchingCards - should only happen at the start of the day, but may also happen if a new daily is created on Habitica

    createCardsForNewDailies(activeDailies,matchingCards)

    #for matching cards, if the card is archived and the task is not complete, complete
    completeArchivedDailies(activeDailies,matchingCards)
    lo.info("Map completed dailies[%i] existing cards[%i]",len(activeDailies),len(matchingCards))

if __name__ == "__main__":
    executePurge(1)
    executeMap()