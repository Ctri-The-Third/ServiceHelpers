import logging
import json

lo = logging.getLogger("ZendeskUser")


class ZendeskUser:
    """takes a JSON encoded string and turns it into an object

    {user:
      {id:123,
      name:foo,
      email:email@domain.com
      organization_id:123}
    }"""

    def __init__(self, api_content: dict) -> None:
        responseObj = {}
        if isinstance(api_content, str):
            try:
                responseObj = json.loads(api_content)["user"]
            except (KeyError, json.JSONDecodeError):
                lo.warning("failed to parse a user from string")
        elif isinstance(api_content, dict):
            responseObj = api_content
        else:
            lo.error("Incorrect data type for responseStr")
            return

        self.user_id = responseObj["id"] if "id" in responseObj else 0
        self.user_id = self.user_id if isinstance(self.user_id, int) else 0

        self.name = responseObj["name"] if "name" in responseObj else ""
        self.name = self.name if isinstance(self.name, str) else ""

        self.email = responseObj["email"] if "email" in responseObj else ""
        self.email = self.email if isinstance(self.email, str) else ""

        self.organisationID = (
            responseObj["organization_id"] if "organization_id" in responseObj else None
        )
        self.organisationID = self.organisationID if isinstance(self, int) else None
