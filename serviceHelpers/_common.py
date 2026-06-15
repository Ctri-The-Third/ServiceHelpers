import requests
import json
import logging
import time

_LO = logging.getLogger("common-methods")
_LO.setLevel(logging.WARN)


# Basic ANSI color codes
RESET = "\033[0m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright (light) colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Text effects
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Text effects
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
STRIKE = "\033[9m"


def _request_and_validate(url, method, headers=None, params=None, body=None, retry=0) -> "ResponseBlock":
    """Make an HTTP request and return a ResponseBlock.

    arguments:
        `url`     - the url to request, including the base url
        `method`  - the requests method to use (requests.get, requests.post, etc.)
        `headers` - any additional headers to send
        `params`  - any additional params to send
        `body`    - any additional body to send
        `retry`   - internal retry counter for rate-limit back-off

    returns:
        ResponseBlock — check .okay/.error before using .content
    """
    try:
        result = method(url=url, headers=headers, data=body,
                        params=params, timeout=10)
    except ConnectionError as e:
        response = ResponseBlock()
        response.error = f"Couldn't connect to {url} - {e}"
        _LO.error("Couldn't connect to %s - %s", url, e)
        return response

    if result.status_code == 429:
        _LO.warning("Rate limit, standing by for a moment")
        if retry >= 5:
            return ResponseBlock(result)
        retry += 1
        time.sleep(pow(retry, 2))
        return _request_and_validate(url, method, headers, params, body, retry)

    if result.status_code == 400:
        response = ResponseBlock(result)
        response.error = f"Invalid request to {url} - {result.content}"
        _LO.error("Invalid request to %s - %s", url, result.content)
        return response
    if result.status_code == 401:
        response = ResponseBlock(result)
        response.error = f"Unrecognised token/key at {url} - {result.content}"
        _LO.error("Unrecognised token/key at  %s - %s", url, result.content)
        return response
    if result.status_code == 403:
        response = ResponseBlock(result)
        response.error = f"Insufficient permissions at {url} - {result.content}"
        _LO.error("insufficient permissions %s - %s", url, result.content)
        return response
    if result.status_code != 200:
        response = ResponseBlock(result)
        response.error = f"Unexpected response {result.status_code} from {url} - {result.content}"
        _LO.error("Got an invalid response: %s - %s ",
                  result.status_code, result.content)
        return response

    return ResponseBlock(result)


def _get_and_validate(url, headers=None, params=None, body=None,   retry=0) -> "ResponseBlock":
    return _request_and_validate(url, requests.get, headers=headers, params=params, body=body, retry=retry)


def _post_and_validate(url, headers=None, params=None, body=None, retry=0) -> "ResponseBlock":
    return _request_and_validate(url, requests.post, headers=headers, params=params, body=body, retry=retry)


def _put_and_validate(url, headers=None, params=None, body=None, retry=0) -> "ResponseBlock":
    return _request_and_validate(url, requests.put, headers=headers, params=params, body=body, retry=retry)


def _delete_and_validate(url, headers=None, params=None, body=None, retry=0) -> "ResponseBlock":
    return _request_and_validate(url, requests.delete, headers=headers, params=params, body=body, retry=retry)


class ResponseBlock:

    def __init__(self, response_object: requests.Response = None):
        if response_object and isinstance(response_object, requests.Response):
            self.okay = response_object.status_code in (200, 201)
            self.error = response_object.status_code
            try:
                self.content = json.loads(response_object.content)
            except json.JSONDecodeError as err:
                self.error = err
                self.okay = False
                self.content = {}
        else:
            self.okay = False
            self.error = "Unknown"
            self.content = {}

    def __bool__(self):
        return self.okay
