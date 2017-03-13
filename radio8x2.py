#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
# $Id: radio8x2.py,v 1.5 2017/02/12 13:01:02 bob Exp $
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
import atexit
import traceback
import subprocess
import sys
import time
import string
import datetime 
from time import strftime
import shutil

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from lcd_class import Lcd
from log_class import Log
from rss_class import Rss

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

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global lcd
	global log
	radio.execCommand("sudo umount /media > /dev/null 2>&1")
	radio.execCommand("sudo umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	lcd.line1("Stopped")
	lcd.line2("")
	lcd.line3("")
	lcd.line4("")
	GPIO.cleanup()
	sys.exit(0)

# Signal SIGTERM handler
def signalSIGUSR1(signal,frame):
	global log
	global radio
	log.message("Radio got SIGUSR1", log.INFO)
	display_mode = radio.getDisplayMode() + 1
	if display_mode > radio.MODE_LAST:
		display_mode = radio.MODE_TIME
	radio.setDisplayMode(display_mode)
	return

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setwarnings(False)	     # Ignore warnings

                # Get switches configuration
                up_switch = radio.getSwitchGpio("up_switch")
                down_switch = radio.getSwitchGpio("down_switch")
                left_switch = radio.getSwitchGpio("left_switch")
                right_switch = radio.getSwitchGpio("right_switch")
                menu_switch = radio.getSwitchGpio("menu_switch")

		boardrevision = radio.getBoardRevision()
		if boardrevision == 1:
			# For rev 1 boards with no inbuilt pull-up/down resistors 
			# Wire the GPIO inputs to ground via a 10K resistor 
			GPIO.setup(menu_switch, GPIO.IN)
			GPIO.setup(up_switch, GPIO.IN)
			GPIO.setup(down_switch, GPIO.IN)
			GPIO.setup(left_switch, GPIO.IN)
			GPIO.setup(right_switch, GPIO.IN)
		else:
			# For rev 2 boards with inbuilt pull-up/down resistors the 
			# following lines are used instead of the above, so 
			# there is no need to physically wire the 10k resistors
			GPIO.setup(menu_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(up_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(down_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(left_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(right_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

		# Initialise radio
		log.init('radio')
		signal.signal(signal.SIGTERM,signalHandler)
		signal.signal(signal.SIGUSR1,signalSIGUSR1)

		progcall = str(sys.argv)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)

		lcd.init(boardrevision)
		lcd.setWidth(8)

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I')

		# Display daemon pid on the LCD
		message = "PID " + str(os.getpid())
		lcd.line1(message)
		time.sleep(2)

		# Wait for the IP network
		ipaddr = ""
		waiting4network = True
		count = 10
		while waiting4network:
			lcd.scroll2("Wait for network",no_interrupt)
			ipaddr = exec_cmd('hostname -I')
			time.sleep(1)
			count -= 1
			if (count < 0) or (len(ipaddr) > 1):
				waiting4network = False

		if len(ipaddr) < 1:
			lcd.line2("No IP")
		else:
			lcd.scroll2("IP " + ipaddr, no_interrupt)

		time.sleep(2)

		log.message("Starting MPD", log.INFO)
		lcd.scroll2("Starting MPD", no_interrupt)
		radio.start()
		log.message("MPD started", log.INFO)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line1("Ver "+ radio.getVersion())
		lcd.scroll2(mpd_version,no_interrupt)
		time.sleep(1)
		 	
                # Auto-load music library if no Internet
                if len(ipaddr) < 1 and radio.autoload():
                        log.message("Loading music library",log.INFO)
                        radio.setSource(radio.PLAYER)

                # Load radio
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

		# Set up switch event processing 
		GPIO.add_event_detect(menu_switch, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(left_switch, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(right_switch, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(up_switch, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(down_switch, GPIO.RISING, callback=switch_event, bouncetime=200)

		# Main processing loop
		count = 0 
		while True:
			switch = radio.getSwitch()
			if switch > 0:
				get_switch_states(lcd,radio,rss)

			display_mode = radio.getDisplayMode()
			lcd.setScrollSpeed(0.3) # Scroll speed normal
			ipaddr = exec_cmd('hostname -I')

		       # Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			if len(ipaddr) < 1:
				lcd.line2("No IP network")
	
			elif display_mode == radio.MODE_TIME:
				if radio.getReload():
					log.message("Reload ", log.DEBUG)
					reload(lcd,radio)
					radio.setReload(False)
				else:
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
				if len(ipaddr) < 1:
					lcd.line1("No IP")
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

# Interrupt scrolling LCD routine
def interrupt():
	global lcd
	global radio
	global rss
	interrupt = False
	switch = radio.getSwitch()
	if switch > 0:
		interrupt = get_switch_states(lcd,radio,rss)

	# Rapid display of timer
	if radio.getTimer() and not interrupt:
		displayTime(lcd,radio)
		interrupt = checkTimer(radio)

	if radio.volumeChanged():
		lcd.line2("Volume " + str(radio.getVolume()))
		time.sleep(0.5)

	if not interrupt:
		interrupt = checkState(radio) or radio.getInterrupt()

	return interrupt

def no_interrupt():
	return False

# Call back routine called by switch events
def switch_event(switch):
	global radio
	radio.setSwitch(switch)
	return

# Check switch states
def get_switch_states(lcd,radio,rss):
	interrupt = False	# Interrupt display
	switch = radio.getSwitch()
	pid = exec_cmd("cat /var/run/radiod.pid")
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()	
	
	# Get rotary switches configuration
	up_switch = radio.getSwitchGpio("up_switch")
	down_switch = radio.getSwitchGpio("down_switch")
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")
	menu_switch = radio.getSwitchGpio("menu_switch")
	
	if switch == menu_switch:
		log.message("MENU switch mode=" + str(display_mode), log.DEBUG)
		if radio.muted():
			unmuteRadio(lcd,radio)
		display_mode = display_mode + 1

		# Skip RSS mode if not available
		if display_mode == radio.MODE_RSS and not radio.alarmActive():
			if rss.isAvailable() and not radio.optionChanged():
				lcd.line2("Getting RSS feed")
			else:
				display_mode = display_mode + 1

		if display_mode > radio.MODE_LAST:
                        boardrevision = radio.getBoardRevision()
                        lcd.init(boardrevision) # Recover corrupted dosplay
			display_mode = radio.MODE_TIME

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = GPIO.input(menu_switch)
		count = 15
		while MenuSwitch:
			time.sleep(0.2)
			MenuSwitch = GPIO.input(menu_switch)
			count = count - 1
			if count < 0:
				log.message("Shutdown", log.DEBUG)
				MenuSwitch = False
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
			option = radio.getOption()
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

		interrupt = True

	elif switch == up_switch:
		if  display_mode != radio.MODE_SLEEP:
			log.message("UP switch display_mode " + str(display_mode), log.DEBUG)
			if radio.muted():
				radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				wait = 0.5
				while GPIO.input(up_switch):
					radio.getNext(UP)
					display_search(lcd,radio)
					time.sleep(wait)
					wait = 0.1

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

			elif display_mode == radio.MODE_SEARCH:
				wait = 0.5
				while GPIO.input(down_switch):
					radio.getNext(DOWN)
					display_search(lcd,radio)
					time.sleep(wait)
					wait = 0.1

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
				wait = 0.5
				while GPIO.input(left_switch):
					radio.findNextArtist(DOWN)
					display_search(lcd,radio)
					time.sleep(wait)
					wait = 0.1
				interrupt = True

			else:
				# Decrease volume
				volChange = True
				while volChange:
					# Mute function (Both buttons depressed)
					if GPIO.input(right_switch):
						radio.mute()
						lcd.line2("Mute")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.decreaseVolume()
						displayVolume(lcd,radio)
						volChange = GPIO.input(left_switch)
						if volume <= 0:
							volChange = False
						time.sleep(0.1)
		else:
			DisplayExitMessage(lcd)

	elif switch == right_switch:
		log.message("RIGHT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				wait = 0.5
				while GPIO.input(right_switch):
					radio.findNextArtist(UP)
					display_search(lcd,radio)
					time.sleep(wait)
					wait = 0.1
				interrupt = True
			else:
				# Increase volume
				volChange = True
				while volChange:
					# Mute function (Both buttons depressed)
					if GPIO.input(left_switch):
						radio.mute()
						lcd.line2("Mute")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.increaseVolume()
						displayVolume(lcd,radio)
						volChange =  GPIO.input(right_switch)
						if volume >= 100:
							volChange = False
						time.sleep(0.1)
		else:
			DisplayExitMessage(lcd)

	# Reset switch and return interrupt
	radio.setSwitch(0)
	return interrupt

# Cycle through the options
# Only display reload the library if in PLAYER mode
def cycle_options(radio,direction):

	option = radio.getOption()
	log.message("cycle_options  direction:" + str(direction)
		+ " option: " + str(option), log.DEBUG)


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

# Toggle or change options
def toggle_option(radio,lcd,direction):
	option = radio.getOption() 
	log.message("toggle_option option="+ str(option), log.DEBUG)

	# Get switches configuration
	up_switch = radio.getSwitchGpio("up_switch")
	down_switch = radio.getSwitchGpio("down_switch")
	left_switch = radio.getSwitchGpio("left_switch")
	right_switch = radio.getSwitchGpio("right_switch")
	menu_switch = radio.getSwitchGpio("menu_switch")

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
		TimerChange = True

		# Buttons held in
		if radio.getTimer():
			while TimerChange:
				if direction == UP:
					radio.incrementTimer(1)
					lcd.line2("Timer " + radio.getTimerString())
					TimerChange = GPIO.input(right_switch)
				else:
					radio.decrementTimer(1)
					lcd.line2("Timer " + radio.getTimerString())
					TimerChange = GPIO.input(left_switch)
				time.sleep(0.1)
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		radio.alarmCycle(direction)

        elif option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS:

		# Buttons held in
		AlarmChange = True
		twait = 0.4
		value = 1
		unit = " mins"
		if option == radio.ALARMSETHOURS:
			value = 60
			unit = " hours"
		while AlarmChange:
			if direction == UP:
				radio.incrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime() + unit)
				time.sleep(twait)
				AlarmChange = GPIO.input(right_switch)
			else:
				radio.decrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime() + unit)
				time.sleep(twait)
				AlarmChange = GPIO.input(left_switch)
			twait = 0.1

	elif option == radio.STREAMING:
		radio.toggleStreaming()


	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			radio.setUpdateLibOff()
		else:
			radio.setUpdateLibOn()

	radio.optionChangedTrue()
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
	lcd.line1("Loading")

	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("stations")
		dirList=os.listdir(PlaylistsDirectory)
		for fname in dirList:
			if os.path.isfile(fname):
				continue
			log.message("Loading " + fname, log.DEBUG)
			lcd.line2(fname)
			time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		lcd.line2("media")
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

# Source selection display
def display_source_select(lcd,radio):

	lcd.line1("Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Radio")
	elif source == radio.PLAYER:
		lcd.line2("Media")
	return

# Display search (Station or Track)
def display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		lcd.scroll1("(" + str(index+1) + ")" + current_artist[0:160],interrupt)
		current_track = radio.getTrackNameByIndex(index)
		lcd.scroll2(current_track,interrupt)
	else:
		current = index+1
		lcd.line1("Search")
		current_station = radio.getStationName(index)
		msg = current_station[0:40] + '('+ str(current) + ')'
		lcd.scroll2(msg,interrupt)
	return

# Display if in sleep
def display_sleep(lcd,radio):
	message = 'Sleep mode'
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
	lcd.line2(message)
	return

# Unmute radio and get stored volume
def unmuteRadio(lcd,radio):
	radio.unmute()
	displayVolume(lcd,radio)
	return

# Display volume and streamin on indicator
def displayVolume(lcd,radio):
	volume = radio.getVolume()
	msg = "Vol " + str(volume)
	if radio.getStreaming():
		msg = msg + ' *'
	lcd.line2(msg)
	return

# Options menu
def display_options(lcd,radio):

	option = radio.getOption()


	if option != radio.TIMER and option != radio.ALARM \
			and option != radio.ALARMSETHOURS and option != radio.ALARMSETMINS :
			lcd.line1("Menu:")

	if option == radio.RANDOM:
		if radio.getRandom():
			lcd.scroll2("Random on", interrupt)
		else:
			lcd.scroll2("Random off", interrupt)

	elif option == radio.CONSUME:
		if radio.getConsume():
			lcd.scroll2("Consume on", interrupt)
		else:
			lcd.scroll2("Consume off", interrupt)

	elif option == radio.REPEAT:
		if radio.getRepeat():
			lcd.scroll2("Repeat on", interrupt)
		else:
			lcd.scroll2("Repeat off", interrupt)

	elif option == radio.TIMER:
		lcd.line1("Timer:")
		if radio.getTimer():
			lcd.line2(radio.getTimerString())
		else:
			lcd.line2("off")

	elif option == radio.ALARM:
		alarmString = "off"
		lcd.line1("Alarm:")
		alarmType = radio.getAlarmType()

		if alarmType == radio.ALARM_ON:
			alarmString = "on"
		elif alarmType == radio.ALARM_REPEAT:
			alarmString = "repeat"
		elif alarmType == radio.ALARM_WEEKDAYS:
			alarmString = "Weekdays"
		lcd.line2(alarmString)

	elif option == radio.ALARMSETHOURS:
		lcd.line1("Set hour")
		lcd.line2(radio.getAlarmTime())

	elif option == radio.ALARMSETMINS:
		lcd.line1("Set mins")
		lcd.line2(radio.getAlarmTime())

	elif option == radio.STREAMING:
		if radio.getStreaming():
			lcd.scroll2("Streamng on", interrupt)
		else:
			lcd.scroll2("Streaming off", interrupt)

	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			lcd.scroll2("Update library:Yes", interrupt)
		else:
			lcd.scroll2("Update library:No", interrupt)

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
	lcd.scroll2(message, interrupt)
	time.sleep(3)
	return

# Display shutdown messages
def displayShutdown(lcd):
	lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop")
	radio.execCommand("shutdown -h now")
	lcd.line2("Shutdown")
	time.sleep(2)
	lcd.line1("Stopped")
	lcd.line2("Turn off")
	return


# Display time and timer/alarm
def displayTime(lcd,radio):
	dateFormat = "%H:%M"
	todaysdate = strftime(dateFormat)
	timenow = strftime("%H:%M")
	message = todaysdate
	if radio.getTimer():
		message = timenow + " " + radio.getTimerString()
		if radio.alarmActive():
			message = message + " " + radio.getAlarmTime()
	lcd.line1(message)
	return

# Sleep exit message
def DisplayExitMessage(lcd):
	lcd.line1("Hit menu")
	lcd.line2("to exit")
	time.sleep(1)
	return


# Check Timer fired
def checkTimer(radio):
	interrupt = False
	if radio.fireTimer():
		log.message("Timer fired", log.INFO)
		radio.mute()
		radio.setDisplayMode(radio.MODE_SLEEP)
		interrupt = True
	return interrupt

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
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
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

