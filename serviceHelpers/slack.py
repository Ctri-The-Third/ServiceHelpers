import json
import logging
from datetime import datetime
from html.parser import HTMLParser
from io import StringIO

import requests

lo = logging.getLogger("slack service helper")


class slack:
    """This class provides methods for interacting with a single slack server."""

    def __init__(self, token="", webhook="") -> None:
        """Initialize the slack object.

        * `token` is the oauth token from slack.dev
        * `webhook` is an optional way of defining a single webhook to send messages by default.
        """
        self.token = token
        self.webhook = webhook

    def post_to_slack_via_token(
        self, text, channelID, parent_ts=None, unfurl: bool = True
    ):
        """Use the `chat.postMessage` api call to send a message to a specified channelID.

        * `parent_ts` = a timestamp for an existing message in the channel. This will cause the message to sent to a thread.
        * `unfurl` = a boolean that controls whether or not URL previews should be shown.
        """
        url = "https://slack.com/api/chat.postMessage"
        headers = self._get_default_headers()
        body = {"channel": channelID, "text": text, "unfurl_links": unfurl}

        if parent_ts is not None:
            body["thread_ts"] = parent_ts

        response = requests.post(url, data=json.dumps(body), headers=headers)
        try:
            r = json.loads(response.content)
            if "error" in r:
                logging.warning("Couldn't post to slack: %s", r["error"])
        except Exception as e:
            logging.warning("Couldn't post to slack: %s", e)
        return self._get_ts_from_post_response(response.text)

    def _get_ts_from_post_response(self, response) -> str:
        returnstr = ""
        j_repsonse = {}
        try:
            j_repsonse = json.loads(response)
        except:
            logging.warn(
                "Couldn't get a timestamp from the slack post - this means no replies are possible"
            )
            return returnstr

        if "ts" in j_repsonse:
            returnstr = j_repsonse["ts"]

        return returnstr

    def _get_default_headers(self):
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }

        return headers

    def postToSlackVia_webhook(self, webhook="", text=None) -> str:

        if webhook == "":
            webhook = self.webhook
        if webhook == "":
            return logging.error(
                "cannot post using webhook without passing in a webhook"
            )
        url = self.webhook
        headers = {"Content-type": "application/json"}
        body = {"text": text}
        r = requests.post(url=url, headers=headers, data=json.dumps(body))
        print(r)
        print(r.content)
        return r.content

    def fetch_messages(self, channel, since: datetime = datetime.min, limit=200):
        return_messages = []
        cont = True
        oldest = since.timestamp
        while cont:
            url = "https://slack.com/api/conversations.history"
            headers = self._get_default_headers()
            params = {
                "channel": channel,
                "oldest": oldest,
                "limit": limit,
                "includsive": True,
            }
            response = requests.post(url=url, headers=headers, params=params)
            content = json.loads(response.content)

            messages = content["messages"] if "messages" in content else {}
            return_messages += messages

            if len(messages) == 0:
                cont = False
            else:
                oldest = messages[0]["ts"]

            if response.status_code != 200:
                print(content, response.status_code)
        return return_messages
