#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
# Rotary encoder version
# $Id: rradio8x2.py,v 1.5 2016/11/13 11:47:56 bob Exp $
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
from lcd_class import Lcd
from log_class import Log
from rss_class import Rss
from rotary_class import RotaryEncoder
from rotary_class_alternative import RotaryEncoderAlternative

# To use GPIO 14 and 15 (Serial RX/TX)
# Remove references to /dev/ttyAMA0 from /boot/cmdline.txt and /etc/inittab 

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile
PlaylistsDirectory = "/var/lib/mpd/playlists/"

log = Log()
radio = Radio()
lcd = Lcd()
rss = Rss()

volumeknob = None
tunerknob = None

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global lcd
	global log
	radio.execCommand("umount /media > /dev/null 2>&1")
	radio.execCommand("umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	lcd.line1("Radio")
	lcd.line2("stopped")
	GPIO.cleanup()
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile
		global volumeknob,tunerknob
		log.init('radio')
		signal.signal(signal.SIGTERM,signalHandler)

		progcall = str(sys.argv)

		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)

		boardrevision = radio.getBoardRevision()
		lcd.init(boardrevision)
		lcd.setWidth(8)

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I')

		# Display daemon pid on the LCD
		message = "PID " + str(os.getpid())
		lcd.line1(message)

		# Wait for the IP network
		ipaddr = ""
		waiting4network = True
		count = 10
		while waiting4network:
			lcd.line2("Connect")
			ipaddr = exec_cmd('hostname -I')
			time.sleep(1)
			count -= 1
			if (count < 0) or (len(ipaddr) > 1):
				waiting4network = False

		if len(ipaddr) < 1:
			lcd.scroll1("No IP network")
		else:
			lcd.scroll2("IP " + ipaddr, no_interrupt)

		time.sleep(2)
		log.message("Starting MPD", log.INFO)
		lcd.line1("Starting")
		lcd.line2("MPD")
		radio.start()
		log.message("MPD started", log.INFO)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line1("Ver "+ radio.getVersion())
		lcd.scroll2(mpd_version,no_interrupt)
		time.sleep(1)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

		# Get switches configuration
		up_switch = radio.getSwitchGpio("up_switch")
		down_switch = radio.getSwitchGpio("down_switch")
		left_switch = radio.getSwitchGpio("left_switch")
		right_switch = radio.getSwitchGpio("right_switch")
		menu_switch = radio.getSwitchGpio("menu_switch")
		mute_switch = radio.getSwitchGpio("mute_switch")

		if radio.getRotaryClass() is radio.ROTARY_STANDARD:
			volumeknob = RotaryEncoder(left_switch,right_switch,mute_switch,volume_event,boardrevision)
			tunerknob = RotaryEncoder(up_switch,down_switch,menu_switch,tuner_event,boardrevision)
		elif radio.getRotaryClass() is radio.ROTARY_ALTERNATIVE:
			volumeknob = RotaryEncoderAlternative(left_switch,right_switch,mute_switch,volume_event,boardrevision)
			tunerknob = RotaryEncoderAlternative(up_switch,down_switch,menu_switch,tuner_event,boardrevision)

		log.message("Running" , log.INFO)

		# Main processing loop
		count = 0 
		while True:
			switch = radio.getSwitch()
			if switch > 0:
				get_switch_states(lcd,radio,rss,volumeknob,tunerknob)
				radio.setSwitch(0)

			display_mode = radio.getDisplayMode()
			lcd.setScrollSpeed(0.3) # Scroll speed normal

			ipaddr = exec_cmd('hostname -I')

		       # Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			if len(ipaddr) < 1 and radio.getSource() != radio.PLAYER:
				lcd.line2("No IP")
	
			elif display_mode == radio.MODE_TIME:

                                if radio.getReload():
                                        log.message("Reload ", log.DEBUG)
                                        reload(lcd,radio)
                                        radio.setReload(False)

				displayTime(lcd,radio)
				if radio.muted():
					msg = "Muted"
					if radio.getStreaming():
						msg = msg + ' *'
					lcd.line2(msg)
				else:
					display_current(lcd,radio)

			elif display_mode == radio.MODE_SEARCH:
				display_search(lcd,radio)

			elif display_mode == radio.MODE_SOURCE:
				display_source_select(lcd,radio)

			elif display_mode == radio.MODE_OPTIONS:
				display_options(lcd,radio)

			elif display_mode == radio.MODE_IP:
				lcd.line2("Ver " + radio.getVersion())
				if len(ipaddr) < 1:
					lcd.scroll1("No IP network", interrupt)
				else:
					lcd.scroll1("IP " + ipaddr, interrupt)

			elif display_mode == radio.MODE_RSS:
				displayTime(lcd,radio)
				display_rss(lcd,rss)

			elif display_mode == radio.MODE_SLEEP:
				displayTime(lcd,radio)
				display_sleep(lcd,radio)

			# Timer function
			checkTimer(radio)

			# Check state (pause or play)
			checkState(radio)

			# Alarm wakeup function
			if display_mode == radio.MODE_SLEEP and radio.alarmFired():
				log.message("Alarm fired", log.INFO)
				unmuteRadio(lcd,radio)
				displayWakeUpMessage(lcd)
				radio.setDisplayMode(radio.MODE_TIME)

			if radio.volumeChanged():
				displayVolume(lcd,radio)


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

# Check Timer fired
def checkTimer(radio):
	interrupt = False
	if radio.fireTimer():
		log.message("Timer fired", log.INFO)
		radio.mute()
		radio.setDisplayMode(radio.MODE_SLEEP)
		interrupt = True
	return interrupt

# Interrupt scrolling LCD routine
def interrupt():
	global lcd
	global radio
	global volumeknob
	global tunerknob
	global rss
	interrupt = False
	switch = radio.getSwitch()
	if switch > 0:
		interrupt = get_switch_states(lcd,radio,rss,volumeknob,tunerknob)

	# Rapid display of timer
	if radio.getTimer() and not interrupt:
		displayTime(lcd,radio)
		interrupt = checkTimer(radio)

	if radio.volumeChanged():
		displayVolume(lcd,radio)

	if not interrupt:
		interrupt = checkState(radio) or radio.getInterrupt()

	return interrupt

def no_interrupt():
	return False

# Call back routine for the volume control knob
def volume_event(event):
	global radio
	global volumeknob
	switch = 0

	mute_switch = radio.getSwitchGpio("mute_switch")
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")

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
def get_switch_states(lcd,radio,rss,volumeknob,tunerknob):
	interrupt = False	# Interrupt display
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
		radio.unmute()
		display_mode = display_mode + 1

		# Skip RSS mode if not available
		if display_mode == radio.MODE_RSS and not radio.alarmActive():
			if not rss.isAvailable():
				display_mode = display_mode + 1
			else:
				lcd.line2("Getting RSS feed")

		if display_mode > radio.MODE_LAST:
			boardrevision = radio.getBoardRevision()
			lcd.init(boardrevision) # Recover corrupted dosplay
			display_mode = radio.MODE_TIME

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = tunerknob.getSwitchState(menu_switch)
		log.message("switch state=" + str(MenuSwitch), log.DEBUG)
		count = 15
		while MenuSwitch == 0:
			time.sleep(0.2)
			MenuSwitch = tunerknob.getSwitchState(menu_switch)
			count = count - 1
			if count < 0:
				log.message("Shutdown", log.DEBUG)
				MenuSwitch = 1
				radio.setDisplayMode(radio.MODE_SHUTDOWN)

		if radio.getUpdateLibrary():
			update_library(lcd,radio)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.getReload(): 
			source = radio.getSource()
			log.message("Reload " + str(source), log.INFO)
			lcd.line2("Reloading ")
			reload(lcd,radio)
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
		interrupt = True

	elif switch == up_switch:
		if  display_mode != radio.MODE_SLEEP:
			log.message("UP switch display_mode " + str(display_mode), log.DEBUG)
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)
				time.sleep(0.2)
				radio.getEvents()	# Clear any events

			elif display_mode == radio.MODE_SEARCH:
				radio.getNext(UP)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,UP)

			else:
				radio.channelUp()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)

			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == down_switch:
		log.message("DOWN switch display_mode " + str(display_mode), log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)
				time.sleep(0.2)
				radio.getEvents()	# Clear any events

			elif display_mode == radio.MODE_SEARCH:
				radio.getNext(DOWN)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,DOWN)

			else:
				radio.channelDown()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)
			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == left_switch:
		log.message("LEFT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,DOWN)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(DOWN)
				interrupt = True

			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
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
					radio.setVolume(volume)
					displayVolume(lcd,radio)
					volAdjust -= 1
		else:
			DisplayExitMessage(lcd)

	elif switch == right_switch:
		log.message("RIGHT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(UP)
				interrupt = True
			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
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
					radio.setVolume(volume)
					displayVolume(lcd,radio)
					volAdjust -= 1
		else:
			DisplayExitMessage(lcd)

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
						displayVolume(lcd,radio)
						interrupt = True
				if not radio.muted():
					radio.speakInformation()
			else:

				if radio.muted():
					radio.unmute()
					displayVolume(lcd,radio)
					time.sleep(1)
				else:
					radio.mute()
					lcd.line2("Mute")
					time.sleep(2)
				interrupt = True
		else:
			DisplayExitMessage(lcd)


	# Reset all rotary encoder events to zero
	radio.resetEvents()
	radio.setSwitch(0)
	return interrupt

# Cycle through the options
# Only display reload the library if in PLAYER mode
def cycle_options(radio,direction):
	log.message("cycle_options " + str(direction) , log.DEBUG)

	option = radio.getOption()

	if direction == UP:
		option += 1
	else:
		option -= 1

	# Don;t display reload if not player mode
	source = radio.getSource()
	if option == radio.RELOADLIB:
		if source != radio.PLAYER:
			if direction == UP:
				option = option+1
			else:
				option = option-1

	if option == radio.STREAMING:
		if not radio.streamingAvailable():
			if direction == UP:
				option = option+1
			else:
				option = option-1

	if option > radio.OPTION_LAST:
		option = radio.RANDOM
	elif option < 0:
		if source == radio.PLAYER:
			option = radio.OPTION_LAST
		else:
			option = radio.OPTION_LAST-1

	radio.setOption(option)
	radio.optionChangedTrue()
	return

# Toggle random mode
def toggle_option(radio,lcd,direction):
	option = radio.getOption() 
	log.message("toggle_option option="+ str(option), log.DEBUG)

	# Get rotary switches configuration
	up_switch = radio.getSwitchGpio("up_switch")
	down_switch = radio.getSwitchGpio("down_switch")
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")
	menu_switch = radio.getSwitchGpio("menu_switch")
	mute_switch = radio.getSwitchGpio("mute_switch")

	events = radio.getEvents()

	if option == radio.RANDOM:
		if radio.getRandom():
			radio.randomOff()
		else:
			radio.randomOn()

	elif option == radio.CONSUME:
		if radio.getSource() == radio.PLAYER:
			if radio.getConsume():
				radio.consumeOff()
			else:
				radio.consumeOn()
		else:
			lcd.line2("Not allowed")
			time.sleep(2)

	elif option == radio.REPEAT:
		if radio.getRepeat():
			radio.repeatOff()
		else:
			radio.repeatOn()

	elif option == radio.TIMER:
		if radio.getTimer():
			if direction == UP:
				radio.incrementTimer(events/2)
				lcd.line2("Timer " + radio.getTimerString())
			else:
				radio.decrementTimer(events/2)
				lcd.line2("Timer " + radio.getTimerString())
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		radio.alarmCycle(direction)

	elif option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS:
		value = 1
		if option == radio.ALARMSETHOURS:
			value = 60
		if direction == UP:
			radio.incrementAlarm(value)
			#lcd.line2("Alarm " + radio.getAlarmTime())
		else:
			radio.decrementAlarm(value)
			#lcd.line2("Alarm " + radio.getAlarmTime())

	elif option == radio.STREAMING:
		radio.toggleStreaming()

	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			radio.setUpdateLibOff()
		else:
			radio.setUpdateLibOn()

	radio.optionChangedTrue()
	log.message("toggle_option end "+ str(option), log.DEBUG)
	return

# Update music library
def update_library(lcd,radio):
	log.message("Updating library", log.INFO)
	lcd.line1("Updating")
	lcd.line2("library")
	radio.updateLibrary()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
        lcd.line1("Loading:")
        radio.unmountAll()

        source = radio.getSource()
        if source == radio.RADIO:
                lcd.line2("Radio Stations")
                dirList=os.listdir(PlaylistsDirectory)
                for fname in dirList:
                        if os.path.isfile(fname):
                                continue
                        log.message("Loading " + fname, log.DEBUG)
                        lcd.line2(fname)
                        time.sleep(0.1)
                radio.loadStations()

        elif source == radio.PLAYER:
		lcd.line2("Media library")
                radio.loadMedia()
                current = radio.execMpcCommand("current")
                if len(current) < 1:
                        update_library(lcd,radio)
        return


# Display the RSS feed
def display_rss(lcd,rss):
	rss_line = rss.getFeed()
	lcd.setScrollSpeed(0.2) # Scroll RSS faster
	lcd.scroll2(rss_line,interrupt)
	return

# Display the currently playing station or track
def display_current(lcd,radio):
	current_id = radio.getCurrentID()
	source = radio.getSource()

	if source == radio.RADIO:
		current = radio.getCurrentStation()
	else:
		current_artist = radio.getCurrentArtist()
		index = radio.getSearchIndex()
		current_artist = radio.getCurrentArtist()
		track_name = radio.getCurrentTitle()
		current = current_artist + " - " + track_name

	# Display any stream error
	leng = len(current)
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll2(errorStr,interrupt)
		radio.clearError()
	else:
		leng = len(current)
		if leng > 16:
			lcd.scroll2(current[0:160],interrupt)
		elif  leng < 1:
			lcd.line2("No input!")
			time.sleep(1)
			radio.play(1) # Reset station or track
		else:
			lcd.scroll2(current, interrupt)
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

# Source selection display
def display_source_select(lcd,radio):

	lcd.line1("Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("radio")
	elif source == radio.PLAYER:
		lcd.line2("media")
	return

# Display search (Station or Track)
def display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		current_track = radio.getTrackNameByIndex(index)

		# Speed up display whilst searching
		if radio.getEvents() == 0:
			lcd.scroll1("(" + str(index+1) + ")" + current_artist[0:160],interrupt)
			lcd.scroll2(current_track,interrupt)
		else:
			lcd.line1("(" + str(index+1) + ")" + current_artist)
			lcd.line2(current_track)
	else:
		lcd.line1("Search:" + str(index+1))

		current = index+1
		lcd.line1("Search")
		current_station = radio.getStationName(index)
		msg = current_station[0:40] + '('+ str(current) + ')'
		lcd.scroll2(msg,interrupt)

		# Speed up display whilst searching
		if radio.getEvents() == 0:
			lcd.scroll2(current_station[0:160],interrupt)
		else:
			lcd.line2(current_station)
	return


# Display volume and streamin on indicator
def displayVolume(lcd,radio):
	volume = radio.getVolume()
	msg = "Vol " + str(volume)
	if radio.getStreaming():
		msg = msg + ' *'
	lcd.line2(msg)
	time.sleep(0.1)
	return

# Options menu
def display_options(lcd,radio):

	option = radio.getOption()

	if option != radio.TIMER and option != radio.ALARM \
		and option != radio.ALARMSETHOURS and option != radio.ALARMSETMINS:
		lcd.line1("Menu:")

	if option == radio.RANDOM:
		if radio.getRandom():
			lcd.scroll2("Random on",interrupt)
		else:
			lcd.scroll2("Random off",interrupt)

	elif option == radio.CONSUME:
		if radio.getConsume():
			lcd.scroll2("Consume on", interrupt)
		else:
			lcd.scroll2("Consume off", interrupt)

	elif option == radio.REPEAT:
		if radio.getRepeat():
			lcd.scroll2("Repeat on",interrupt)
		else:
			lcd.scroll2("Repeat off",interrupt)

	elif option == radio.TIMER:
		lcd.line1("Set timer:")
		if radio.getTimer():
			lcd.scroll2("Timer " + radio.getTimerString(),interrupt)
		else:
			lcd.scroll2("Timer off",interrupt)

	elif option == radio.ALARM:
		alarmString = "Alarm off"
		lcd.line1("Set alarm:")
		alarmType = radio.getAlarmType()

		if alarmType == radio.ALARM_ON:
			alarmString = "Alarm on"
		elif alarmType == radio.ALARM_REPEAT:
			alarmString = "Alarm repeat"
		elif alarmType == radio.ALARM_WEEKDAYS:
			alarmString = "Weekdays only"
		lcd.scroll2(alarmString,interrupt)

	elif option == radio.ALARMSETHOURS:
		lcd.line1("Alarm:")
		lcd.scroll2("Alarm " + radio.getAlarmTime() + " hours",interrupt)

	elif option == radio.ALARMSETMINS:
		lcd.line1("Set alarm time:")
		lcd.scroll2("Alarm " + radio.getAlarmTime() + " mins",interrupt)

	elif option == radio.STREAMING:
		if radio.getStreaming():
			lcd.scroll2("Streaming on",interrupt)
		else:
			lcd.scroll2("Streaming off",interrupt)

	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			lcd.line2("Update list:Yes")
		else:
			lcd.line2("Update list:No")

	return

# Display shutdown  messages
def displayShutdown(lcd):
	lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop")
	radio.execCommand("shutdown -h now")
	lcd.line2("Shutdown issued")
	time.sleep(2)
	lcd.line1("Radio stopped")
	lcd.line2("Power off radio")
	return


# Display time and timer/alarm
def displayTime(lcd,radio):
	dateFormat = '%H:%M'
	todaysdate = strftime(dateFormat)
	timenow = strftime("%H:%M")
	message = todaysdate
	if radio.getTimer():
		message = timenow + " " + radio.getTimerString()
		if radio.alarmActive():
			message = message + " " + radio.getAlarmTime()
	lcd.line1(message)
	return


# Display wake up message
def displayWakeUpMessage(lcd):
	message = 'Good day'
	t = datetime.datetime.now()
	if t.hour >= 0 and t.hour < 12:
		message = 'Good morning'
	if t.hour >= 12 and t.hour < 18:
		message = 'Good afternoon'
	if t.hour >= 16 and t.hour <= 23:
		message = 'Good evening'
	lcd.line2(message)
	time.sleep(3)
	return

# Display if in sleep
def display_sleep(lcd,radio):
	message = 'Sleep mode'
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
	lcd.line2(message)

# Unmute radio and get stored volume
def unmuteRadio(lcd,radio):
	radio.unmute()
	displayVolume(lcd,radio)
	return

# Sleep exit message
def DisplayExitMessage(lcd):
	lcd.line1("Hit menu button")
	lcd.line2("to exit sleep")
	time.sleep(1)
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
			unmuteRadio(lcd,radio)
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

