import base64
import json
import logging
import math
import re
from datetime import datetime
from typing import Dict
from urllib.parse import quote_plus

import requests

# get all open FD tickets
# get all open trello cards

# cross reference all Trello Cards with a custom field to their FD ticket brethren
# turn unaffilliated tickets into cards.


_LO = logging.getLogger("freshdesk")
TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"


class FreshDesk:
    def __init__(self, host, api_key:str ) -> None:
        "Note, api_key should not be base-64 encoded already"
        self.host = host
        
        key_as_bytes = api_key.encode('utf-8')
        encoded_bytes = base64.b64encode(key_as_bytes)
        self.api_key = encoded_bytes.decode('utf-8')

    def search_fd_tickets(self, query_string):
        """now paginated! See the search definition here: 
        
        https://developers.freshdesk.com/api/#ticket_attributes"""

        # sample query string = ((agent_id:%s OR agent_id:null) AND (status:2 OR status:3))
        ticketObj = {}
        current_page = 1
        get_next_page = True
        last_content = {}
        while get_next_page and current_page <= 10 :
            url = f'https://{self.host}/api/v2/search/tickets?page={current_page}&query="{query_string}"'
            
            search_results = self._request_and_validate(url)
            
            if search_results != last_content:
                if "results" in search_results:
                    for ticket in search_results["results"]:
                        new_ticket = FreshdeskTicket()
                        new_ticket.from_dict(ticket)
                        ticketObj[new_ticket.id] = new_ticket
                last_content = search_results
            else:
                get_next_page = False
                break
            current_page += 1
                
        return ticketObj

    def _get_default_headers(self) -> dict:
        "headers with auth token for requests"
        AuthString = "Basic %s" % (self.api_key)
        return {"Authorization": AuthString, "Content-Type": "application/json"}

    def fetch_worklogs(self, ticketID: str):
        returnObj = []
        getNextPage = True
        oldResponse = ""
        currentPage = 0

        worklogs = {}
        while getNextPage == True:
            currentPage = currentPage + 1
            url = "https://%s/api/v2/tickets/%s/time_entries" % (self.host, ticketID)
            r = requests.get(url, headers=self._get_default_headers())

            if r.status_code != 200:
                _LO.warn(
                    "Unexpected response code [%s], whilst getting worklogs for %s"
                    % (r.status_code, ticketID)
                )
                print(r.content)
                return
            if r.content == oldResponse:
                getNextPage = False
            else:
                oldResponse = r.content

            try:
                response = json.loads(r.content)
            except Exception as e:
                _LO.error("Couldn't parse json of worklogs")
                response = []

            for worklog in response:
                if "id" in worklog:
                    worklogs[worklog["id"]] = worklog

        if len(returnObj) > 0:
            _LO.debug(worklogs)
        return list(worklogs.values())

    def fetch_comments(self, ticket: str) -> list:

        #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
        getNextPage = True
        oldResponse = ""
        countOfMessages = 0
        currentPage = 0
        comments = []
        while getNextPage == True:
            currentPage = currentPage + 1
            url = f"https://{self.host}/api/v2/tickets/{ticket}/conversations?page={currentPage}"

            json = self._request_and_validate(url)
            if json == oldResponse:
                getNextPage = False
            else:
                oldResponse = json
                for message in json:
                    comments.append(message)
        if len(comments) > 0:
            logging.debug("[%s]" % countOfMessages)
        return comments

    def get_fd_tickets_updated_on(self, targetdate: str):
        "expects a string in the format %Y-%m-%d"
        return self.search_fd_tickets(f"updated_at:'{targetdate}'")

    def get_worklogs(self, ticketID):
        # /api/v2/tickets/[id]/time_entries
        # returns all tickets associated with me, or unassigned

        returnObj = []
        getNextPage = True
        oldResponse = ""
        currentPage = 0
        while getNextPage == True:
            currentPage = currentPage + 1

            url = f"https://{self.host}/api/v2/tickets/{ticketID}/time_entries" 
            
            response = self._request_and_validate(url)
            if oldResponse == response:
                getNextPage = False
                break

            for worklog in response:
                returnObj.append(worklog)

        return returnObj

    def get_comments(self, ticket):
        #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
        getNextPage = True
        oldResponse = ""

        currentPage = 0
        messages = []
        while getNextPage == True:
            currentPage = currentPage + 1
            url = "https://%s/api/v2/tickets/%s/conversations?page=%s" % (
                self.host,
                ticket,
                currentPage,
            )
            AuthString = "Basic %s" % (self.api_key)
            try:
                r = requests.get(
                    url,
                    headers={
                        "Authorization": AuthString,
                        "Content-Type": "application/json",
                    },
                )
                conversation = json.loads(r.content)
                if len(conversation) < 30:
                    getNextPage = False
            except Exception as e:
                return []

            if r.status_code != 200:
                print(
                    "Unexpected response code [%s], whilst getting ticket list"
                    % r.status_code
                )
                print(r.content)
                return
            if r.content == oldResponse:
                getNextPage = False

            else:
                oldResponse = r.content
                maybeJSON = r.content
                for message in conversation:
                    messages.append(message)
        return messages

    def search_agent(self, email:str=None, id=None):
        if id is not None and email != None:
            _LO.error("Pick either email or ID to search by, not both")
            return None
        if id is not None:
            return self._get_agent_by_id(id)
        if email is not None:
            return self._get_agent_by_email(email)

    def _get_agent_by_id(self, id):
        url = f"https://{self.host}/api/v2/agents/{id}"
        agent_j = self._request_and_validate(url)

        agent_o = FreshdeskAgent()
        agent_o.from_dict(agent_j)
        return agent_o

    def _get_agent_by_email(self, email):
        if email is None or not isinstance(email,str):
            _LO.error("invalid parameters passed to _get_agent_by_email")
            return FreshdeskAgent()
        email_f = quote_plus(email)
        url = f"https://{self.host}/api/v2/agents?email={email_f}"
        
        agent_j = self._request_and_validate(url)
        agent_o = FreshdeskAgent()
        agent_o.from_dict(agent_j)
        return

    def _request_and_validate(self,url,headers={},body=None) -> dict:
        
        if headers == {}:
            headers = self._get_default_headers()
        
        try:
            result = requests.get(url=url,headers=headers,data=body)
        except (ConnectionError) as e:
            _LO.error("Couldn't connect to FD %s - %s",url,e)
            return {} 
        if result.status_code != 200:
            _LO.error("Got an invalid response: %s - %s ",result.status_code, result.content)
            return {}
        try:
            parsed_content = json.loads(result.content)
        except json.JSONDecodeError as e:
            _LO.error("Couldn't parse JSON from FD - %s",e)
            return {}
        return parsed_content

class FreshdeskTicket:
    def __init__(self) -> None:
        self.status = ""
        self.id = 0
        self.responder_id = 0
        self.priority = 0
        self.subject = ""
        self.description = ""
        self.type = ""
        self.custom_fields = {}
        self.created = datetime.min
        self.updated = datetime.min
        self.response_group = 0

    def from_dict(self, new_params: dict) -> None:
        self.status = new_params["status"] if "status" in new_params else self.status
        self.id = new_params["id"] if "id" in new_params else self.id
        self.responder_id = (
            new_params["responder_id"]
            if "responder_id" in new_params
            else self.responder_id
        )
        self.priority = (
            new_params["priority"] if "priority" in new_params else self.priority
        )
        self.subject = (
            new_params["subject"] if "subject" in new_params else self.subject
        )
        self.description = (
            new_params["description_text"]
            if "description_text" in new_params
            else self.description
        )
        self.type = new_params["type"] if "type" in new_params else self.type
        self.custom_fields = (
            new_params["custom_fields"]
            if "custom_fields" in new_params
            else self.custom_fields
        )
        self.created = (
            datetime.strptime(new_params["created_at"], TIMESTAMP_FORMAT)
            if "created_at" in new_params
            else self.created
        )
        self.updated = (
            datetime.strptime(new_params["updated_at"], TIMESTAMP_FORMAT)
            if "updated_at" in new_params
            else self.updated
        )

        self.response_group = (
            new_params["group_id"] if "group_id" in new_params else self.response_group
        )


class FreshdeskAgent():
    def __init__(self) -> None:
        self.id = 0
        self.name = ""
        self.email = ""
        
    def from_dict(self, api_result:dict) -> None:
        self.id = api_result.get("id",0)
        contact = api_result.get("contact",{})
        self.name = contact.get("name","")
        self.email = contact.get("email","")
         

