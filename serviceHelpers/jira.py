import json
import logging
import urllib.parse

import requests

from serviceHelpers.models.JiraDetails import JiraDetails
from serviceHelpers.models.JiraTicket import JiraTicket
from serviceHelpers.models.JiraWorklog import JiraWorklog

LO = logging.getLogger("jira")
TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%S.%f%z"


class Jira:
    """Represents a single Jira instance, accepting necessary methods to use the API.
    Exposes methods for fetching tickets.
    """

    def __init__(self, config: JiraDetails) -> None:

        config: JiraDetails
        self.valid = config.valid
        self.host = config.host
        self.name = config.name
        self.token = config.key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.token}",
        }
        self.logger = LO

    def fetch_jira_tickets(self, jql) -> dict:
        "takes a JQL string, encodes it, send its to Jira, and returns a dict of tickets, with the ticket ID (PRJ-123) as the dict key"

        jql = urllib.parse.quote(jql)

        url = f"https://{self.host}/rest/api/2/search?jql={jql}&fields=key,summary,description,status,priority,assignee,created,updated"

        retrieved_results = _request_and_validate(url, self.headers)
        incoming_tickets = {}
        for ticket in retrieved_results["issues"]:

            new_ticket = JiraTicket().from_dict(ticket)

            incoming_tickets[ticket["key"]] = new_ticket
            # print(json.dumps(ticket,indent=2))
        return incoming_tickets

    def fetch_worklogs_for_jira_ticket(self, ticket_key: str) -> list:
        "takes a ticket key and returns the worklogs for it"

        url = f"https://{self.host}/rest/api/2/issue/{ticket_key}/worklog"
        results = _request_and_validate(url, self.headers)
        worklogs = []
        if "worklogs" in results:
            for worklog in results["worklogs"]:
                parsed_worklog = JiraWorklog().from_json(worklog)
                if parsed_worklog.is_valid:
                    worklogs.append(parsed_worklog)

        return worklogs


def _request_and_validate(url, headers, body=None) -> dict:
    "internal method to request and return results from Jira"

    try:
        result = requests.get(url=url, headers=headers, data=body)
    except (ConnectionError) as e:
        LO.error("Couldn't connect to Jira %s - %s", url, e)
        return {}
    if result.status_code != 200:
        LO.error(
            "Got an invalid response on the endpoint %s: %s - %s ",
            url,
            result.status_code,
            result.content,
        )
        return {}
    try:
        parsed_content = json.loads(result.content)
    except json.JSONDecodeError as e:
        LO.error("Couldn't parse JSON from Jira - %s", e)
        return {}
    return parsed_content
