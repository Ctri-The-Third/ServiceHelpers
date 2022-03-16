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
    def search_fd_tickets(self,  query_string):
        "now paginated!"
        
        #sample query string = ((agent_id:%s OR agent_id:null) AND (status:2 OR status:3))
        ticketObj = {} 
        current_page = 1
        get_next_page = True
        last_content = {}
        while get_next_page:
            url = f'https://{self.host}/api/v2/search/tickets?page={current_page}&query="{query_string}"'
            r = requests.get (
                url,
                headers = self._get_default_headers()
            )
        
            if r.status_code != 200:
                lo.warning("Unexpected response code [%s], whilst getting ticket list - reason:\t%s" % (r.status_code,r.content))
                return {}
            
            if r.content != last_content:
                tickets = json.loads(r.content)
                if "results" in tickets: 
                    for ticket in tickets["results"]:
                        new_ticket = FreshdeskTicket()
                        new_ticket.from_dict(ticket)
                        ticketObj[new_ticket.id] = new_ticket
                last_content = r.content
            else:
                get_next_page = False
                current_page += 1 
            
        
        return ticketObj

    def _get_default_headers(self) -> dict:
        "headers with auth token for requests"
        AuthString = "Basic %s" % (self.api_key)
        return {'Authorization':AuthString,
            'Content-Type':'application/json'}

    def fetch_worklogs(self,ticketID:str):
        returnObj = []
        getNextPage = True
        oldResponse = ""
        currentPage = 0
        
        worklogs = {}
        while getNextPage == True:
            currentPage = currentPage + 1
            url = 'https://%s/api/v2/tickets/%s/time_entries' % (self.host,ticketID)            
            r = requests.get ( url, headers = self._get_default_headers() )
        
            if r.status_code != 200:
                lo.warn("Unexpected response code [%s], whilst getting worklogs for %s" % (r.status_code,ticketID))
                print(r.content)
                return 
            if r.content == oldResponse:
                getNextPage = False
            else :
                oldResponse = r.content
            
            try: 
                response = json.loads(r.content)
            except Exception as e:
                lo.error("Couldn't parse json of worklogs")
                response = []

            for worklog in response:
                if "id" in worklog:
                    worklogs[worklog["id"]] = worklog
                    
        if len(returnObj) > 0:
            lo.debug(worklogs)
        return list(worklogs.values())

    def fetch_comments(self,ticket:str) -> list:

        #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
        getNextPage = True
        oldResponse = ""
        countOfMessages = 0
        currentPage = 0
        comments = []
        while getNextPage == True:
            currentPage = currentPage + 1
            url = 'https://%s/api/v2/tickets/%s/conversations?page=%s' % (self.host,ticket,currentPage)
            
            try:
                r = requests.get (
                    url,
                    headers = self._get_default_headers()
                )
                conversation = json.loads(r.content)
                if len(conversation) < 30:
                    getNextPage = False
            except Exception as e:
                lo.error("unrecoverable error when getting comments, %s", e)
                return [] 
                
            
            if r.status_code != 200:
                print("Unexpected response code [%s], whilst getting ticket list" % r.status_code)
                print(r.content)
                return 
            if r.content == oldResponse:
                getNextPage = False
            else :
                oldResponse = r.content
                for message in conversation:
                    comments.append(message)
        if len(comments) > 0:
            logging.debug("[%s]" % countOfMessages)    
        return comments

    def get_fd_tickets_updated_on(self,targetdate:str):
        "expects a string in the format %Y-%m-%d"
        return self.search_fd_tickets(f"updated_at:\'{targetdate}\'")
        
    def get_worklogs(self,ticketID):
        #/api/v2/tickets/[id]/time_entries
        #returns all tickets associated with me, or unassigned

        returnObj = []
        getNextPage = True
        oldResponse = ""
        currentPage = 0
        while getNextPage == True:
            currentPage = currentPage + 1


            url = 'https://%s/api/v2/tickets/%s/time_entries' % (self.host,ticketID)
<<<<<<< HEAD
=======

>>>>>>> 9251d5b9adf5e5c462589e7ef30ed9343ab8f572
            AuthString = "Basic %s" % (self.api_key) 
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
                returnObj.append(worklog)
                    
        
        
        return returnObj

    def get_comments(self,ticket):
        #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
        getNextPage = True
        oldResponse = ""
        
        currentPage = 0
        messages = [] 
        while getNextPage == True:
            currentPage = currentPage + 1
            url = 'https://%s/api/v2/tickets/%s/conversations?page=%s' % (cfg.FreshdeskURL,ticket,currentPage)
            AuthString = "Basic %s" % (self.api_key)
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
                    messages.append(message)
        return messages






class FreshdeskTicket():
    def __init__(self) -> None:
        self.status = ""
        self.id = 0
        self.responder_id = 0
        self.priority = 0
        self.subject = ""
        self.description = ""
        self.type = ""
        self.custom_fields = {}


    def from_dict(self,new_params:dict) -> None:
        self.status = new_params["status"] if "status" in new_params else self.status
        self.id = new_params["id"] if "id" in new_params else self.id
        self.responder_id = new_params["responder_id"] if "responder_id" in new_params else self.responder_id
        self.priority = new_params["priority"] if "priority" in new_params else self.priority
        self.subject = new_params["subject"] if "subject" in new_params else self.subject
        self.description = new_params["description_text"] if "description_text" in new_params else self.description
        self.type = new_params["type"] if "type" in new_params else self.type
        self.custom_fields = new_params["custom_fields"] if "custom_fields" in new_params else self.custom_fields

        