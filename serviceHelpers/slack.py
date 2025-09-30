import json
import logging
from datetime import datetime

import requests

LO = logging.getLogger("slack service helper")


class slack:
    """This class provides methods for interacting with a single slack server."""

    def __init__(self, token="", webhook="") -> None:
        """Initialize the slack object.

        * `token` is the oauth token from slack.dev
        * `webhook` is an optional way of defining a single webhook to send messages by default.
        """
        self.token = token
        self.webhook = webhook
        self.logger = LO

    def post_to_slack_via_token(
        self, text, channelID, parent_ts=None, unfurl: bool = True, attachment=None
    ):
        """Use the `chat.postMessage` api call to send a message to a specified channelID.

        * `parent_ts` = a timestamp for an existing message in the channel. This will cause the message to sent to a thread.
        * `unfurl` = a boolean that controls whether or not URL previews should be shown.

        returns: the timestamp of the posted message or None on failure
        """
        url = "https://slack.com/api/chat.postMessage"
        headers = self._get_default_headers()
        body = {"channel": channelID, "text": text, "unfurl_links": unfurl}

        if parent_ts is not None:
            body["thread_ts"] = parent_ts

        if attachment is not None:
            body["attachments"] = attachment

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
        except requests.JSONDecodeError:
            logging.warning
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
        """
        DEPRECIATED - use post_to_slack_via_token
        
        """
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
        "Fetches messages from slack in a specific channel, from a given datetime"
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

    def fetch_user_profile(self, user_id: str) -> dict:
        "With the ID for a slack user, return their profile as a dictionary"

        if not isinstance(user_id, str):
            logging.error("user_id must be a string")
            return {}

        url = "https://slack.com/api/users.profile.get"
        parameters = {"user": user_id}
        headers = self._get_default_headers()

        parsed_json = _request_and_validate(url, headers, params=parameters)
        if parsed_json.get("ok") is not True:
            return {}

        return parsed_json.get("profile", {})

    def update_message(self, channel, message_ts, new_text, attachment=None):
        """Edit an existing message using the chat.update API call.

        * `channel` = the channel ID containing the message to update
        * `message_ts` = the timestamp of the message to update (returned from original post)
        * `new_text` = the new text content for the message
        * `attachment` = optional new attachments for the message
        
        Returns the timestamp of the updated message on success, empty string on failure.
        """
        url = "https://slack.com/api/chat.update"
        headers = self._get_default_headers()
        body = {
            "channel": channel,
            "ts": message_ts,
            "text": new_text
        }

        if attachment is not None:
            body["attachments"] = attachment

        response = requests.post(url, data=json.dumps(body), headers=headers)
        try:
            r = json.loads(response.content)
            if "error" in r:
                logging.warning("Couldn't update slack message: %s", r["error"])
                return ""
            elif "ok" in r and r["ok"]:
                logging.info("Successfully updated slack message")
                return self._get_ts_from_post_response(response.text)
        except Exception as e:
            logging.warning("Couldn't update slack message: %s", e)
        
        return ""

    def get_message_info(self, channel, message_ts):
        """Retrieve information about a specific message using its timestamp.
        
        * `channel` = the channel ID containing the message
        * `message_ts` = the timestamp of the message to retrieve
        
        Returns a dictionary with message information on success, empty dict on failure.
        This can be useful to verify a message exists before attempting to edit it.
        """
        url = "https://slack.com/api/conversations.history" 
        headers = self._get_default_headers()
        params = {
            "channel": channel,
            "latest": message_ts,
            "oldest": message_ts,
            "inclusive": True,
            "limit": 1
        }

        parsed_json = _request_and_validate(url, headers, params=params)
        if parsed_json.get("ok") is not True:
            logging.warning("Couldn't retrieve message info: %s", parsed_json.get("error", "unknown error"))
            return {}
        
        messages = parsed_json.get("messages", [])
        if len(messages) > 0 and messages[0].get("ts") == message_ts:
            return messages[0]
        
        logging.warning("Message with timestamp %s not found in channel %s", message_ts, channel)
        return {}


def _request_and_validate(url, headers, body=None, params=None) -> dict:
    "internal method to request and return results from Slack"

    try:
        result = requests.get(url=url, headers=headers, data=body, params=params)
    except (ConnectionError) as e:
        LO.error("Couldn't connect to Slack API %s - %s", url, e)
        return {}
    if result.status_code != 200:
        LO.error(
            "Got an invalid response on the endpoint %s: %s - %s ",
            url,
            result.status_code,
            result.content,
        )
        return {}
    try:
        parsed_content: dict = json.loads(result.content)
    except json.JSONDecodeError as e:
        LO.error("Couldn't parse JSON from Jira - %s", e)
        return {}
    if "ok" not in parsed_content:
        LO.warning("Doesn't look like valid Slack JSON?")
    elif parsed_content.get("ok", "") != True:
        LO.warning(
            "Request made it to slack but was rejected, %s",
            parsed_content.get("error", "no error block found"),
        )

    return parsed_content
