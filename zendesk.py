import json
import logging
import requests
from models.ZendeskTicket import ZendeskTicket
from models.ZendeskOrg import ZendeskOrganisation
from models.ZendeskUser import ZendeskUser

lo = logging.getLogger("ZendeskMapper")


class zendesk:
    """Represents a single zendesk tenency, and exposes methods for interacting with it via the API."""

    def __init__(self, host, api_key):
        
        lo.error(host)
        lo.error("Key equals ***?" % (api_key == "***"))
            
        self.host = host
        self.key = api_key
        self._headers = {"Authorization": f"Basic {self.key}"}
        if host is None or api_key is None:
            lo.warning("Zendesk object initialised without necessary parameters!!")

    def search_for_tickets(self, search_string):
        """uses the zendesk search notation that's detailed here:
        https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/
        """
        # gets the most recently 100 Zendesk tickets.
        url = str.format(
            "https://{0}/api/v2/search.json?query={1}", self.host, search_string
        )
        response = requests.get(url, headers=self._headers)
        if response.status_code != 200:
            lo.warning(
                "couldn't retrieve zendesk tickets [%s]\n%s",
                response.status_code,
                response.content,
            )
            return []

        try:
            tickets = json.loads(response.content)["results"]
        except Exception as e:
            lo.error(
                "Couldn't parse zendesk tickets as json! %s\n%s,", e, response.content
            )
            return []
        return self._parse_tickets(tickets)

    def _parse_tickets(self, tickets: list):
        """expecting a list of ticket dicts"""
        responseObj = {}
        for ticket in tickets:  # tickets are now indexed by ID

            new_ticket = ZendeskTicket(self.host).from_dict(ticket)
            if new_ticket.id != 0:
                responseObj[f"{new_ticket.id}"] = new_ticket
        return responseObj

    def get_user(self, userID: int) -> ZendeskUser:
        """fetches a user from an ID"""
        url = f"https://{self.host}/api/v2/users/{userID}.json"
        try:
            response = requests.get(url, headers=self._headers)
        except Exception as ex:
            lo.error("Something really weird happened hitting url: %s\n %s", url,ex )
            return ZendeskUser("")

        if response.status_code != 200:
            lo.warning(
                "couldn't retrieve zendesk user %s [%s]\n%s",
                userID,
                response.status_code,
                response.content,
            )

        return ZendeskUser(response.content)

    def get_organisation(self, orgID: int) -> ZendeskOrganisation:
        """Fetches an organisation from an ID. Not yet implemented."""
        raise NotImplementedError
        # TODO - finish the below
        url = str.format(
            f"https://{self.host}/api/v2/users/{orgID}.json".format(self.host, orgID)
        )
        response = requests.get(url, headers=self._headers)
        responseObj = {}
        if response.status_code != 200:
            logging.warning(
                "couldn't retrieve zendesk organisation %s [%s]\n%s",
                orgID,
                response.status_code,
                response.content,
            )

        try:
            responseObj = json.loads(response.content)
        except Exception as e:
            lo.warning(
                "Couldn't parse org info as json! %s, %s\n%s",
                orgID,
                e,
                response.content,
            )

        return ZendeskOrganisation(responseObj)
