import logging
import json
from typing import List
import requests 

lo = logging.getLogger("HabiticaMapper")

class Habitica():
    def __init__(self,user_id,api_key) -> None:
            self.user_id = user_id
            self.api_key = api_key
        
    def fetchHabiticaDailies(self,dateAsString) -> list:
        url =  "https://habitica.com/api/v3/tasks/user?type=dailys&dueDate=%s" % (dateAsString)
        headers = self._getHabiticaHeaders()

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


    def completeDaily(self,dailyID):
        url = "https://habitica.com/api/v3/tasks/%s/score/up" % (dailyID)
        headers = self._getHabiticaHeaders()
        r = requests.post(url,headers=headers)
        if r.status_code != 200:
            print ("Unexpected error whilst completing a habitica task! \n%s\t%s" % (r.status_code, r.content))


    
    def resetDailies(self):
        """Call's the endpoint that triggers the end of day process to executes"""
        url = "https://habitica.com/api/v3/cron"
        headers = self._getHabiticaHeaders()
        r = requests.post(url,headers=headers)
        if r.status_code != 200:
            lo.warning("Failed to request Habitica reset!!")

    def _getHabiticaHeaders(self):
        headersObj = {
            "x-client" : "d97d7173-7502-405a-89b7-fe58b1a2e967-Presence", #habitica asks app authors to self-report their identity - please change this if you modify the habitica code.
            "x-api-user" : self.user_id,
            "x-api-key" : self.api_key
        } 
        return headersObj


