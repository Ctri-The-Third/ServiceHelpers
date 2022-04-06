import logging
import pytest
from datetime import datetime


class ZendeskTicket():
    def __init__(self, host) -> None:
        self.host = host
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
        self.group_id = 0
        self.lo = logging.getLogger("zendeskHelper.zendeskTicket")
        pass 

    def from_string(self,str):
        try: 
            self.from_dict(json.loads(str))
        except Exception as e:
            self.lo.error("Couldn't parse a ticket string into a dict")
        return self 

    def from_dict(self,dict:dict):
            
        self.id = int(dict["id"]) if "id" in dict else self.id
        self.url = "{}agent/tickets/{}".format(self.host,self.id) if "id" in dict else self.url
        try:
            self.created_ts = datetime.strptime(dict["created_at"],_ZD_FORMAT) if "created_at" in dict else self.created_ts
            self.updated_ts = datetime.strptime(dict["updated_at"],_ZD_FORMAT) if "updated_at" in dict else self.updated_ts
        except Exception as e:
            self.lo.error("Date found but not parsed properly : %s",dict["updated_at"])
        self.summary = dict["subject"] if "subject" in dict else self.summary
        self.desc = dict["description"]  if "description" in dict else self.desc
        self.assignee_id = dict["assignee_id"]  if "assignee_id" in dict else self.assignee_id
        self.requester_id = dict["requester_id"]  if "requester_id" in dict else self.requester_id
        self.group_id = dict["group_id"]  if "group_id" in dict else self.group_id
        self.status = dict["status"] if "status" in dict else self.status
        self.priority = dict["priority"] if "priority" in dict else self.priority

        return self 
        
    def __str__(self) ->str:
        dict = {
            "id" : self.id,
            "url" : self.url,
            "created" : datetime.strftime(self.created_ts,_ZD_FORMAT),
            "updated" : datetime.strftime(self.updated_ts,_ZD_FORMAT),
            "subject" : self.summary,
            "description" : self.desc,
            "assignee_id" : self.assignee_id,
            "requester_id" : self.requester_id,
            "group_id" : self.group_id
        }
        return json.dumps(dict,sort_keys=True)