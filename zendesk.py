
import json
import logging 
import requests
import re 
import helpers.TrelloHelper as TrelloHelper
import helpers.cfg as cfg




lo = logging.getLogger("ZendeskMapper")

class zendesk:
    def __init__(self, host,api_key):
        
        self.host = host
        self.key = api_key
        self._headers =  {"Authorization" : "Basic %s" % (self.key)}

        
        
    def search_for_tickets(self,search_string): #gets the most recently 100 Zendesk tickets.
        url = str.format("https://{0}/api/v2/search.json?query={1}", self.host,search_string)
        response = requests.get(url,headers=self._headers)
        if response.status_code != 200:
            lo.warn("couldn't retrieve zendesk tickets [%s]\n%s" % (response.status_code, response.content))

        try:
            tickets = json.loads(response.content)["results"]
        except:
            lo.warn("Couldn't parse zendesk tickets as json! \n%s" % (response.content))
            return []
        return tickets


    def get_user_from_id(self,ticketID):
        """helper method to get the userID assigned to a ticket. Helpful for when the user doesn't know their own ID"""
        raise NotImplementedError