import json
import requests


class bulbState():
    def __init__(self,active,brightness,hue,saturation) -> None:
        self.active = active
        self.brightness = brightness
        self.hue = hue
        self.saturation = saturation

     
    def fromApiObj(apiObj:dict):
        "initiate a bulbState object from a dict provided by the Bridge API"
        stateBlock = apiObj.get("state")
        if isinstance(stateBlock,dict):
            active = stateBlock.get("on")
            brightness = stateBlock.get("bri")
            hue = stateBlock.get("hue")
            saturation = stateBlock.get("sat")
            return bulbState(active,brightness,hue,saturation)

        
        return bulbState(None,None,None,None)

    def __str__(self) -> str:
        returnObj = {}
        if self.active is not None:
            returnObj["on"] = self.active
        if self.brightness is not None:
            returnObj["bri"] = self.brightness
        if self.hue is not None:
            returnObj["hue"] = self.hue
        if self.saturation is not None:
            returnObj["sat"] = self.saturation
        return json.dumps(returnObj)
        
    def __eq__(self, __o:object) -> bool:
        if not isinstance(__o,bulbState):
            return False
        
        if self.hue != __o.hue:
            return False
        if self.active != __o.active:
            return False
        if self.brightness != __o.brightness:
            return False 
        if self.saturation != __o.saturation:
            return False 
        return True
    
    def generateOFFbulbstate():
        return bulbState(False,None,None,None)

    
    def generateONbulbstate(): 
        return bulbState(True,None,None,None)
    
class hueBulb():
    def __init__(self,helper, apiObj:dict = None, apiObjStr:str = None) -> None:
        if apiObjStr is not None:
            apiObj = json.loads(apiObjStr)
        self.name = apiObj.get("name")
        self.id = int(apiObj.get("deviceIDonBridge"))
        self.type = apiObj.get("type")
        self._helper = helper
        self.cfg = helper._config
        state = apiObj.get("state",{})
        self.state = bulbState(state.get("on",False),state.get("bri",0),state.get("hue",0),state.get("sat",0))
        
        pass 

    def setNewState(self,newState:bulbState, force=False) -> bool:
        
        if not force:
            #check if current state = cached state
            #if cached state == current state, proceed. If not, return False
            currentState = self._helper.getDevice(self.id).state
            if currentState != self.state:
                print("Didn't match - returning")
                return False 
        
        url = "http://{host}/api/{username}/lights/{bulbID}/state".format(host=self._helper._config.bridgeIP,username=self._helper._config.bridgeUser, bulbID=self.id)
        data = str(newState)
        result = requests.put(url,data=data)
        if result:
            self.state = self._helper.getDevice(self.id).state
        return result

    def refreshCache(self):
        url = "http://{host}/api/{username}/lights/{bulbID}".format(host=self._helper._config.bridgeIP,username=self._helper._config.bridgeUser, bulbID=self.id)
        newBulbObj = json.loads(requests.get(url=url).content)
        currentState = bulbState.fromApiObj(newBulbObj)
        self.state = currentState
        
        pass 