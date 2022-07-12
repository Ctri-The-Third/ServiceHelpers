import re
import base64
import json
import logging
from datetime import datetime
from urllib.parse import quote_plus
import requests

# get all open FD tickets
# get all open trello cards

# cross reference all Trello Cards with a custom field to their FD ticket brethren
# turn unaffilliated tickets into cards.


_LO = logging.getLogger("freshdesk")
TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"

 
class FreshDesk:
    "Represents a single freshdesk tenancy"

    def __init__(self, host, api_key: str) -> None:
        "Note, api_key should not be base-64 encoded already"
        self.host = host
        key_as_bytes = api_key.encode("utf-8")
        encoded_bytes = base64.b64encode(key_as_bytes)
        self.api_key = encoded_bytes.decode("utf-8")

    def search_fd_tickets(self, query_string) -> dict:
        """now paginated! See the search definition here:

        https://developers.freshdesk.com/api/#ticket_attributes"""

        url = f'https://{self.host}/api/v2/search/tickets?query="{query_string}"'

        ticket_dict = {}
        pages = self._request_and_validate_paginated(url)
        for page in pages:
            for ticket_j in page.get("results", []):
                page: dict
                ticket_o = FreshdeskTicket()
                ticket_o.from_dict(ticket_j)
                ticket_dict[ticket_o.id] = ticket_o

        return ticket_dict

    def _get_default_headers(self) -> dict:
        "headers with auth token for requests"
        AuthString = "Basic %s" % (self.api_key)
        return {"Authorization": AuthString, "Content-Type": "application/json"}

    def fetch_worklogs(self, ticket_id: str):
        "Returns the worklogs for a given ticket"

        url = f"https://{self.host}/api/v2/tickets/{ticket_id}/time_entries"
        pages = self._request_and_validate_paginated(url)

        worklogs = []
        for page in pages:
            for worklog in page:
                worklogs.append(worklog)
        return worklogs

    def fetch_comments(self, ticket: str) -> list:
        "Returns the comments for a given ticket"
        url = f"https://{self.host}/api/v2/tickets/{ticket}/conversations?"
        pages = self._request_and_validate_paginated(url)

        comments = []
        for page in pages:
            for comment in page:
                comments.append(comment)
        return comments

    def get_fd_tickets_updated_on(self, targetdate: str):
        "expects a string in the format %Y-%m-%d"
        return self.search_fd_tickets(f"updated_at:'{targetdate}'")

    def get_worklogs(self, ticketID) -> list:
        "returns a list of dictionaries of parsed JSON representing worklogs representing a ticketID"

        url = f"https://{self.host}/api/v2/tickets/{ticketID}/time_entries"
        pages = self._request_and_validate_paginated(url)
        worklogs = []
        for page in pages:
            for worklog in page:
                worklogs.append(worklog)
        return worklogs

    def get_comments(self, ticket_id):
        "retrieve the comments on a ticket. Can be an int or a str"
        #'https://domain.freshdesk.com/api/v2/tickets/1/conversations?page=2'
        url = url = f"https://{self.host}/api/v2/tickets/{ticket_id}/conversations"
        pages = self._request_and_validate_paginated(url)

        comments = []
        for page in pages:
            for comment in page:
                comments.append(comment)
        return comments

    def search_agent(self, email: str = None, agent_id=None):
        "Returns the first agent found that matches either the email or the id"
        if agent_id is not None and email != None:
            _LO.error("Pick either email or ID to search by, not both")
            return None
        if agent_id is not None:
            return self._get_agent_by_id(agent_id)
        if email is not None:
            return self._get_agent_by_email(email)

    def reply_to_ticket(self, ticket_id, agent_id, reply_txt):
        "Takes an HTML string and sends it as a reply from the given agent_id"
        url = f"https://{self.host}/api/v2/tickets/{ticket_id}/reply"
        data = {"body": reply_txt, "user_id": agent_id}
        self._request_and_validate(url, headers=None, body=data, method="post")

    def update_ticket(
        self, ticket_id, responder_id=None, status=None, ticket_type=None
    ):
        "updates a ticket with new values for its fields"
        url = f"https://{self.host}/api/v2/tickets/{ticket_id}"
        data = {}
        if responder_id is not None:
            data["responder_id"] = responder_id
        if status is not None:
            data["status"] = status
        if ticket_type is not None:
            data["type"] = ticket_type
        data = json.dumps(data)
        self._request_and_validate(url, body=data, method="put")

    def _get_agent_by_id(self, agent_id):
        "internal method"
        url = f"https://{self.host}/api/v2/agents/{agent_id}"
        agent_j = self._request_and_validate(url)

        agent_o = FreshdeskAgent()
        agent_o.from_dict(agent_j)
        return agent_o

    def _get_agent_by_email(self, email):
        """internal method"""

        if email is None or not isinstance(email, str):
            _LO.error("invalid parameters type passed to _get_agent_by_email")
            return FreshdeskAgent()
        if re.match(r".*@.*..*", email) is None:
            _LO.error("invalid email format passed to _get_agent_by_email")
            return FreshdeskAgent()

        email_f = quote_plus(email)
        url = f"https://{self.host}/api/v2/agents?email={email_f}"

        agent_j = self._request_and_validate(url)
        agent_o = FreshdeskAgent()
        if len(agent_j) > 0:
            agent_o.from_dict(agent_j[0])
        return agent_o

    def _request_and_validate(self, url, headers=None, body=None, method="get") -> dict:
        "internal method to request and return"
        if isinstance(body, dict):
            body = json.dumps(body)
        if headers is None:
            headers = self._get_default_headers()
        try:
            if method == "get":
                result = requests.get(url=url, headers=headers, data=body)
            elif method == "post":
                result = requests.post(url=url, headers=headers, data=body)
            elif method == "put":
                result = requests.put(url=url, headers=headers, data=body)
        except (ConnectionError) as err:
            _LO.error("Couldn't connect to FD %s - %s", url, err)
            return {}

        if result.status_code not in (200, 201):
            _LO.error(
                "Got an invalid response: %s - %s ", result.status_code, result.content
            )
            return {}
        if len(result.content) == 0:
            return None
        try:
            parsed_content = json.loads(result.content)
        except json.JSONDecodeError as err:
            _LO.error("Couldn't parse JSON from FD - %s", err)
            return {}
        return parsed_content

    def _request_and_validate_paginated(self, url, headers=None, body=None) -> list:
        getNextPage = True
        oldResponse = ""
        param_char = "&" if "?" in url else "?"
        current_page = 1
        pages = []
        while getNextPage and current_page <= 10:
            r_url = f"{url}{param_char}page={current_page}"
            resp = self._request_and_validate(r_url, headers, body)
            if resp == oldResponse:
                getNextPage = False
                break
            else:
                oldResponse = resp
                pages.append(resp)
                current_page = current_page + 1
        return pages


class FreshdeskTicket:
    "represents a freshdesk ticket"

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
        "Takes the dictionary provided by the Freshdesk API and populates them into the object parameters"
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


class FreshdeskAgent:
    "loosely represnts some of the parameters in a freshdesk agent"

    def __init__(self) -> None:
        self.id = 0
        self.name = ""
        self.email = ""

    def from_dict(self, api_result: dict) -> None:
        "takes the results from an API call and applies them to the object's parameters"
        self.id = api_result.get("id", 0)
        contact = api_result.get("contact", {})
        self.name = contact.get("name", "")
        self.email = contact.get("email", "")
