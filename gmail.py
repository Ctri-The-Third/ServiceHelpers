from __future__ import print_function
import pickle
import os.path
import json
import requests 
import re 
import html
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging

import helpers.TrelloHelper  as TrelloHelper
import helpers.cfg as cfg

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
cfg = cfg.getCfgHelper()
lo = logging.getLogger("GMailMapper")
logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.WARNING)


def ListThreadsMatchingQuery(service, user_id, query='label:UNREAD label:INBOX'):
  """List all Threads of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
           Eg.- 'label:UNREAD' for unread messages only.

  Returns:
    List of threads that match the criteria of the query. Note that the returned
    list contains Thread IDs, you must use get with the appropriate
    ID to get the details for a Thread.
  """
  try:
    response = service.users().threads().list(userId=user_id, q=query).execute()
    threads = []
    if 'threads' in response:
      threads.extend(response['threads'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().threads().list(userId=user_id, q=query,
                                        pageToken=page_token).execute()
      threads.extend(response['threads'])

    return threads
  except Exception as error:
    print ('An error occurred: %s' % error)

def getToken(tokenName):
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  filename = "resources/GMailAuthTokens/%s.pickle" % (tokenName)
  #print(os.getcwd()+filename)
  if os.path.exists(filename):
      with open(filename, 'rb') as token:
          creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
      lo.warning ("Needing authorisation for the %s inbox!" % (tokenName))
      if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
      else:
          lo.warning ("Needing authorisation for the %s inbox!" % (tokenName))
          flow = InstalledAppFlow.from_client_secrets_file(
              'resources/GMailCredentials.json', SCOPES)
          creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open(filename, 'wb') as token:
          pickle.dump(creds, token)
  return creds


def fetchGmailItems(creds):
  
  """Shows basic usage of the Gmail API.
  Lists the user's emails that are in the inbox.
  """
  
  service = build('gmail', 'v1', credentials=creds)

  # Call the Gmail API
  #results = service.users().labels().list(userId='me').execute()
  threads = ListThreadsMatchingQuery(service,"me")
  #get the trello card. wipe its checklist.
  #create new checklist with all the items.

  for result in threads:
    pass
      #print (result)
      #https://mail.google.com/mail/u/ctri@ctri.co.uk/#inbox/173ab098f347ef24
  
  #find the trello card. If it doesn't exist, create it. - distinguish by title.
  #get the checklist, make dictionary list of threads & checklists
  #iterate through the list of threads. If not in list, add item.
  #iterate through checklist. If thread ID not in list of threads, mark complete and move on.
  #description = summary of unread emails and snippet of most recent
  return threads


def getTrelloCard(token):
  
  return TrelloHelper.findTrelloCard("^Gmail: check \[[0-9]*\] unread %s emails" % (token))
   

def makeTrelloCard(token):

  newCard = TrelloHelper.makeTrelloCard('Gmail: check [0000] unread %s emails' % token)
  newCheckListID = TrelloHelper.createChecklist(newCard["id"],checklistName="Unread mail")
  newCard['idChecklists'].append(newCheckListID)
  return newCard

def attachItemsToChecklist(gmailItems, gmailCard,emailAddress):
  checkListID = gmailCard["idChecklists"][0] #assuming a single checklist. Probably should iterate and find the matching name. I'll allow one "I told you so, you filthy technical debtor" from my future self.
  
  url = "https://api.trello.com/1/checklists/%s" % (checkListID)
  params = TrelloHelper._getTrelloParams()
  params["checkItems"] = "all"
  r = requests.get(url,params=params)
  if r.status_code != 200:
    print("ERROR: %s when attempting to get the unread gmail checklist from Trello\n%s" % (r.status_code,r.content))
    return []
  checklist = json.loads(r.content)

  existingItems = {} #The key is the Gmail ID, the value is the trello card
  incomingItems = []
  

  for checkListItem in checklist["checkItems"]:
    matches = re.findall(r'.*https:\/\/mail.google.com\/mail\/u\/.*\/#inbox\/([a-zA-Z0-9]*)',checkListItem["name"])
    if len(matches) != 0:
      existingItems[matches[0]] = checkListItem["id"]
      
    #regex extract the ID from the URL.
    #existingItem[GmailID] = TrelloID
    
  

  for thread in gmailItems:
    # does the gmail thread already exist?
    # if yes then just add it to the newItems cache. in the Existing cache without a mapping Incoming entry = read /deleted email & we tidy that up.
    if thread["id"] in existingItems:
      incomingItems.append(thread["id"])

      
    #if no, create, then add to cache.
    else:
      thread["snippet"] = html.unescape(thread["snippet"])
      incomingItemText = "%s - https://mail.google.com/mail/u/%s/#inbox/%s" % (thread["snippet"],emailAddress, thread["id"])
      TrelloHelper.addItemToChecklist(checkListID,incomingItemText)
      incomingItems.append(thread["id"])

  #search through all the cached email IDs (the keys to the dictionary)
  #on a find, the value = the associated trello object.
  for existingItem in existingItems.keys():
    if existingItem not in incomingItems:
      url = "https://api.trello.com/1/checklists/%s/checkItems/%s" % (checkListID,existingItems[existingItem])
      params = TrelloHelper._getTrelloParams()
      r = requests.delete(url,params=params)
      if r.status_code != 200:
        print ("ERROR: %s, Couldn't delete trello card %s " % (r.status_code,existingItems[existingItem]))

  
  #finally, update the card title.

def updateTrelloCardTitle(trelloCard,unreadMailCount,tokenName):
  
  cardNewName = ('Gmail: check [%s] unread %s emails'%(unreadMailCount, tokenName) )
  TrelloHelper.updateTrelloCard(trelloCard["id"],cardNewName)  
  
def executePurge(account,deleteLevel):
  if account == "all" or account == "*":
    account = ".*"
  titlePattern = r"(Gmail: check \[[0-9]*\] unread {0} emails)".format(account)
  if deleteLevel == 0:
      targetLists = [cfg.trelloListForNewCards] 
  elif deleteLevel == 1: 
      targetLists = ["*",] 
  else: 
    return 

  TrelloHelper.purgeTrelloCards(titlePattern=titlePattern, targetLists=targetLists)     



def executeMap(targetAccount = "*"):
  lo.info("Beginning map of account [%s]" % targetAccount)
  for tokenName in cfg.GmailAddresses.keys():
    if (targetAccount == tokenName or targetAccount == "*") and cfg.serviceStatus.checkService("gmail",subService=tokenName):
        
      gmailAddress = cfg.GmailAddresses[tokenName]
      
      gmailToken = getToken(tokenName)
      gmailItems = fetchGmailItems(gmailToken)
      gmailCard = getTrelloCard(tokenName)
      
      if len(gmailItems) > 0 or ( gmailCard is not None and len(gmailItems) == 0):
        if gmailCard == None:
          gmailCard = makeTrelloCard(tokenName)
        attachItemsToChecklist(gmailItems, gmailCard, gmailAddress)
        updateTrelloCardTitle(gmailCard,len(gmailItems),tokenName)
      lo.info("Completed update of account [%s], items[%s]",tokenName,len(gmailItems))

      
      #archive the card?
  lo.info("end of gmail mapping")
