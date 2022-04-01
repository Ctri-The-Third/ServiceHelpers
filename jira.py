from datetime import datetime
import json
import logging
import urllib.parse
from time import strptime
from pytest import param

import requests

lo = logging.getLogger("jira")
TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%S.%f%z"


class Jira:
    """ Represents a single Jira instance, accepting necessary methods to use the API. 
    Exposes methods for fetching tickets.
    """
    def __init__(self, config) -> None:
        # config = jiraDetails()
        self.valid = config.valid
        self.host = config.host
        self.name = config.name
        self.token = config.key

    def fetch_jira_tickets(self, jql) -> dict:
        "takes a JQL string, encodes it, send its to Jira, and returns a dict of tickets, with the ticket ID (PRJ-123) as the dict key"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % self.token,
        }
        jql = urllib.parse.quote(jql)

        url = f"https://{self.host}/rest/api/2/search?jql={jql}&fields=key,summary,description,status,priority,assignee,created,updated"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(
                "ERROR: %s could not fetch Jira tickets\n%s"
                % (r.status_code, r.content)
            )
            return []
        loaded_tickets = json.loads(r.content)
        incoming_tickets = {}
        for ticket in loaded_tickets["issues"]:

            new_ticket = JiraTicket().from_dict(ticket)
            

            incoming_tickets[ticket["key"]] = new_ticket
            # print(json.dumps(ticket,indent=2))
        return incoming_tickets


class JiraTicket:
    "represents a single Jira ticket"

    def __init__(
            self,
            key="",
            summary="",
            assignee_id="",
            assignee_name="",
            status="",
            priority="",
            description="",
            created=datetime.min,
            updated=datetime.min,
    ) -> None:
        self.key = key
        self.summary = summary
        self.description = description
        self.assignee_id = assignee_id
        self.assignee_name = assignee_name
        self.status = status
        self.priority = priority
        self.created = created
        self.updated = updated


    def from_dict(self, new_dict: dict):
        """Takes the dictionary returned from the API and applies the contents to the matching parameters."""
        fields = new_dict["fields"] if "fields" in new_dict else {}
        assignee_dict = fields["assignee"] if "assignee" in fields else {}
        assignee_dict = {} if assignee_dict is None else assignee_dict
        priority_dict = fields["priority"] if "priority" in fields else {}

        self.key = new_dict["key"] if "key" in new_dict else self.key
        self.summary = fields["summary"] if "summary" in fields else self.summary
        self.description = (
            fields["description"] if "description" in fields else self.description
        )
        self.assignee_id = (
            assignee_dict["key"] if "key" in assignee_dict else self.assignee_id
        )
        self.assignee_id = (
            assignee_dict["accountId"]
            if "accountId" in assignee_dict
            else self.assignee_id
        )
        self.assignee_name = (
            assignee_dict["displayName"]
            if "displayName" in assignee_dict
            else self.assignee_name
        )
        self.priority = (
            priority_dict["name"] if "name" in priority_dict else self.priority
        )

        status_dict = fields["status"] if "status" in fields else {}
        self.status = status_dict["name"] if "name" in status_dict else self.status

        self.created = (
            datetime.strptime(fields["created"], TIMESTAMP_FORMAT)
            if "created" in fields
            else self.created
        )

        self.updated = (
            datetime.strptime(fields["updated"], TIMESTAMP_FORMAT)
            if "updated" in fields
            else self.updated
        )

        return self


class JiraDetails:
    """represents the settings for a jira object"""

    def __init__(self) -> None:
        self.host = ""
        self.name = ""
        self.key = ""
        self.default_assignee = ""

        self._lo = logging.getLogger("jiraDetails")


    def from_dict(self, src: dict) :
        """Takes a dictionary and tries to map appropriate details to the class parameters."""
        self.name = src["instanceName"] if "instanceName" in src else ""
        self.host = src["instanceHost"] if "instanceHost" in src else ""
        self.key = src["bearerToken"] if "bearerToken" in src else ""
        self.default_assignee = (
            src["instanceUserID"] if "instanceUserID" in src else ""
        )


        return self

    @param
    def valid(self):
        """self checking of the parameters."""
        valid = True
        if self.name == "":
            lo.warning("jira obj name is blank")
            valid = False
        if self.host == "":
            lo.warning("jira object host is blank")
            valid = False
        if self.default_assignee == "":
            lo.warning("jira object primary_user_id is blank")
        if self.key == "":
            lo.warning("key missing from jira settings")
            valid = False
        
        return valid 
