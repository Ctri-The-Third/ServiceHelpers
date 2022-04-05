import logging 
import json

lo = logging.getLogger("ZendeskUser")

class ZendeskUser():
    """takes a JSON encoded string and turns it into an object
    
    {user:
      {id:123,
      name:foo,
      email:email@domain.com
      organization_id:123}
    } """
    def __init__(self,responseStr) -> None:
        responseObj = {}
        try:
            responseObj = json.loads(responseStr)["user"]
        except KeyError:
            lo.warning("failed to parse a user from string")

        self.userID = responseObj["id"] if "id" in responseObj else 0
        self.userID = self.userID if isinstance(self.userID, int) else 0 

        self.name = responseObj["name"] if "name" in responseObj else ""
        self.name = self.name if isinstance(self.name,str) else ""

        self.email = responseObj["email"] if "email" in responseObj else ""
        self.email = self.email if isinstance(self.email,str) else ""

        self.organisationID = responseObj["organization_id"] if "organization_id" in responseObj else None
        self.organisationID = self.organisationID if isinstance(self, int) else None
        