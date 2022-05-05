from datetime import datetime

TIMESTAMP_FORMAT = r"%Y-%m-%dT%H:%M:%S.%f%z"


class JiraTicket:
    "represents a single Jira ticket"

    def __init__(
        self,
        key="",
        summary="",
        assignee_id="",
        assignee_name="",
        assignee_email="",
        status="",
        priority="",
        description="",
        created=datetime.min,
        updated=datetime.min,
    ) -> None:
        self.key = key
        self.summary = summary
        self.description = description
        self.assignee_id = assignee_id
        self.assignee_name = assignee_name
        self.assignee_email = assignee_email
        self.status = status
        self.priority = priority
        self.created = created
        self.updated = updated

    def from_dict(self, new_dict: dict):
        """Takes the dictionary returned from the API and applies the contents to the matching parameters."""
        fields = new_dict["fields"] if "fields" in new_dict else {}
        assignee_dict = fields["assignee"] if "assignee" in fields else {}
        assignee_dict = {} if assignee_dict is None else assignee_dict
        priority_dict = fields["priority"] if "priority" in fields else {}

        self.key = new_dict["key"] if "key" in new_dict else self.key
        self.summary = fields["summary"] if "summary" in fields else self.summary
        self.description = (
            fields["description"] if "description" in fields else self.description
        )
        self.assignee_id = (
            assignee_dict["key"] if "key" in assignee_dict else self.assignee_id
        )
        self.assignee_id = (
            assignee_dict["accountId"]
            if "accountId" in assignee_dict
            else self.assignee_id
        )
        self.assignee_name = (
            assignee_dict["displayName"]
            if "displayName" in assignee_dict
            else self.assignee_name
        )
        self.assignee_email = (
            assignee_dict["emailAddress"]
            if "emailAddress" in assignee_dict
            else self.assignee_email
        )
        self.priority = (
            priority_dict["name"] if "name" in priority_dict else self.priority
        )

        status_dict = fields["status"] if "status" in fields else {}
        self.status = status_dict["name"] if "name" in status_dict else self.status

        self.created = (
            datetime.strptime(fields["created"], TIMESTAMP_FORMAT)
            if "created" in fields
            else self.created
        )

        self.updated = (
            datetime.strptime(fields["updated"], TIMESTAMP_FORMAT)
            if "updated" in fields
            else self.updated
        )

        return self
