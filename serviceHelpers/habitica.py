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
        r: ResponseBlock
        dailies = r.content

        if not dailies:
            lo.error("Couldn't get habitica dailies - %s", r.error)
            return []
        active_dailies = []

        for daily in dailies["data"]:
            if daily["isDue"]:
                active_dailies.append(daily)
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

    def _get_habitica_headers(self):
        headers_obj = {
            # habitica asks app authors to self-report their identity - please change this if you modify the habitica code.
            "x-client": self.client_id,
            "x-api-user": self.user_id,
            "x-api-key": self.api_key
        }
        return headers_obj

    def _habitica_request_and_validate(self, url: str, method,  headers: dict, params: dict, body: dict) -> ResponseBlock:
        """internal method to make a GET request and return the parsed json response (either a dict of cards, or a dict of actions, or whatever is returned)

        arguments:
            `url` - the url to request, including the base url
            `headers` - any additional headers to send
            `params` - any additional params to send (the key and token are added automatically)
            `body` - any additional body to send

        returns:
            a dict of the parsed json response, or an empty dict on failure
        """
        if headers is None:
            headers = self._get_habitica_headers()
        else:
            headers = {**params, **self._get_habitica_headers()}

        r = _request_and_validate(url, method, headers, params, body)
        r: ResponseBlock
        if not r:
            try:
                r.error = body["error"]
            except:
                pass
        return r
