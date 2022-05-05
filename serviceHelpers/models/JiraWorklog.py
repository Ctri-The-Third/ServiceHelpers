from datetime import datetime
import logging

from xmlrpc.client import DateTime

TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%S.%f%z"


class JiraWorklog:
    "represents a single instance of time tracking on a Jira ticket"

    def __init__(self) -> None:
        self.created = datetime.datetime.min
        self.duration_seconds = 0
        self.author_key = ""
        self.author_email = ""
        self.logger = logging.getLogger("JiraWorklog")

    def from_json(self, json_dict: dict):
        "takes the JSON returned from the rest API and extracts appropriate properties"
        print(json_dict)

        try:
            self.created = datetime.strptime(json_dict.get("created"), TIMESTAMP_FORMAT)
        except (ValueError, Exception) as err:
            self.logger.error(
                "Couldn't parse %s as timestamp using format %s becase %s",
                json_dict.get("created"),
                TIMESTAMP_FORMAT,
                err,
            )
        try:
            self.duration_seconds = int(json_dict.get("timeSpentSeconds"))
        except (ValueError, Exception) as err:
            self.logger.error(
                "Couldn't parse %s as an int for duration, because %s",
                json_dict.get("timeSpentSeconds"),
                err,
            )
        return self

    @property
    def is_valid(self):
        "whether or not the necessary parameters are populated"
        return False
