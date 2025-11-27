import json
import logging
import requests


from serviceHelpers.models.ZendeskTicket import ZendeskTicket
from serviceHelpers.models.ZendeskOrg import ZendeskOrganisation
from serviceHelpers.models.ZendeskUser import ZendeskUser
from serviceHelpers.models.ZendeskWorklog import ZendeskWorklog

_LO = logging.getLogger("ZendeskMapper")


class zendesk:
    """Represents a single zendesk tenency, and exposes methods for interacting with it via the API."""

    def __init__(self, host: str, api_key):

        self.host = host
        self.key = api_key
        self._headers = {"Authorization": f"Basic {self.key}"}
        self.logger = _LO
        if host is None or api_key is None:
            _LO.warning("Zendesk object initialised without necessary parameters!!")

    def get_comments(self, ticket_id:int = None, ticket:ZendeskTicket = None):
        if not ticket_id and not ticket:
            self.logger.warning("No id/ticket passed to zendesk.get_comments")
            return None
        if ticket:
            ticket_id = ticket.id
        
        url = f"https://{self.host}/api/v2/tickets/{ticket_id}/comments?sort=-created_at"
        
        try:
            response = self._request_and_validate_paginated(url)
            comments = response[0]["comments"]
            if ticket is not None: #if we're searching by ticket, not by ticket_id
                ticket.comments = comments
                return ticket #return a ticket that now includes comments
            return comments #return just the comments 
        except Exception as err:
            self.logger.error("Unknown error when getting comments for ticket %s, %s", ticket_id,err)
        return []

    def search_for_tickets(self, search_string):
        """uses the zendesk search notation that's detailed here:
        https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/
        """
        # gets the most recently 100 Zendesk tickets.
        url = (
            f"https://{self.host}/api/v2/search.json?query=type:ticket {search_string}"
        )

        pages = self._request_and_validate_paginated(url)
        tickets = {}
        for page in pages:
            for ticket_j in page.get("results", []):
                ticket_o = ZendeskTicket(self.host)
                ticket_o.from_dict(ticket_j)
                tickets[ticket_o.id] = ticket_o
        return tickets

    def search_for_users(self, search_string):
        """Uses the zendesk search notation that's detailed here:
        https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/"""

        url = f"https://{self.host}/api/v2/search.json?query=type:user {search_string}"
        pages = self._request_and_validate_paginated(url)
        users = {}
        for page in pages:
            for user_j in page.get("results", []):
                user_o = ZendeskUser(user_j)
                users[user_o.user_id] = user_o
        return users

    def get_user(self, userID: int) -> ZendeskUser:
        """fetches a user from an ID"""
        url = f"https://{self.host}/api/v2/users/{userID}.json"
        response = self._request_and_validate(url)

        return ZendeskUser(response.get("user", {}))

    def get_worklogs(
        self, ticket_id: int, time_since_last_update_field_id: int
    ) -> list:
        """Fetches a list of worklog objects from Zendesk using the audit trail"""
        url = f"https://{self.host}/api/v2/tickets/{ticket_id}/audits"
        response = self._request_and_validate_paginated(url)

        #            "author_id": 387974337212,
        #            "created_at": "2022-04-22T09:16:04Z",
        #            "events": [
        #                    "field_name": "360028226391", #total
        #                    "value": "300",

        #                    "value": "900",
        #                    "field_name": "360028226411", #most recent
        logs = []
        for page in response:
            if "audits" not in page:
                self.logger.warning(
                    "Got something unexpected from ZD, missing `audits` key"
                )
                continue
            for audit in page["audits"]:

                worklog = ZendeskWorklog()
                worklog.from_json(audit, time_since_last_update_field_id)
                if worklog.is_valid:
                    logs.append(worklog)

        return logs
    
    def update_ticket(self, ticket_id:int, body:dict):
        """Updates a ticket with the given body dict. Provide a key-value pair for each field to update."""
        url = f"https://{self.host}/api/v2/tickets/{ticket_id}"
        

        body_json = json.dumps({
            "ticket": body
        })

        response = self._request_and_validate(url, body=body_json)

        return response
    def assign_ticket(self, ticket_id:int, user_id:int):
        """Assigns a ticket to a user"""
        
        body = { "assignee_id": user_id }
        return self.update_ticket(ticket_id, body)

        

    def _request_and_validate(self, url, headers=None, body=None) -> dict:
        "internal method to request and return"
        if headers is None:
            headers = self._headers

        if body is not None and  isinstance(body, dict):
            body = json.dumps(body)
            


        try:
            result = requests.get(url=url, headers=headers, data=body)
        except (ConnectionError) as e:
            _LO.error("Couldn't connect to Zendesk %s - %s", url, e)
            return {}
        if result.status_code != 200:
            _LO.error(
                "Got an invalid response: %s - %s ", result.status_code, result.content
            )
            return {}
        try:
            parsed_content = json.loads(result.content)
        except json.JSONDecodeError as e:
            _LO.error("Couldn't parse JSON from Zendesk - %s", e)
            return {}
        return parsed_content

    def _request_and_validate_paginated(self, url, headers=None, body=None) -> list:

        param_char = "&" if "?" in url else "?"
        next_page = 1
        pages = []
        while next_page is not None:
            r_url = f"{url}{param_char}page={next_page}"
            resp = self._request_and_validate(r_url, headers, body)
            pages.append(resp)
            next_page = resp.get("nextPage", None)
        return pages

    def get_organisation(self, orgID: int) -> ZendeskOrganisation:
        """Fetches an organisation from an ID. Not yet implemented."""

        url = f"https://{self.host}/api/v2/users/{orgID}.json".format(self.host, orgID)
        org_j = self._request_and_validate(url)
        org_o = ZendeskOrganisation(org_j)

        return org_o


    def get_form_d(self, formID:int) -> dict:
        "fetches from `/api/v2/ticket_forms/` and returns the response as a dict. "

        url = f"https://{self.host}/api/v2/ticket_forms/{formID}"
        form_j = self._request_and_validate(url)

        return form_j["ticket_form"] if "ticket_form" in form_j else form_j
        