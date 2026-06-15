import logging
import json
from typing import List
import requests

from ._common import ResponseBlock, _request_and_validate

lo = logging.getLogger("HabiticaMapper")


class Habitica():
    def __init__(self, user_id, api_key, client_id: str) -> None:
        self.user_id = user_id
        self.api_key = api_key
        self.client_id = client_id

    def fetch_habitica_dailies(self, date_as_string: str) -> ResponseBlock:
        "Gets all the dailies, then filters down to just the active ones"
        url = f"https://habitica.com/api/v3/tasks/user?type=dailys&dueDate={date_as_string}"
        r = self._habitica_request_and_validate(url, requests.get)
        if not r:
            lo.error("Couldn't get habitica dailies - %s", r.error)
            return r

        active_dailies = [
            daily for daily in r.content["data"] if daily["isDue"]]
        r.content = active_dailies
        return r

    def complete_daily(self, daily_id: str) -> ResponseBlock:
        "Completes a given daily based on its daily"
        url = f"https://habitica.com/api/v3/tasks/{daily_id}/score/up"
        r = self._habitica_request_and_validate(url, requests.post)
        if not r:
            lo.error(
                "Unexpected error whilst completing a habitica task! \n%s", r.error)
        return r

    def reset_dailies(self) -> ResponseBlock:
        """Call's the endpoint that triggers the end of day process to executes"""
        url = "https://habitica.com/api/v3/cron"
        r = self._habitica_request_and_validate(url, requests.post)
        if not r:
            lo.warning("Failed to request Habitica reset!!")
        return r

    def fetch_habitica_tags(self):
        "Gets all the user's tags: their names and their IDs"

        url = "https://habitica.com/api/v3/tags"
        r = self._habitica_request_and_validate(url, requests.get)
        if not r:
            lo.warning("Failed to fetch tags from Habitica: %s ", r.error)

            return r.content
        else:
            r.content = r.content["data"]
            return r

    def _get_habitica_headers(self):
        return {
            # habitica asks app authors to self-report their identity
            "x-client": self.client_id,
            "x-api-user": self.user_id,
            "x-api-key": self.api_key,
        }

    def _habitica_request_and_validate(self, url: str, method, headers: dict = None, params: dict = None, body: dict = None) -> ResponseBlock:
        if headers is None:
            headers = self._get_habitica_headers()
        else:
            headers = {**headers, **self._get_habitica_headers()}

        r = _request_and_validate(url, method, headers, params, body)
        if not r:
            try:
                r.error = r.content["error"]
            except Exception:
                pass
        return r
