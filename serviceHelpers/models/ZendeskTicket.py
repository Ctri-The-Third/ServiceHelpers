import logging
import json
from datetime import datetime

from serviceHelpers.models.ZendeskUser import ZendeskUser

# 2021-11-25T12:00:15Z
_ZD_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"


class ZendeskTicket:
    "Represents a ticket in the Zendesk ticketing system"

    def __init__(self, host) -> None:
        self.zd_host = host
        self.url = ""
        self.id = 0
        self.created_ts = datetime.min
        self.updated_ts = datetime.min
        self.summary = ""
        self.desc = ""
        self.priority = ""
        self.status = ""
        self.assignee_id = None
        self.requester_id = None
        self.requester_name = ""
        self.requester = None
        self.group_id = 0
        self.comments = []
        self.tags = []
        self.logger = logging.getLogger("zendeskHelper.zendeskTicket")
        self.custom_fields = {}
        self.ticket_form_id = 0
        self.sla_breach_at = None
        pass

    def from_string(self, str):
        "takes an unparsed string expected to be from the ZD API, parsed and loads it"
        try:
            self.from_dict(json.loads(str))
        except Exception as e:
            self.logger.error("Couldn't parse a ticket string into a dict")
        return self

    def from_dict(self, source: dict):
        "takes a dictionary object expected to be parsed from the ZD API, and tries to load it"
        self.id = int(source["id"]) if "id" in source else self.id
        self.url = (
            f"https://{self.zd_host}/agent/tickets/{self.id}"
            if "id" in source
            else self.url
        )
        try:
            self.created_ts = (
                datetime.strptime(source["created_at"], _ZD_FORMAT)
                if "created_at" in source
                else self.created_ts
            )
            self.updated_ts = (
                datetime.strptime(source["updated_at"], _ZD_FORMAT)
                if "updated_at" in source
                else self.updated_ts
            )
        except ValueError as e:
            self.logger.error(
                "Date found but not parsed properly : %s", source["updated_at"]
            )
        self.tags = source["tags"] if "tags" in source else self.tags
        self.summary = source["subject"] if "subject" in source else self.summary
        self.desc = source["description"] if "description" in source else self.desc
        self.assignee_id = (
            source["assignee_id"] if "assignee_id" in source else self.assignee_id
        )
        self.requester_id = (
            source["requester_id"] if "requester_id" in source else self.requester_id
        )
        self.group_id = source["group_id"] if "group_id" in source else self.group_id
        self.status = source["status"] if "status" in source else self.status
        self.priority = source["priority"] if "priority" in source else self.priority
        self.ticket_form_id = source["ticket_form_id"] if "ticket_form_id" in source else self.ticket_form_id
        for custom_field in source["custom_fields"]:
            try:
                if custom_field["value"] is not None:
                    self.custom_fields[custom_field["id"]] = custom_field["value"]
            except KeyError as err:
                self.logger.warning("Couldn't properly get a custom field - %s", err)
        self.sla_breach_at = self._earliest_active_sla_breach(source.get("slas"))
        return self

    def _earliest_active_sla_breach(self, slas: dict):
        """From an inline `slas` sideload (include=tickets(slas)), returns the soonest
        active SLA breach time as a datetime, or None if there's no active SLA."""
        if not isinstance(slas, dict):
            return None
        breaches = []
        for metric in slas.get("policy_metrics", []):
            if metric.get("stage") == "active" and metric.get("breach_at"):
                try:
                    breaches.append(datetime.strptime(metric["breach_at"], _ZD_FORMAT))
                except (ValueError, TypeError):
                    self.logger.error(
                        "Couldn't parse SLA breach_at: %s", metric.get("breach_at")
                    )
        return min(breaches) if breaches else None

    def __str__(self) -> str:
        dict = {
            "id": self.id,
            "url": self.url,
            "created": datetime.strftime(self.created_ts, _ZD_FORMAT),
            "updated": datetime.strftime(self.updated_ts, _ZD_FORMAT),
            "subject": self.summary,
            "description": self.desc,
            "assignee_id": self.assignee_id,
            "requester_id": self.requester_id,
            "group_id": self.group_id,
            "ticket_form_id" : self.ticket_form_id
        }
        return json.dumps(dict, sort_keys=True)
