#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# Rotary encoder version with no LCD display for Retro Radio conversion
# $Id: retro_radio.py,v 1.28 2017/08/08 10:55:49 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# 
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc' 
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# 
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import RPi.GPIO as GPIO
import signal
import subprocess
import sys
import time
import string
import datetime
from time import strftime
import shutil
import atexit
import traceback

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from log_class import Log
from rotary_class import RotaryEncoder
from rotary_class_alternative import RotaryEncoderAlternative
from status_led_class import StatusLed
from menu_switch_class import MenuSwitch

# To use GPIO 14 and 15 (Serial RX/TX)
# Remove references to /dev/ttyAMA0 from /boot/cmdline.txt and /etc/inittab 

UP = 0
DOWN = 1

GREEN_LED = 27	# Normal operation
BLUE_LED  = 22	# Initialisation or loading operation
RED_LED   = 23	# Error occured

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile
PlaylistsDirectory = "/var/lib/mpd/playlists/"

log = Log()
radio = Radio()
statusLed = None
volumeknob = None
tunerknob = None
menu_switch = None
menu_switch_value = 0

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global log
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	radio.exit()

# Menu switch event handler
def menu_swich_event(switch):
		global menu_switch_value
		global menu_switch
		global log,radio
		time.sleep(0.1)
		value = menu_switch.get()
		if value != menu_switch_value:
			message = "Menu switch "  + str(switch) + " value " + str(value)
			log.message(message , log.INFO)
			menu_switch_value = value
		return

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile
		global menu_switch_value
		global volumeknob,tunerknob,statusLed,menu_switch

		menu_settle = 5 	# Allow menu switch to settle

		log.init('radio')
		signal.signal(signal.SIGTERM,signalHandler)

		# Configure RGB status LED
		rgb_red = radio.getRgbLed('rgb_red')
		rgb_green = radio.getRgbLed('rgb_green')
		rgb_blue = radio.getRgbLed('rgb_blue')
		statusLed = StatusLed(rgb_red,rgb_green,rgb_blue)
		statusLed.set(StatusLed.BUSY)

		progcall = str(sys.argv)

		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I')

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())

		# Wait for the IP network
		ipaddr = ""
		waiting4network = True
		count = 10
		while waiting4network:
			ipaddr = exec_cmd('hostname -I')
			time.sleep(1)
			count -= 1
			if (count < 0) or (len(ipaddr) > 1):
				waiting4network = False

		if len(ipaddr) < 1:
			log.message("No IP network", log.INFO)
			statusLed.set(StatusLed.ERROR)
			time.sleep(1)
		else:
			log.message("IP " + ipaddr, log.INFO)

		time.sleep(2)
		log.message("Starting MPD", log.INFO)
		radio.start()
		log.message("MPD started", log.INFO)

		radio.setLastMode(radio.MODE_OPTIONS)
		radio.setLastOption(radio.RELOADLIB)
		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		time.sleep(1)
		 	
		# Auto-load music library if no Internet
		if len(ipaddr) < 1 and radio.autoload():
			log.message("Loading music library",log.INFO)
			radio.setSource(radio.PLAYER)

		# Load radio
		reload(radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

		# Get rotary switches configuration
		up_switch = radio.getSwitchGpio("up_switch")
		down_switch = radio.getSwitchGpio("down_switch")
		left_switch = radio.getSwitchGpio("left_switch")
		right_switch = radio.getSwitchGpio("right_switch")
		menu_switch = radio.getSwitchGpio("menu_switch")
		mute_switch = radio.getSwitchGpio("mute_switch")

		boardrevision = radio.getBoardRevision()

		if radio.getRotaryClass() is radio.ROTARY_STANDARD:
			boardrevision = radio.getBoardRevision()
			volumeknob = RotaryEncoder(left_switch,right_switch,mute_switch,volume_event,boardrevision)
			tunerknob = RotaryEncoder(up_switch,down_switch,menu_switch,tuner_event,boardrevision)
		elif radio.getRotaryClass() is radio.ROTARY_ALTERNATIVE:
			volumeknob = RotaryEncoderAlternative(left_switch,right_switch,mute_switch,volume_event,boardrevision)
			tunerknob = RotaryEncoderAlternative(up_switch,down_switch,menu_switch,tuner_event,boardrevision)

		# Configure rotary switch (not rotary encoder)
		switch1 = radio.getMenuSwitch('menu_switch_value_1')
		switch2 = radio.getMenuSwitch('menu_switch_value_2')
		switch4 = radio.getMenuSwitch('menu_switch_value_4')
		menu_switch = MenuSwitch(switch1,switch2,switch4,menu_swich_event)

		log.message("Running" , log.INFO)
		statusLed.set(StatusLed.NORMAL)

		# Main processing loop
		count = 0 
		while True:
			display_mode = radio.getDisplayMode()
			if not radio.getReload():
				if display_mode is radio.MODE_SEARCH:
					statusLed.set(StatusLed.SELECT)
				else:
					statusLed.set(StatusLed.NORMAL)
			switch = radio.getSwitch()
			if switch > 0:
				get_switch_states(radio,volumeknob,tunerknob)
				radio.setSwitch(0)

			if menu_switch_value > 0:
				menu_settle -=  1
				if menu_settle < 0:
					setMenu(radio,menu_switch_value)
					menu_settle = 5
				else:
					time.sleep(0.2)

			dateFormat = radio.getDateFormat()
			todaysdate = strftime(dateFormat)

			# Check for IP address
			ipaddr = exec_cmd('hostname -I')
			if len(ipaddr) < 1 and radio.getSource() != radio.PLAYER:
				statusLed.set(StatusLed.ERROR)

			# Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				while True:
					# Not an error just shutting down
					statusLed.set(StatusLed.ERROR)
					radio.execCommand("shutdown -h now")
					time.sleep(1)

			elif display_mode == radio.MODE_TIME:

				if radio.getReload():
					log.message("Reload ", log.DEBUG)
					reload(radio)
					radio.setReload(False)

			# Check state (pause or play)
			checkState(radio)


			if radio.volumeChanged():
				time.sleep(0.1)

			time.sleep(0.1)

	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "radiod status: not running"
	    		log.message(message, log.INFO)
			print message 
		else:
			message = "radiod running pid " + str(pid)
	    		log.message(message, log.INFO)
			print message 
		return

# End of class overrides

# Call back routine for the volume control knob
def volume_event(event):
	global radio
	global volumeknob
	switch = 0

	# Get rotary switches configuration
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")
	mute_switch = radio.getSwitchGpio("mute_switch")

	ButtonNotPressed = volumeknob.getSwitchState(mute_switch)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = right_switch
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = left_switch

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = mute_switch

	radio.setSwitch(switch)
	return

# Call back routine for the tuner control knob
def tuner_event(event):
	global radio
	global tunerknob
	switch = 0

	# Get rotary switches configuration
	up_switch = radio.getSwitchGpio("up_switch")
	down_switch = radio.getSwitchGpio("down_switch")
	menu_switch = radio.getSwitchGpio("menu_switch")

	ButtonNotPressed = tunerknob.getSwitchState(menu_switch)

	# Suppress events if tuner button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = up_switch
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = radio.getSwitchGpio("down_switch")

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = menu_switch

	radio.setSwitch(switch)
	return

# Check switch states
def get_switch_states(radio,volumeknob,tunerknob):
	switch = radio.getSwitch()
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()	
	events = radio.getEvents()
	option = radio.getOption()


	# Get rotary switches configuration
	up_switch = radio.getSwitchGpio("up_switch")
	down_switch = radio.getSwitchGpio("down_switch")
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")
	menu_switch = radio.getSwitchGpio("menu_switch")
	mute_switch = radio.getSwitchGpio("mute_switch")

	if switch == menu_switch:
		log.message("MENU switch mode=" + str(display_mode), log.DEBUG)

		# Exit Airplay if menu button pressed
		if input_source == radio.AIRPLAY and not radio.getReload():
			log.message("Exiting Airplay", log.DEBUG)
			radio.setSource(radio.RADIO)
			display_mode = radio.MODE_TIME
			radio.setReload(True)
			radio.getEvents()	# Clear any events
		else:
			radio.unmute()
			display_mode = display_mode + 1

		# This radio version doesn't use RSS or IP information display
		if display_mode >= radio.MODE_RSS:
			display_mode = radio.MODE_TIME

		# Set the new mode
		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = tunerknob.getSwitchState(menu_switch)
		count = 15
		while MenuSwitch == 0:
			time.sleep(0.2)
			MenuSwitch = tunerknob.getSwitchState(menu_switch)
			count = count - 1
			if count < 0:
				statusLed.set(StatusLed.ERROR)
				log.message("Shutdown", log.DEBUG)
				MenuSwitch = 1
				radio.setDisplayMode(radio.MODE_SHUTDOWN)

		if radio.getUpdateLibrary():
			update_library(radio)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.getReload(): 
			source = radio.getSource()
			reload(radio)
			radio.setReload(False)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.optionChanged():
			log.message("optionChanged", log.DEBUG)
			if radio.alarmActive() and not radio.getTimer() \
					and (option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS):
				radio.setDisplayMode(radio.MODE_SLEEP)
				radio.mute()
			else:
				radio.setDisplayMode(radio.MODE_TIME)

			radio.optionChangedFalse()

		elif radio.loadNew():
			log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
			radio.playNew(radio.getSearchIndex())
			radio.setDisplayMode(radio.MODE_TIME)

		time.sleep(0.2)

	elif switch == up_switch:
		if  display_mode != radio.MODE_SLEEP:
			log.message("UP switch display_mode " + str(display_mode), log.DEBUG)
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.cycleSource(UP)
				radio.setReload(True)
				time.sleep(0.2)
				radio.getEvents()	# Clear any events

			elif display_mode == radio.MODE_SEARCH:
				statusLed.set(StatusLed.BUSY)
				radio.getNext(UP)

			elif display_mode == radio.MODE_OPTIONS:
				radio.cycleOptions(UP)

			else:
				statusLed.set(StatusLed.BUSY)
				radio.channelUp()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)


	elif switch == down_switch:
		log.message("DOWN switch display_mode " + str(display_mode), log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.cycleSource(DOWN)
				radio.setReload(True)
				time.sleep(0.2)
				radio.getEvents()	# Clear any events

			elif display_mode == radio.MODE_SEARCH:
				statusLed.set(StatusLed.BUSY)
				radio.getNext(DOWN)

			elif display_mode == radio.MODE_OPTIONS:
				radio.cycleOptions(DOWN)

			else:
				statusLed.set(StatusLed.BUSY)
				radio.channelDown()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)

	elif switch == left_switch:
		log.message("LEFT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				#toggle_option(radio,DOWN)
				radio.changeOption(DOWN)

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				statusLed.set(StatusLed.BUSY)
				radio.findNextArtist(DOWN)

			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
				statusLed.set(StatusLed.BUSY)
				if events > 1:
					volAdjust = events/2
				else:
					volAdjust = events

				if radio.muted():
					radio.unmute()
				volume = radio.getVolume()
				while volAdjust > 0:	
					volume -=  1
					if volume < 0:
						volume = 0
					if input_source == radio.AIRPLAY:
						radio.decreaseMixerVolume()
                                        else:
						radio.setVolume(volume)
					volAdjust -= 1
				statusLed.set(StatusLed.NORMAL)

	elif switch == right_switch:
		log.message("RIGHT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				radio.changeOption(UP)

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				statusLed.set(StatusLed.BUSY)
				radio.findNextArtist(UP)
			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
				statusLed.set(StatusLed.BUSY)
				if events > 1:
					volAdjust = events/2
				else:
					volAdjust = events
				if radio.muted():
					radio.unmute()

				volume = radio.getVolume()
				range = radio.getVolumeRange()

				while volAdjust > 0:	
					volume += 1
					if volume > range:
						volume = range
					if input_source == radio.AIRPLAY:
						radio.increaseMixerVolume()
					else:
						radio.setVolume(volume)
					volAdjust -= 1
				statusLed.set(StatusLed.NORMAL)

	elif switch == mute_switch:
		log.message("MUTE switch" ,log.DEBUG)

		if  display_mode != radio.MODE_SLEEP:
			# If mute button held in for 2 seconds then mute otherwise speak information
			if radio.speechEnabled() and not radio.muted():
				log.message("Speech enabled" ,log.DEBUG)
				MuteSwitch = volumeknob.getSwitchState(mute_switch)
				log.message("Mute switch state=" + str(MuteSwitch), log.DEBUG)
				count = 5
				while MuteSwitch == 0:
					time.sleep(0.2)
					MuteSwitch = volumeknob.getSwitchState(mute_switch)
					count = count - 1
					if count < 0:
						log.message("Mute", log.DEBUG)
						MuteSwitch = 1
						radio.mute()
				if not radio.muted():
					radio.speakInformation()
			else:

				if radio.muted():
					radio.unmute()
				else:
					radio.mute()
					time.sleep(2)
					radio.getEvents()	# Clear any events

	# Reset all rotary encoder events to zero
	radio.resetEvents()
	radio.setSwitch(0)
	return 

# Update music library
def update_library(radio):
	log.message("Updating library", log.INFO)
	radio.updateLibrary()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(radio):
	radio.unmountAll()
	source = radio.getSource()
	log.message("Reload " + str(source), log.DEBUG)

	if source == radio.RADIO:
		dirList=os.listdir(PlaylistsDirectory)
		for fname in dirList:
			if os.path.isfile(fname):
				continue
			log.message("Loading " + fname, log.DEBUG)
			time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		radio.loadMedia()
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			update_library(radio)

        elif source == radio.AIRPLAY:
                radio.startAirplay()
	return


# Get currently playing station or track number from MPC
def get_current_id():
	current_id = 1
	status = radio.execMpcCommand("status | grep \"\[\" ")
	if len(status) > 1:
		x = status.index('#')+1
		y = status.index('/')
		current_id = int(status[x:y])
	exec_cmd ("echo " + str(current_id) + " > " + CurrentFile)
	return current_id

# Get the last ID stored in /var/lib/radiod
def get_stored_id(current_file):
	current_id = 5
	if os.path.isfile(current_file):
		current_id = int(exec_cmd("cat " + current_file) )
	return current_id

# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# Get list of tracks or stations
def get_mpc_list(cmd):
	list = []
	line = ""
	p = os.popen("/usr/bin/mpc " + cmd)
	while True:
		line =  p.readline().strip('\n')
		if line.__len__() < 1:
			break
		list.append(line)

	return list

def unmuteRadio(radio):
	radio.unmute()
	return

# Set the display state from the menu switch
def setMenu(radio,value):
	global log
	global menu_switch_value
	log.message("setMenu " + str(value), log.DEBUG)

	if radio.getDisplayMode != radio.MODE_TIME:
		radio.setDisplayMode(radio.MODE_TIME)

	source = radio.getSource()

	if statusLed.get() is StatusLed.SELECT:
			statusLed.set(StatusLed.NORMAL)
	if value <= 1:
		check4new(radio)
		if source is radio.PLAYER:
			statusLed.set(StatusLed.BUSY)
			radio.setSource(radio.RADIO)
			radio.setReload(True)

	elif value == 2:
		statusLed.set(StatusLed.BUSY)
		radio.speakInformation()

	elif value == 3:
		statusLed.set(StatusLed.SELECT)
		radio.setDisplayMode(radio.MODE_SEARCH)

	elif value == 4:
		check4new(radio)
		if source is radio.RADIO:
			radio.setSource(radio.PLAYER)
			radio.setReload(True)
			statusLed.set(StatusLed.BUSY)
			check4new(radio)

	elif value == 5:
		radio.setSource(radio.PLAYER)
		statusLed.set(StatusLed.BUSY)
		update_library(radio)
		statusLed.set(StatusLed.NORMAL)

	elif value == 6:
		radio.setSource(radio.AIRPLAY)
		statusLed.set(StatusLed.BUSY)
		radio.startAirplay()
		statusLed.set(StatusLed.NORMAL)

	menu_switch_value = 0
	return

# Check if load new required
def check4new(radio):
	if radio.loadNew():
		log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
		radio.playNew(radio.getSearchIndex())
	return

# Check state (play or pause)
# Returns paused True if paused
def checkState(radio):
	paused = False
	display_mode = radio.getDisplayMode()
	state = radio.getState()
	radio.getVolume()

	if state == 'pause':
		paused = True
		if not radio.muted():
			if radio.alarmActive() and not radio.getTimer():
				radio.setDisplayMode(radio.MODE_SLEEP)
			radio.mute()
	elif state == 'play':
		if radio.muted():
			unmuteRadio(radio)
			radio.setDisplayMode(radio.MODE_TIME)
	return paused

### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/radiod.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			os.system("service mpd stop")
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'version' == sys.argv[1]:
			print "Version " + radio.getVersion()
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 

