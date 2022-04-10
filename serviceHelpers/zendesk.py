import json
import logging
import requests


from serviceHelpers.models.ZendeskTicket import ZendeskTicket
from serviceHelpers.models.ZendeskOrg import ZendeskOrganisation
from serviceHelpers.models.ZendeskUser import ZendeskUser

_LO = logging.getLogger("ZendeskMapper")


class zendesk:
    """Represents a single zendesk tenency, and exposes methods for interacting with it via the API."""

    def __init__(self, host: str, api_key):

        self.host = host
        self.key = api_key
        self._headers = {"Authorization": f"Basic {self.key}"}
        if host is None or api_key is None:
            _LO.warning("Zendesk object initialised without necessary parameters!!")

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

    def _request_and_validate(self, url, headers=None, body=None) -> dict:
        "internal method to request and return"
        if headers is None:
            headers = self._headers

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
