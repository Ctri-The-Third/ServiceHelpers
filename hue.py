import logging
import json

import requests
import time
import threading

from datetime import datetime, timedelta

from models import hueBulb 


class huehelper():
    
    def __init__(self,bridge_ip,bridge_user,deviceIdentifier = None) -> None:
        
        
        self.bridge_ip = bridge_ip
        self.bridge_user = bridge_user
        self.authenticate()
        self.getDevices()
        self.logger = logging.getLogger("HueHelper")
        pass 

    

    def authenticate(self) -> None:
        self.is_ready = False
        if self.bridge_ip is None:
            self._getIP()
        if self.bridge_user is None:
            self._linkButtonLoop()
        self.is_ready = True
        return 


    def getDevices(self) -> None:
        if not self.is_ready:
            return {}
        
        url = f"http://{self.bridge_ip}/api/{self.bridge_user}/lights"
        lights = json.loads(requests.get(url=url).content)
        self.devices = {} 
        for lightKey in lights:
            lights[lightKey]["deviceIDonBridge"] = lightKey
            newBulb = hueBulb.hueBulb(self,apiObj=lights[lightKey])
            self.devices[newBulb.name] = newBulb
        return self.devices

    def getDevice(self,bulbID) -> None:
        url = f"http://{self.bridge_ip}/api/{self.bridge_user}/lights/{bulbID}"
        response = json.loads(requests.get(url=url).content)
        response["deviceIDonBridge"] = bulbID
        newBulb = hueBulb.hueBulb(self,apiObj=response)

        self.devices[newBulb.name] = newBulb
        return newBulb

    def pulseLights(self,hue,sat,bri = None, rate = 0.5, duration = 0.1 ):
        #pulse only the config named lights a fixed colour at a fixed rate for a specific duration in seconds
        cachedSettings = {}
        pulseStates = {}
        redstate = hueBulb.bulbState.generateONbulbstate()
        redstate.hue = hue
        redstate.saturation = sat
        endtime = datetime.now() + timedelta(seconds=duration)
        if bri != None:
            redstate.brightness = bri 
    
        for deviceName in self._config.HueDevicesToFlash:
            device:hueBulb = self.devices.get(deviceName)
            if device is None:
                pass 
            else:
                cachedSettings[device.name] = self.getDevice(device.id).state #47104-blue #25600-green
                pulseStates[device.name]= []
                pulseStates[device.name].append(redstate)
                pulseStates[device.name].append(cachedSettings[device.name])
                t = threading.Thread(target=huehelper._pulseLight,args=(device,endtime,rate,pulseStates[device.name],True))
                t.start()
        


        time.sleep(duration+rate+rate)
        print("Resetting devices...")
        for deviceName in self._config.HueDevicesToFlash:
            device = self.devices.get(deviceName)
            cachedState = cachedSettings.get(deviceName)
            if device is None or cachedState is None:
                pass 
            else:
                print("%s\t%s"%(device.name,cachedState))

                device.setNewState(cachedState)

    def _pulseLight(device,endtime,rate,pulseStates,force):
        counter = 0
        while datetime.now() < endtime:
            print("%s-%s\t%s"%(counter,device.name,pulseStates[counter%len(pulseStates)]))
            success = device.setNewState(pulseStates[counter%len(pulseStates)],force)
            if not success:
                print("Something messed with the bulb since we last touched it. Aborting")
                break
                    
            counter += 1 
            time.sleep(rate)
    

    def _getIP(self) -> None:
        if self._config.bridgeIP is None or self._config.bridgeIP == "":
            result = json.loads(requests.get("https://discovery.meethue.com/").content)
            if len(result) == 0:
                logging.warning("Couldn't discover Hue IP address")                
            if len(result) > 1:
                logging.warning("More than one Bridge present, selecting first")
            try:
                self._config.bridgeIP = result[0]["internalipaddress"]
            except:
                logging.error("Couldn't parse bridge IP result from discovery")
            

    def _linkButtonLoop(self) -> str:
        print("Press link button")
        logging.info("Need to press the link button to continue")
        url = "http://{host}/api".format(host=self._config.bridgeIP)
        body = json.dumps({"devicetype":"tmp-lightbulbs#noUniqueID"})
        isValid = False 
        status_code = 200 
        while not isValid or status_code != 200 :
            responseObj = requests.post(url=url,data=body)
            status_code = responseObj.status_code
            responses = json.loads(responseObj.content)
            for response in responses:
                if "success" not in response:
                    
                    time.sleep(.2)
                else:
                    success = response["success"]
                    if "username" in success:
                        self.bridge_user = success["username"]
                        logging.info("Successfully got a username from the Hue Bridge")
                        isValid = True 
        

