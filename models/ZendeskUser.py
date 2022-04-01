import logging 
import json
import pytest

lo = logging.getLogger("ZendeskUser")

class ZendeskUser():
    def __init__(self,responseStr) -> None:
        responseObj = {}
        try:
            responseObj = json.loads(responseStr)["user"]
        except Exception as e:
            lo.warning("failed to parse a user from string")

        self.userID = responseObj["id"]
        self.name = responseObj["name"]
        self.email = responseObj["email"]
        self.organisationID = responseObj["organization_id"]
        self.organisation = {}