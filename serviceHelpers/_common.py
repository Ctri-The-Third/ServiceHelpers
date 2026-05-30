import requests 
import json 
import logging 
import time 
_LO = logging.getLogger("common-methods")
_LO.setLevel(logging.WARN)

def _request_and_validate( url, method, headers=None, params=None, body=None, retry=0, ) -> ResponseBlock:
        """internal method to make a GET request and return the parsed json response (either a dict of cards, or a dict of actions, or whatever is returned)

        arguments:
            `url` - the url to request, including the base url
            `headers` - any additional headers to send
            `params` - any additional params to send (the key and token are added automatically)
            `body` - any additional body to send

        returns:
            a dict of the parsed json response, or an empty dict on failure
        """

        try:
            result = method(
                url=url, headers=headers, data=body, params=params, timeout=10
            )
        except ConnectionError as e:
            response = ResponseBlock()
            response.error = f"Couldn't connect to {url} - {e}"

            _LO.error("Couldn't connect to %s - %s", url, e)
            return response
        if result.status_code == 400:
            response = ResponseBlock(result)
            response.error = f"Invalid request to {url} - {result.content}" 
            _LO.error("Invalid request to %s - %s", url, result.content)
            return response
        if result.status_code == 401:
            response = ResponseBlock(result)
            response.error = f"Invalid request to {url} - {result.content}" 
            _LO.error("Unrecognised token/key at  %s - %s", url, result.content)
            return response
        elif result.status_code == 403:
            response = ResponseBlock(result)
            response.error = f"Invalid request to {url} - {result.content}" 
            _LO.error("insufficient permissions %s - %s", url, result.content)
            return response
        if result.status_code != 200:
            response = ResponseBlock(result)
            response.error = f"Invalid request to {url} - {result.content}" 
            _LO.error(
                "Got an invalid response: %s - %s ", result.status_code, result.content
            )
            return response
        if result.status_code == 429:
            _LO.warning("Rate limit, standing by for a moment")
            if retry >= 5:
                response = ResponseBlock(result)
                return response

            retry += 1
            time.sleep (pow(retry,2)*1000)
            response =_request_and_validate(url, method, headers=None, params=None, body=None, retry=0)

            # sleep for an increasing set of seconds
        response = ResponseBlock()
        parsed_content = None 
        try:
            response = ResponseBlock(result)
            if "cards" in response.content:
                parsed_content = response.content["cards"]
            elif "actions" in response.content:
                parsed_content = response.content["actions"]
        except json.JSONDecodeError as e:
            _LO.error("Couldn't parse JSON from %s - %s", url, e)
            return {"error":"couldn't parse JSON", "ok":False}
        if isinstance(parsed_content,list):
            parsed_content = { "results": parsed_content}
        
        if parsed_content:
            response.content = parsed_content

        return response

def _get_and_validate(self, url,  headers=None, params=None, body=None, retry=0, ) -> ResponseBlock:
    return  self.__request_and_validate(url, requests.get, headers=headers, params=params, body=body, retry=0)

def _post_and_validate(self, url,  headers=None, params=None, body=None, retry=0, ) -> ResponseBlock:
    return self.__request_and_validate(url, requests.post, headers, params, body, retry)

def _put_and_validate(self, url,  headers=None, params=None, body=None, retry=0, ) -> ResponseBlock:
    return self.__request_and_validate(url, requests.put, headers, params, body, retry)

def _delete_and_validate(self, url,  headers=None, params=None, body=None, retry=0, ) -> ResponseBlock:
    return self.__request_and_validate( url, requests.delete, headers, params, body, retry)




class ResponseBlock():

    def __init__(self, response_object:requests.Response = None ):

        if response_object and isinstance(response_object, requests.Response):
            self.okay = response_object.status_code in (200,201)
            self.error = response_object.status_code
            try:
                self.content = json.loads(response_object.content)
                if isinstance(self.content, list):
                    self.content = {"results" : self.content}
            except json.JSONDecodeError as err:
                self.error = err
                self.okay = False 
                self.content = {}
            pass
    
        else: 
            self.okay = False 
            self.error = "Unknown"
            self.content = {}


    def __bool__(self):
        return self.okay
    


