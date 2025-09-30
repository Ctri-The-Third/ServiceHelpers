import json
import time
from asyncio.log import logger
import logging

import re
import requests


HOST = "https://api.trello.com/"
API_VERSION = "1"
BASE_URL = f"{HOST}{API_VERSION}/"
_LO = logging.getLogger("TrelloHelper")
_LO.setLevel(logging.WARN)


class trello:
    """represents a trello board, and provides methods to interact with it

    Args:
        `board_id` (str): the id of the board to interact with
        `key` (str): the trello api key
        `token` (str): the trello api token for the authenticated user
    """

    def __init__(self, board_id, key, token) -> None:
        self.board_id = board_id
        self.key = key
        self.token = token
        self._cached_cards = {}  # listID into list of cards, sorted by their IDs
        self.dirty_cache = True

    def find_trello_card(self, regex) -> dict:
        "uses regexes to search name and description of cached / fetched cards, or exactly matching IDs. Returns the first it finds."
        cards = (
            self.fetch_trello_cards()
            if self.dirty_cache
            else list(self._cached_cards.values())
        )
        for card in cards:
            card: dict
            try:
                if (
                    card.get("id", "") == regex
                    or re.search(regex, card.get("name", ""))
                    or re.search(regex, card.get("desc", ""))
                ):
                    return card

            except (Exception,) as err:
                _LO.error(
                    "Failed to parse trello card's title & description when looking for matches, %s ",
                    err,
                )
        return

    def find_trello_cards(self, regex):
        "uses regexes to search name and description of cached / fetched cards. Returns all cards found."

        cards = (
            self.fetch_trello_cards()
            if self.dirty_cache
            else list(self._cached_cards.values())
        )
        foundCards = []
        for card in cards:
            card: dict
            if (
                card.get("id", "") == regex
                or re.search(regex, card.get("name", ""))
                or re.search(regex, card.get("desc", ""))
            ):
                foundCards.append(card)
        return foundCards

    def search_trello_cards(self, search_criteria, board_id=None) -> list:
        "uses the trello search criteria, can return archived cards"
        url = f"{BASE_URL}search"
        params = {}
        params["card_fields"] = "desc, name"
        params["modelTypes"] = "cards"
        if board_id:
            params["idBoards"] = board_id
        params["query"] = search_criteria

        r = self._request_and_validate(url, params=params)
        return r

    def purge_trello_cards(
        self, title_pattern="", descPattern="", target_lists=None, custom_field_ids=None
    ):
        """
        * titlePattern and descPattern are both used for regex searches through title and card descriptions
        * customFieldIDs and targetLists are  an array of IDs. Cards without those fields populated, or outside of those fields will be deleted.
        * targetLists can have the value `[*]` which will result in all lists being considered valid
        """
        target_lists = [] if target_lists is None else target_lists
        custom_field_ids = [] if custom_field_ids is None else custom_field_ids
        cards = self.fetch_trello_cards() if self.dirty_cache else self._cached_cards

        for card in cards:
            # search through all cards, attempt to DQ from list. If all checks pass and not DQd, delete
            continue_search = True
            if target_lists[0] != "*" and card["idList"] not in target_lists:
                continue_search = False
            if continue_search and custom_field_ids != []:
                # if we're clear to continue, and there is an ID, scruitinse ID
                continue_search = False
                for field in card["customFieldItems"]:
                    if field["idCustomField"] in custom_field_ids:
                        # card has the right ID
                        continue_search = True
            if (
                continue_search
                and title_pattern != ""
                and re.search(title_pattern, card["name"]) is None
            ):
                # no objections found so far, there is a regex for the title, and it missed
                continue_search = False
            if (
                continue_search
                and descPattern != ""
                and re.search(descPattern, card["desc"]) is None
            ):
                # no objections found so far, there is a regex for the description
                continue_search = False

            if continue_search:
                # we found no disqualifiers.
                self.delete_trello_card(card["id"])
                self.dirty_cache = True
        return

    def get_all_cards_on_list(self, list_id):
        """Returns all the visible cards on a given list"""
        if self.dirty_cache:
            self.fetch_trello_cards()
        cards = self._cached_cards
        filtered_cards = {k: v for k, v in cards.items() if v["idList"] == list_id}
        return filtered_cards
        # creates Key:value FOR - (for each Key, value in cards) BUT ONLY IF the list_id matches

    def fetch_trello_cards(self) -> list:
        """returns all visible cards from the board"""
        url = f"{BASE_URL}boards/%s/cards" % (self.board_id)
        params = self._get_trello_params()
        params["filter"] = "visible"

        # params["customFieldItems"] = "true"

        cards = self._request_and_validate(url, params=params)

        self._populate_cache(cards)
        self.dirty_cache = False
        return cards

    def fetch_trello_card(self, card_id: str) -> dict:
        "returns a single trello card"

        url = f"{BASE_URL}cards/%s" % card_id
        params = self._get_trello_params()
        card = self._request_and_validate(url, params=params)

        self._populate_cache([card])
        return card

    def get_trello_card(self, card_id: str) -> dict:
        "gets a card from the cache, or fetches it"
        if card_id in self._cached_cards:
            return self._cached_cards[card_id]
        else:
            return self.fetch_trello_card(card_id)

    def convert_index_to_pos(self, list_id, position) -> float:
        "takes the index of a card, and finds a suitable position float value for it"
        cards = self.get_all_cards_on_list(list_id)
        cards = self._sort_trello_cards_dict(cards)

        cards = list(cards.items())
        if len(cards) == 1:
            return cards[0][1].get("pos", 0) + 1
        if len(cards) == 0:
            return 0
        if position == 0:
            return (cards[0][1].get("pos", 0)) / 2
        if position == -1:
            return cards[len(cards) - 1][1].get("pos", 0) + 0.0000001

        try:
            card = cards[position]
            prev_card = cards[position - 1]
            pos = (prev_card[1]["pos"] + card[1]["pos"]) / 2
            return pos
        except IndexError:
            _LO.error(
                "got a horrible value when trying to convert index to pos value - index=[%s], len=[%s]"
            )
            return 0

    def fetch_actions_for_board(
        self,
        since: str = None,
        before: str = None,
        limit: int = None,
        actions_filter: str = None,
    ) -> list:
        """hits the `/1/boards/{{board_id}}/actions` endpoint

        Filter should be a comma seperated list of action types:
        https://developer.atlassian.com/cloud/trello/guides/rest-api/action-types/

        returns a list of lists of actions, each list being a page of actions
        """

        url = f"{BASE_URL}boards/{self.board_id}/actions"

        params = {
            "memberCreator": "false",
            "member": "false",
        }
        if limit is not None:
            params["limit"] = limit
        if since is not None:
            params["since"] = since
        if before is not None:
            params["before"] = before
        if actions_filter is not None:
            params["filter"] = actions_filter

        actions = self._request_and_validate_paginated(
            url,
            params=params,
            page_limit=10,
            page_size_limit=50,
            since=since,
        )
        return actions

    def create_card(
        self,
        title,
        list_id,
        description=None,
        labelID=None,
        dueTimestamp=None,
        position: int = None,
    ):
        "`position` is the numerical index of the card on the list it's appearing on. 0 = top, 1 = second, -1 = last"

        params = self._get_trello_params()
        params["name"] = title

        if description is not None:
            params["desc"] = description
        if labelID is not None:
            params["idLabels"] = labelID
        if dueTimestamp is not None:
            params["due"] = dueTimestamp
        if position is not None and position >= 0:
            # if position is -1 (bottom) then use default behaviour
            params["pos"] = self.convert_index_to_pos(list_id, position)
        params["idList"] = list_id

        url = f"{BASE_URL}cards/"
        r = requests.post(url, params=params, timeout=10)
        if r.status_code != 200:
            print(
                "Unexpected response code [%s], whilst creating card [%s]"
                % (r.status_code, title)
            )
            print(r.content)
            return
        card = json.loads(r.content)

        if not self._try_update_cache(r.content):
            self.dirty_cache = True
        return card

    def update_card(
        self,
        card_id: str,
        title: str,
        description: str = None,
        pos: float = None,
        new_list_id: str = None,
        new_due_timestamp: str = None,
    ):
        "Update the card with a new title, description, position. use list_id to move to another list."
        params = self._get_trello_params()
        params["name"] = title

        if description is not None:
            params["desc"] = description
        if pos is not None:
            params["pos"] = pos
        if new_list_id is not None:
            params["idList"] = new_list_id
        if new_due_timestamp is not None:
            params["due"] = new_due_timestamp
        url = f"{BASE_URL}cards/%s" % (card_id)
        r = requests.put(url, params=params, timeout=10)
        if r.status_code != 200:
            _LO.error(
                "ERROR: %s couldn't update the Gmail Trello card's name", r.status_code
            )
            return
        if not self._try_update_cache(r.content):
            self.dirty_cache = True
        return

    def create_checklist_on_card(self, cardID, checklistName="Todo items") -> str:
        "create a checklist on an existing card, returns the ID for use."
        url = f"{BASE_URL}checklists"
        params = self._get_trello_params()
        params["idCard"] = cardID
        params["name"] = checklistName

        r = requests.post(url, params=params, timeout=10)

        if r.status_code != 200:
            print(
                "ERROR: %s when attempting create a trello checklist (HabiticaMapper) \n%s"
                % (r.status_code, r.content)
            )
            return
        checklist = json.loads(r.content)
        self.dirty_cache = True
        return checklist["id"]

    def add_item_to_checklist(self, checklistID: str, text: str):
        "add a single item to an existing checklist"
        url = f"{BASE_URL}checklists/%s/checkItems" % (checklistID)
        params = self._get_trello_params()
        params["pos"] = "bottom"
        params["name"] = text
        r = requests.post(url, params=params, timeout=10)
        if r.status_code != 200:
            print(
                "ERROR: %s when attempting add to a trello checklist (HabiticaMapper) \n%s",
                r.status_code,
                r.content,
            )

            return
        self.dirty_cache = True
        return

    def delete_checklist_item(self, checklist_id, checklist_item_id):
        "delete a single item from an existing checklist"
        url = f"{BASE_URL}checklists/%s/checkItems/%s" % (
            checklist_id,
            checklist_item_id,
        )
        params = self._get_trello_params()
        r = requests.delete(url, params=params, timeout=10)
        if r.status_code != 200:
            _LO.error(
                "ERROR: %s, Couldn't delete trello checklist item %s ",
                r.status_code,
                checklist_item_id,
            )

        self.dirty_cache = True

    def _setCustomFieldValue(self, cardID, value, fieldID):
        url = f"{BASE_URL}card/%s/customField/%s/item" % (cardID, fieldID)
        data = json.dumps({"value": {"text": "%s" % (value)}})
        params = self._get_trello_params()
        headers = {"Content-type": "application/json"}
        r = requests.put(url=url, data=data, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            _LO.error(
                "Unexpected response code [%s], whilst updating card  %s's field ID %s",
                r.status_code,
                cardID,
                fieldID,
            )

            print(r.content)

    def archive_trello_card(self, trelloCardID):
        "archives an exisiting trello card"
        url = f"{BASE_URL}card/%s" % (trelloCardID)
        params = self._get_trello_params()
        params["closed"] = True
        r = requests.put(url, params=params, timeout=10)
        if r.status_code != 200:
            print(r)
            print(r.reason)
        self.dirty_cache = True

    def create_custom_field(self, field_name) -> str:
        "creates a custom field on the board, returns the ID for use."
        board_id = self.board_id
        url = f"{BASE_URL}customFields/"
        params = self._get_trello_params()
        data = {
            "idModel": board_id,
            "modelType": "board",
            "name": field_name,
            "type": "text",
            "pos": "bottom",
        }
        result = requests.post(url, data=data, params=params, timeout=10)
        if result.status_code != 200:
            _LO.warning("Creation of a custom field failed!")
            return ""
        try:
            new_field = json.loads(result.content)["id"]
            return new_field

        except json.JSONDecodeError as e:
            _LO.warning(
                "Couldn't parse JSON of new field? this shouldn't happen - %s", e
            )

        return ""

    def _get_trello_params(self):
        params = {"key": self.key, "token": self.token}
        return params

    def delete_trello_card(self, trelloCardID):
        "deletes an exisiting trello card"
        url = f"{BASE_URL}card/%s" % (trelloCardID)
        r = requests.delete(url, params=self._get_trello_params(), timeout=10)
        if r.status_code != 200:
            print(r)
            print(r.reason)
            return
        self.dirty_cache = True

    def fetch_checklist_content(self, checklist_id) -> list:
        "fetches the content of a checklist, returns a list of dicts"
        url = f"{BASE_URL}checklists/%s" % (checklist_id)
        r = self._request_and_validate(url)
        return r

    def _sort_trello_cards_list(self, array_of_cards: list) -> list:
        "Takes an arbitrary list of cards and sorts them by their position value if present"
        array_of_cards = sorted(array_of_cards, key=lambda card: card.get("pos", 0))

        return array_of_cards

    def _sort_trello_cards_dict(self, dict_of_cards: dict) -> dict:
        sorted_dict = {
            k: v
            for k, v in sorted(dict_of_cards.items(), key=lambda x: x[1].get("pos"))
        }
        # note for future C'tri reading this - the part that does the sorting is this:
        # key=lambda x:x[1].get("pos")
        # in this case, x is a tuple comprised of K and V
        # x[1] is the card - a dict, and x[0] is the id, a string.
        return sorted_dict

    def _populate_cache(self, array_of_cards: list) -> None:
        "takes a list of cards and puts them into the _cached_cards dict"
        for card in array_of_cards:
            card: dict
            if "id" not in card:
                _LO.warning("skipped adding a card to the cache, no id present")
                continue

            self._cached_cards[card.get("id")] = card

    def _try_update_cache(self, response_content) -> bool:
        "attempts to parse the raw response from update/create and turn it into a cached card. Returns True on success"

        try:
            response_content = response_content.decode()
        except (UnicodeDecodeError, AttributeError):
            pass

        if not isinstance(response_content, str):
            logger.error("error in _try_update_cache, supplied object not a string.")
            return False
        try:
            card = json.loads(response_content)
            card: dict
        except Exception as err:
            logger.error(
                "error in _try_update_cache, couldn't parse supplied object becase '%s'",
                err,
            )
            logger.debug("supplied object %s", response_content)
            return False

        self._cached_cards[card.get("id")] = card
        return True

    def _request_and_validate(self, url, headers=None, params=None, body=None, retry=0) -> dict:
        """internal method to make a GET request and return the parsed json response (either a dict of cards, or a dict of actions, or whatever is returned)

        arguments:
            `url` - the url to request, including the base url
            `headers` - any additional headers to send
            `params` - any additional params to send (the key and token are added automatically)
            `body` - any additional body to send

        returns:
            a dict of the parsed json response, or an empty dict on failure
        """
        if params is None:
            params = self._get_trello_params()
        else:
            params = {**params, **self._get_trello_params()}

        try:
            result = requests.get(
                url=url, headers=headers, data=body, params=params, timeout=10
            )
        except ConnectionError as e:
            _LO.error("Couldn't connect to %s - %s", url, e)
            return {}
        if result.status_code == 400:
            _LO.error("Invalid request to %s - %s", url, result.content)
            return {}
        if result.status_code == 401:
            _LO.error("Unrecognised token/key at  %s - %s", url, result.content)
            return {}
        elif result.status_code == 403:
            _LO.error("insufficient permissions %s - %s", url, result.content)
            return {}
        if result.status_code != 200:
            _LO.error(
                "Got an invalid response: %s - %s ", result.status_code, result.content
            )
            return {}
        if result.status_code == 429:
            _LO.warning("Rate limit, standing by for a moment")
            if retry >= 5:
                return {}

            retry += 1
            time.sleep (pow(retry,2)*1000)
            self._request_and_validate(self, url, headers=None, params=None, body=None, retry=0)

            # sleep for an increasing set of seconds
        try:
            parsed_content = json.loads(result.content)
            if "cards" in parsed_content:
                parsed_content = parsed_content["cards"]
            elif "actions" in parsed_content:
                parsed_content = parsed_content["actions"]
        except json.JSONDecodeError as e:
            _LO.error("Couldn't parse JSON from %s - %s", url, e)
            return {}
        return parsed_content

    # we haven't handled pagination yet - this was copied from the zendesk thing.
    def _request_and_validate_paginated(
        self,
        url,
        params=None,
        headers=None,
        body=None,
        page_limit=None,
        page_size_limit=None,
        since=None,
    ) -> list:
        params = {} if params is None else params
        params["limit"] = page_size_limit

        page_limit = 10 if page_limit is None else page_limit
        page_size_limit = 100 if page_size_limit is None else page_size_limit
        next_page = 1
        pages = []
        if since is not None:
            params["since"] = since
        while next_page is not None:
            r_url = f"{url}"
            try:
                resp = self._request_and_validate(r_url, headers, params, body)
            except Exception as e:
                _LO.error("Couldn't get page %s from %s- %s", next_page, url, e)
                break
            if resp in pages or len(resp) == 0:
                break
            pages.append(resp)

            # this is probably going to break at some point
            params["since"] = resp[0]["id"]
            # check if `resp` is already in `pages``

        flattened_list = []
        for page in pages:
            flattened_list.extend(page)
        return flattened_list
