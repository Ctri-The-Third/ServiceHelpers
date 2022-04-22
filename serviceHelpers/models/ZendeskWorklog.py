import json
import logging
from datetime import datetime

_ZD_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"


class ZendeskWorklog:
    """Represents a single piece of work associated with a user in Zendesk.

    Is formed from the audit logs for a given ticket."""

    def __init__(
        self,
        author_id=None,
        timestamp: datetime = None,
        time_in_seconds: int = None,
    ):
        self.author_id = author_id
        self.timestamp = timestamp
        self.duration = time_in_seconds
        self.logger = logging.getLogger("ZendeskWorklog")

    def from_json(self, audit_dict: dict, field_id_for_time_log) -> None:

        "Takes an audit record and extracts relevant info"
        if "events" not in audit_dict:
            self.logger.warning(
                "Got something unexpected from ZD, missing `events` key in audit record"
            )
            return False
        if "author_id" not in audit_dict:
            return False

        self.author_id = audit_dict["author_id"]

        for event in audit_dict["events"]:
            if "type" not in event or "field_name" not in event:
                self.logger.debug("Skipping over a non field creation/update")
                continue

            if event["field_name"] == f"{field_id_for_time_log}":
                self.timestamp = datetime.strptime(audit_dict["created_at"], _ZD_FORMAT)
                self.duration = int(event["value"])

    @property
    def is_valid(self):
        "Whether or not all the necessary fields are set and this is a real worklog"
        return (
            self.author_id is not None
            and self.author_id != ""
            and self.duration is not None
            and self.duration > 0
            and self.timestamp is not None
        )

    def __str__(self) -> str:
        ret = json.dumps(
            {
                "author_id": self.author_id,
                "timestamp": datetime.strftime(self.timestamp, _ZD_FORMAT),
                "time_in_seconds": self.duration,
            }
        )
        return ret
