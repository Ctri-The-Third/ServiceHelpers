import logging
from pytest import param

class JiraDetails:
    """represents the settings for a jira object"""

    def __init__(self) -> None:
        self.host = ""
        self.name = ""
        self.key = ""
        self.default_assignee = ""

        self.logger = logging.getLogger("jiraDetails")

    def from_dict(self, src: dict):
        """Takes a dictionary and tries to map appropriate details to the class parameters."""
        self.name = src["instanceName"] if "instanceName" in src else ""
        self.host = src["instanceHost"] if "instanceHost" in src else ""
        self.key = src["bearerToken"] if "bearerToken" in src else ""
        self.default_assignee = src["instanceUserID"] if "instanceUserID" in src else ""

        return self

    @param
    def valid(self):
        """self checking of the parameters."""
        valid = True
        if self.name == "":
            self.logger.warning("jira obj name is blank")
            valid = False
        if self.host == "":
            self.logger.warning("jira object host is blank")
            valid = False
        if self.default_assignee == "":
            self.logger.warning("jira object primary_user_id is blank")
        if self.key == "":
            self.logger.warning("key missing from jira settings")
            valid = False

        return valid
