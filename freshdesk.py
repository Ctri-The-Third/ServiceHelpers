import json
import requests
import datetime
import re
import math
import logging


#get all open FD tickets
#get all open trello cards

#cross reference all Trello Cards with a custom field to their FD ticket brethren
#turn unaffilliated tickets into cards.



lo = logging.getLogger("freshdesk")
class FreshDesk():
    def __init__(self, host, api_key) -> None:
        self.host = host
        self.api_key = api_key
        pass
    def searchFDtickets(self,  query_string):
        "not paginated"
        
        #sample query string = ((agent_id:%s OR agent_id:null) AND (status:2 OR status:3))
        url = f'https://{self.host}/api/v2/search/tickets?query="{query_string}"'
        
        r = requests.get (
            url,
            headers = self._get_default_headers()
        )
    
        if r.status_code != 200:
            lo.warning("Unexpected response code [%s], whilst getting ticket list - reason:\t%s" % (r.status_code,r.content))
            return {}
        
        ticketObj = {}
        tickets = json.loads(r.content)
        if "results" in tickets: 
            for ticket in tickets["results"]:
                new_ticket = FreshdeskTicket()
                new_ticket.from_dict(ticket)
                ticketObj[new_ticket.id] = new_ticket
                    
        
        
        return ticketObj

    def _get_default_headers(self) -> dict:
        "headers with auth token for requests"
        AuthString = "Basic %s" % (self.api_key)
        return {'Authorization':AuthString,
            'Content-Type':'application/json'}
        



    def _getWorklogs(ticketID):
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

class FreshdeskTicket():
    def __init__(self) -> None:
        self.status = ""
        self.id = 0
        self.responder_id = 0
        self.priority = 0
        self.subject = ""
        self.description = ""
        
    def from_dict(self,new_params:dict) -> None:
        self.status = new_params["status"] if "status" in new_params else self.status
        self.id = new_params["id"] if "id" in new_params else self.id
        self.responder_id = new_params["responder_id"] if "responder_id" in new_params else self.responder_id
        self.priority = new_params["priority"] if "priority" in new_params else self.priority
        self.subject = new_params["subject"] if "subject" in new_params else self.subject
        self.description = new_params["description_text"] if "description_text" in new_params else self.description

        