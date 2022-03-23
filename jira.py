import json
import requests
import logging

import urllib.parse

lo = logging.getLogger("jira")

class Jira():
    def __init__(self, config) -> None:
        #config = jiraDetails()
        self.valid = config.valid
        self.host = config.host
        self.name = config.name
        self.token = config.key


    def fetchJiraTickets(self, jql) -> dict:
        "takes a JQL string, encodes it, send its to Jira, and returns a dict of tickets, with the ticket ID (PRJ-123) as the dict key"
        headers = {"Content-Type" : "application/json", "Authorization" : "Basic %s" % self.token}
        jql = urllib.parse.quote(jql)
        
        url = f"https://{self.host}/rest/api/2/search?jql={jql}&fields=key,summary,description,status,priority,assignee"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print("ERROR: %s could not fetch Jira tickets\n%s" % (r.status_code, r.content))
            return []
        loadedTickets = json.loads(r.content)
        incomingTickets = {}
        for ticket in loadedTickets["issues"]:

            new_ticket = jiraTicket()
            new_ticket.from_dict(ticket)
            
            incomingTickets[ticket["key"]] = new_ticket
            #print(json.dumps(ticket,indent=2))
        return incomingTickets
        

class jiraTicket():
    "represents a single Jira ticket"
    def __init__(self, key = "", summary = "", assignee_id = "", assignee_name = "", status = "", priority = "", description = "") -> None:
        self.key = key
        self.summary = summary
        self.description = description
        self.assignee_id = assignee_id
        self.assignee_name = assignee_name
        self.status = status
        self.priority = priority
        pass

    def from_dict(self,new_dict:dict):
        fields = new_dict["fields"] if "fields" in new_dict else {}
        assignee_dict = fields["assignee"] if "assignee" in fields else {}
        assignee_dict = {} if assignee_dict is None else assignee_dict
        priority_dict = fields["priority"] if "priority" in fields else {}

        self.key = new_dict["key"] if "key" in new_dict else self.key
        self.summary = fields["summary"] if "summary" in fields else self.summary
        self.description = fields["description"] if "description" in fields else self.description
        self.assignee_id = assignee_dict["key"] if "key" in assignee_dict else self.assignee_id
        self.assignee_id = assignee_dict["accountId"] if "accountId" in assignee_dict else self.assignee_id
        self.assignee_name = assignee_dict["displayName"] if "displayName" in assignee_dict else self.assignee_name
        self.priority = priority_dict["name"] if "name" in priority_dict else self.priority
        self.status = new_dict["status"] if "status" in new_dict else self.status
        pass 

class jiraDetails():
    """represents the settings for a jira object"""
    def __init__(self) -> None:
        self.valid = False
        self.host = ""
        self.name = ""
        self.key = ""
        self.primary_user_id = "" 
        self.issues_jql = ""
        self.trello_label = ""
        self.trello_custom_field = "" 
        self._lo = logging.getLogger("jiraDetails")
        pass
    def from_dict(self, dict:dict):
        self.name = dict["instanceName"] if "instanceName" in dict else ""
        self.host = dict["instanceHost"] if "instanceHost" in dict else ""
        self.key = dict["bearerToken"] if "bearerToken" in dict else "" 
        self.primary_user_id = dict["instanceUserID"] if "instanceUserID" in dict else ""
        self.issues_jql = dict["instanceJQL"] if "instanceJQL" in dict else ""
        self.trello_custom_field = dict["TrelloCustomFieldIDforJira"] if "TrelloCustomFieldIDforJira" in dict else ""
        self.trello_label = dict["TrelloLabelForJiraCards"] if "TrelloLabelForJiraCards" in dict else ""
        self.check_keys()
        pass 


    def check_keys(self):
        valid = True
        if self.name == "":
            lo.warning("jira obj name is blank")
            valid = False 
        if self.host == "":
            lo.warning("jira object host is blank")
            valid = False 
        if self.primary_user_id == "":
            lo.warning("jira object primary_user_id is blank")
            valid = False 
        if self.issues_jql == "":
            lo.warning("jira object issues_jql is blank")
            valid = False 
        if self.trello_custom_field == "":
            lo.warning("jira object trello_custom_field is blank")
            valid = False 
        if self.trello_label == "":
            lo.warning("jira object trello_label is blank")
            valid = False 
        if self.key == "":
            lo.warning("key missing from jira settings")
        self.valid = valid


