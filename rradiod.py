#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
# Rotary encoder version
# $Id: rradiod.py,v 1.44 2014/08/21 13:33:46 bob Exp $
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

# Switch definitions
# Volume rotary encoder
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
MUTE_SWITCH = 4
# Tuner rotary encoder
UP_SWITCH = 17
DOWN_SWITCH = 18
MENU_SWITCH = 25

# To use GPIO 14 and 15 (Serial RX/TX)
# Remove references to /dev/ttyAMA0 from /boot/cmdline.txt and /etc/inittab 

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile

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
	lcd.line1("Radio stopped ")
	lcd.line2("")
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

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I')
		myos = exec_cmd('uname -a')
		log.message(myos, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.line1(message)
		lcd.line2("IP " + ipaddr)
		time.sleep(4)
		log.message("Starting MPD", log.INFO)
		lcd.line2("Starting MPD")
		radio.start()
		log.message("MPD started", log.INFO)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line1("Radio ver "+ radio.getVersion())
		lcd.scroll2(mpd_version,no_interrupt)
		time.sleep(1)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

		# Define rotary switches
		volumeknob = RotaryEncoder(LEFT_SWITCH,RIGHT_SWITCH,MUTE_SWITCH,volume_event,boardrevision)
		tunerknob = RotaryEncoder(UP_SWITCH,DOWN_SWITCH,MENU_SWITCH,tuner_event,boardrevision)
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
			todaysdate = strftime("%H:%M %d/%m/%Y")
			ipaddr = exec_cmd('hostname -I')

		       # Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			elif ipaddr is "":
				lcd.line2("No IP network")
	
			elif display_mode == radio.MODE_TIME:
				displayTime(lcd,radio)
				if radio.muted():
					msg = "Sound muted"
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
				lcd.line2("Radio v" + radio.getVersion())
				if ipaddr is "":
					lcd.line1("No IP network")
				else:
					lcd.scroll1("IP " + ipaddr, interrupt)

			elif display_mode == radio.MODE_RSS:
				lcd.line1(todaysdate)
				display_rss(lcd,rss)

			elif display_mode == radio.MODE_SLEEP:
				lcd.line1(todaysdate)
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
				lcd.line2("Volume " + str(radio.getVolume()))
				time.sleep(0.5)


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
		lcd.line2("Volume " + str(radio.getVolume()))
		time.sleep(0.5)

	if not interrupt:
		interrupt = checkState(radio)

	return interrupt

def no_interrupt():
	return False

# Call back routine for the volume control knob
def volume_event(event):
	global radio
	global volumeknob
	switch = 0
	ButtonNotPressed = volumeknob.getSwitchState(MUTE_SWITCH)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = RIGHT_SWITCH
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = LEFT_SWITCH

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = MUTE_SWITCH

	radio.setSwitch(switch)
	return

# Call back routine for the tuner control knob
def tuner_event(event):
	global radio
	global tunerknob
	switch = 0
	ButtonNotPressed = tunerknob.getSwitchState(MENU_SWITCH)

	# Suppress events if tuner button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = UP_SWITCH
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = DOWN_SWITCH

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = MENU_SWITCH

	radio.setSwitch(switch)
	return

# Check switch states
def get_switch_states(lcd,radio,rss,volumeknob,tunerknob):
	interrupt = False	# Interrupt display
	switch = radio.getSwitch()
	pid = exec_cmd("cat /var/run/radiod.pid")
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()	
	events = radio.getEvents()
	option = radio.getOption()
	
	if switch == MENU_SWITCH:
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
			display_mode = radio.MODE_TIME

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = tunerknob.getSwitchState(MENU_SWITCH)
		log.message("switch state=" + str(MenuSwitch), log.DEBUG)
		count = 15
		while MenuSwitch == 0:
			time.sleep(0.2)
			MenuSwitch = tunerknob.getSwitchState(MENU_SWITCH)
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
			if radio.alarmActive() and not radio.getTimer() and option == radio.ALARMSET:
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

	elif switch == UP_SWITCH:
		if  display_mode != radio.MODE_SLEEP:
			log.message("UP switch display_mode " + str(display_mode), log.DEBUG)
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				scroll_search(radio,UP)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,UP)

			else:
				radio.channelUp()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)

			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == DOWN_SWITCH:
		log.message("DOWN switch display_mode " + str(display_mode), log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				scroll_search(radio,DOWN)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,DOWN)

			else:
				radio.channelDown()
				if display_mode == radio.MODE_RSS:
					radio.setDisplayMode(radio.MODE_TIME)
			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == LEFT_SWITCH:
		log.message("LEFT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,DOWN)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				scroll_artist(radio,DOWN)
				interrupt = True

			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
				volAdjust = radio.getEvents()/2
				if radio.muted():
					radio.unmute()
				volume = radio.getVolume()
				while volAdjust > 0:	
					volume -=  1
					if volume < 1:
						volume = 1
					radio.setVolume(volume)
					displayVolume(lcd,radio)
					volAdjust -= 1
		else:
			DisplayExitMessage(lcd)

	elif switch == RIGHT_SWITCH:
		log.message("RIGHT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				scroll_artist(radio,UP)
				interrupt = True
			else:
				# Set the volume by the number of rotary encoder events
				log.message("events=" + str(radio.getEvents()), log.DEBUG)
				volAdjust = radio.getEvents()/2
				if radio.muted():
					radio.unmute()

				volume = radio.getVolume()
				while volAdjust > 0:	
					volume += 1
					if volume > 100:
						volume = 100
					radio.setVolume(volume)
					displayVolume(lcd,radio)
					volAdjust -= 1
		else:
			DisplayExitMessage(lcd)

	elif switch == MUTE_SWITCH:
		log.message("MUTE switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				radio.unmute()
				displayVolume(lcd,radio)
				time.sleep(1)
			else:
				radio.mute()
				lcd.line2("Mute")
				interrupt = True
				time.sleep(2)
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

	elif option == radio.ALARMSET:
		value = 1
		if events > 4:
			value = 5
		if events > 10:
			value = 60
		if direction == UP:
			radio.incrementAlarm(value)
			lcd.line2("Alarm " + radio.getAlarmTime())
		else:
			radio.decrementAlarm(value)
			lcd.line2("Alarm " + radio.getAlarmTime())

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
	log.message("Initialising music library", log.INFO)
	lcd.line1("Initialising")
	lcd.line2("Please wait")
	exec_cmd("/bin/umount /media")
	exec_cmd("/bin/umount /share")
	radio.updateLibrary()
	mount_usb(lcd)
	mount_share()
	log.message("Updatimg music library", log.INFO)
	lcd.line1("Updating Library")
	lcd.line2("Please wait")
	radio.updateLibrary()
	radio.loadMusic()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
	lcd.line1("Loading:")
	exec_cmd("/bin/umount /media")  # Unmount USB stick
	exec_cmd("/bin/umount /share")  # Unmount network drive

	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Radio Stations")
		dirList=os.listdir("/var/lib/mpd/playlists")
		for fname in dirList:
		       log.message("Loading " + fname, log.DEBUG)
		       lcd.line2(fname)
		       time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		mount_usb(lcd)
		mount_share()
		radio.loadMusic()
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			update_library(lcd,radio)
	return

# Mount USB  drive
def mount_usb(lcd):
	usbok = False
	if os.path.exists("/dev/sda1"):
		device = "/dev/sda1"
		usbok = True

	elif os.path.exists("/dev/sdb1"):
		device = "/dev/sdb1"
		usbok = True

	if usbok:
		exec_cmd("/bin/mount -o rw,uid=1000,gid=1000 "+ device + " /media")
		log.message(device + " mounted on /media", log.DEBUG)
		dirList=os.listdir("/var/lib/mpd/music")
		for fname in dirList:
			lcd.line2(fname)
			time.sleep(0.1)
	else:
		msg = "No USB stick found!"
		lcd.line2(msg)
		time.sleep(2)
		log.message(msg, log.WARNING)
	return

# Mount any remote network drive
def mount_share():
	if os.path.exists("/var/lib/radiod/share"):
		myshare = exec_cmd("cat /var/lib/radiod/share")
		if myshare[:1] != '#':
			exec_cmd(myshare)
			log.message(myshare,log.DEBUG)
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
			lcd.line2(current)
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

# Scroll up and down between stations/tracks
def scroll_search(radio,direction):
	current_id = radio.getCurrentID()
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()

	# Artist displayed then don't increment track first time in
	
	if not radio.displayArtist():
		leng = len(playlist)
		log.message("len playlist =" + str(leng),log.DEBUG)
		if leng > 0:
			if direction == UP:
				index = index + 1
				if index >= leng:
					index = 0 
			else:
				index = index - 1
				if index < 0:
					index = leng - 1
			
	radio.setDisplayArtist(False)
	track =  radio.getTrackNameByIndex(index)
 	radio.setSearchIndex(index)	
 	radio.setLoadNew(True)	
	return 

# Scroll through tracks by artist
def scroll_artist(radio,direction):
	radio.setLoadNew(True)
	index = radio.getSearchIndex()
	playlist = radio.getPlayList()
	current_artist = radio.getArtistName(index)

	found = False
	leng = len(playlist)
	count = leng
	while not found:
		if direction == UP:
			index = index + 1
			if index >= leng:
				index = 0
		elif direction == DOWN:
			index = index - 1
			if index < 1:
				index = leng - 1

		new_artist = radio.getArtistName(index)
		if current_artist != new_artist:
			found = True

		count = count - 1

		# Prevent everlasting loop
		if count < 1:
			found = True
			index = current_id

	# If a Backward Search find start of this list
	found = False
	if direction == DOWN:
		current_artist = new_artist
		while not found:
			index = index - 1
			new_artist = radio.getArtistName(index)
			if current_artist != new_artist:
				found = True
		index = index + 1
		if index >= leng:
			index = leng-1

	radio.setSearchIndex(index)
	return

# Source selection display
def display_source_select(lcd,radio):

	lcd.line1("Input Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Internet Radio")
	elif source == radio.PLAYER:
		lcd.line2("Music library")
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
		current_station = radio.getStationName(index)

		# Speed up display whilst searching
		if radio.getEvents() == 0:
			lcd.scroll2(current_station[0:160],interrupt)
		else:
			lcd.line2(current_station)
	return


# Display volume and streamin on indicator
def displayVolume(lcd,radio):
	volume = radio.getVolume()
	msg = "Volume " + str(volume)
	if radio.getStreaming():
		msg = msg + ' *'
	lcd.line2(msg)
	return

# Options menu
def display_options(lcd,radio):

	option = radio.getOption()

	if option != radio.TIMER and option != radio.ALARM and option != radio.ALARMSET:
		lcd.line1("Menu selection:")

	if option == radio.RANDOM:
		if radio.getRandom():
			lcd.line2("Random on")
		else:
			lcd.line2("Random off")

	elif option == radio.CONSUME:
		if radio.getConsume():
			lcd.line2("Consume on")
		else:
			lcd.line2("Consume off")

	elif option == radio.REPEAT:
		if radio.getRepeat():
			lcd.line2("Repeat on")
		else:
			lcd.line2("Repeat off")

	elif option == radio.TIMER:
		lcd.line1("Set timer:")
		if radio.getTimer():
			lcd.line2("Timer " + radio.getTimerString())
		else:
			lcd.line2("Timer off")

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
		lcd.line2(alarmString)

	elif option == radio.ALARMSET:
		lcd.line1("Set alarm time:")
		lcd.line2("Alarm " + radio.getAlarmTime())

	elif option == radio.STREAMING:
		if radio.getStreaming():
			lcd.line2("Streaming on")
		else:
			lcd.line2("Streaming off")

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
	todaysdate = strftime("%H:%M %d/%m/%Y")
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

