# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

# downloaded from https://github.com/Azure/iot-central-firmware/tree/master/RaspberryPi

import time
import sys
import os
import grove_dht_pro_once  # Grove sensors stuff, file is located circa /home/pi/Dexter/GrovePi/Sofware/Python
import grovepi
from grove_rgb_lcd import * #LCD support
import iotc # installed using pip install iotc. Check link on the top of this file for instructions
from iotc import IOTConnectType, IOTLogLevel
from random import randint

# params from IoT Central --> go to device page, click in Connect on the top right corner, copy-paste these parameters
deviceId = "756353cd-dfdb-4a7f-8c30-038c7ae63ea7" 
scopeId = "0ne0004C2BE"
mkey = "PQxORiqcbvMm/A7u2jU1N2oAH5iLMFn+xOeIY1upkHI="
oldState = "NOMINAL"
newState = "NOMINAL"
vibration_threshold = 40

iotc = iotc.Device(scopeId, mkey, deviceId, IOTConnectType.IOTC_CONNECT_SYMM_KEY)
iotc.setLogLevel(IOTLogLevel.IOTC_LOGGING_API_ONLY)

gCanSend = False
gCounter = 0

def display_running_indicator(indicatorChar):

  indicatorText = indicatorChar
  counter = 0

  while counter <= 15:
    indicatorText = ' ' * counter
    indicatorText += indicatorChar
    setText(indicatorText)
    counter+=1
    time.sleep(0.1)
    

def display_status(text):
	
	try:
		setText(text) # Write to LCD display

	except:
		print("[display status] => Failed on something or other!")

def onconnect(info):
  global gCanSend
  display_status("Connecting...\n=> MS Azure")
  print("- [onconnect] => status:" + str(info.getStatusCode()))
  if info.getStatusCode() == 0:
     if iotc.isConnected():
       gCanSend = True

def onmessagesent(info):
  print("\t- [onmessagesent] => " + str(info.getPayload()))

def oncommand(info):
  print("- [oncommand] => " + info.getTag() + " => " + str(info.getPayload()))

def onsettingsupdated(info):
  print("- [onsettingsupdated] => " + info.getTag() + " => " + info.getPayload())

iotc.on("ConnectionStatus", onconnect)
iotc.on("MessageSent", onmessagesent)
iotc.on("Command", oncommand)
iotc.on("SettingsUpdated", onsettingsupdated)

iotc.connect()
try:
  gCounter = 0
  while iotc.isConnected():
    iotc.doNext() # do the async work needed to be done for MQTT
    if gCanSend == True:
          
      print("Getting telemetry...")

      # read vibration from the file, there's another process writing there. The other process is lauched at startup in /etc/init.d
      f = open("/ramdisk/vibration.value", "r")
      vibration = f.read()
      f.close()
      vibration = float(vibration)

      # if vibration is above threshold, set status to WARNING
      if (vibration > vibration_threshold):
        newState = "WARNING"
        if(newState != oldState):
          iotc.sendState("{ \"state\": \""+ newState + "\"}") #report status change only once
          print("Status changed to "+ newState)
          oldState ="WARNING"
        setRGB(178,34,34) # Set background color to red
      else:
        newState = "NOMINAL"
        if(newState != oldState):
          iotc.sendState("{ \"state\": \""+ newState + "\"}") #report status change only once
          print("Status changed to "+ newState)
          oldState ="NOMINAL"
        setRGB(0,128,64) # Set background color to light blue
      
    
        
      # read temperature and humidity from Grove lib
      temperature, humidity = grove_dht_pro_once.main()
      print("#" + str(gCounter) +" Sending telemetry...")
      
      iotc.sendTelemetry("{ \
        \"test\": " + str(0) + ", \
        \"temperature\": " + str(temperature) + ", \
        \"humidity\": " + str(humidity) + ", \
        \"vibration\": " + str(vibration) + "}")

      display_running_indicator("=")
      display_status("Connected=>Azure\n#"+str(gCounter)+" T:"+str(temperature)+"V:"+str(vibration))  
      gCounter += 1
      time.sleep(5) # each 5 seconds (instead of gCounter % 20 == 0 as the original script was doing) 
except KeyboardInterrupt: #When interruptedd interactively exit and display default message
  print('Interrupted by keyboard')
  display_status("Terminating..")
  time.sleep(15)
  ipv4_addr = os.popen('ip addr show wlan0 | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip()
  display_status(ipv4_addr + '\npi:arrowiot ')
  setRGB(0,255,0)
  try:
      sys.exit(0)
  except SystemExit:
      os._exit(0)