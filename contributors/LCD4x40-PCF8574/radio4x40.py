#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an HD44780 LCD display via PCF8574 Port Expander
# $Id: radio4x40.py,v 1.1 2016/04/30 11:11:19 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# 
# modding by Pythy
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc' 
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# 4 x 20 character LCD version
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
from lcd_class4x40 import Lcd
from log_class import Log
from rss_class import Rss

# Switch definitions
MENU_SWITCH = 25
LEFT_SWITCH = 23
RIGHT_SWITCH = 24
UP_SWITCH = 17
DOWN_SWITCH = 4

# To use GPIO 14 and 15 (Serial RX/TX)
# Remove references to /dev/ttyAMA0 from /boot/cmdline.txt and /etc/inittab 

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile

log = Log()
radio = Radio()
lcd = Lcd(0x20,1,6,7,5,4,0,1,2,3)
rss = Rss()

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global lcd
	global log
	radio.execCommand("umount /media > /dev/null 2>&1")
	radio.execCommand("umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	lcd.line1("Radio stopped")
	lcd.line2("2")
	lcd.line3("1")
	lcd.line4("0")
	GPIO.cleanup()
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile

		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setwarnings(False)      # Ignore warnings

		boardrevision = radio.getBoardRevision() 
		if boardrevision == 1:
			# For rev 1 boards with no inbuilt pull-up/down resistors
			# Wire the GPIO inputs to ground via a 10K resistor
			GPIO.setup(MENU_SWITCH, GPIO.IN)
			GPIO.setup(UP_SWITCH, GPIO.IN)
			GPIO.setup(DOWN_SWITCH, GPIO.IN)
			GPIO.setup(LEFT_SWITCH, GPIO.IN)
			GPIO.setup(RIGHT_SWITCH, GPIO.IN)

		else:
			# For rev 2 boards with inbuilt pull-up/down resistors 
			# there is no need to physically wire the 10k resistors
			GPIO.setup(MENU_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(UP_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(DOWN_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(LEFT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(RIGHT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

		# Initialise radio
		log.init('radio')
		signal.signal(signal.SIGTERM,signalHandler)

		progcall = str(sys.argv)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)

		lcd.init()
		lcd.setWidth1(40)
		lcd.setWidth2(40)
		lcd.line1("Radio version " + radio.getVersion())
		time.sleep(0.5)

		ipaddr = exec_cmd('hostname -I')
		myos = exec_cmd('uname -a')
		hostname = exec_cmd('hostname -s')
		log.message(myos, log.INFO)
		log.message("IP " + ipaddr, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.line2(message)

		lcd.line3("Starting MPD")
		lcd.line4("IP " + ipaddr)
		radio.start()
		log.message("MPD started", log.INFO)
		time.sleep(0.5)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line3(mpd_version)
		lcd.line4("GPIO version " + str(GPIO.VERSION))
		time.sleep(2.0)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)
		lcd.line3("Radio Station " + str(radio.getCurrentID()))

		# Set up switch event processing
		GPIO.add_event_detect(MENU_SWITCH, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(LEFT_SWITCH, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(RIGHT_SWITCH, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(UP_SWITCH, GPIO.RISING, callback=switch_event, bouncetime=200)
		GPIO.add_event_detect(DOWN_SWITCH, GPIO.RISING, callback=switch_event, bouncetime=200)

		# Main processing loop
		count = 0 
		while True:

			# See if we have had an interrupt
			switch = radio.getSwitch()
			if switch > 0:
				get_switch_states(lcd,radio,rss)
				radio.setSwitch(0)

			display_mode = radio.getDisplayMode()
			lcd.setScrollSpeed(0.3) # Scroll speed normal
			todaysdate = strftime("%A, %d.%B %Y Time: %H:%M")
			ipaddr = exec_cmd('hostname -I')

			# Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			elif ipaddr is "":
				lcd.line3("No IP network")

			elif display_mode == radio.MODE_TIME:
				msg = todaysdate
				if radio.getStreaming():
					msg = msg + ' *' 
				lcd.line1(msg)
				display_current(lcd,radio)

			elif display_mode == radio.MODE_SEARCH:
				display_search(lcd,radio)

			elif display_mode == radio.MODE_SOURCE:
				display_source_select(lcd,radio)

			elif display_mode == radio.MODE_OPTIONS:
				display_options(lcd,radio)

			elif display_mode == radio.MODE_IP:
				displayInfo(lcd,ipaddr,mpd_version)

			elif display_mode == radio.MODE_RSS:
				lcd.line1(todaysdate)
				input_source = radio.getSource()
				if input_source == radio.RADIO:
					lcd.line3("Current station:" + str(radio.getCurrentID()))
				else:
					lcd.line3("Current track:" + str(radio.getCurrentID()))
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
				radio.unmute()
				displayWakeUpMessage(lcd)
				radio.setDisplayMode(radio.MODE_TIME)
					
			time.sleep(0.1)
			# End of main processing loop

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

# Scrolling LCD display interrupt routine
def interrupt():
	global lcd
	global radio
	global rss
	interrupt = False
	switch = radio.getSwitch()
	if switch > 0:
		interrupt = get_switch_states(lcd,radio,rss)
		radio.setSwitch(0)

	# Rapid display of track play status
	if  radio.getSource() == radio.PLAYER:
		if radio.volumeChanged():
			displayLine4(lcd,radio,"Volume " + str(radio.getVolume()))
			time.sleep(0.5)
		else:
			lcd.line4(radio.getProgress()) 

	elif (radio.getTimer() and not interrupt) or radio.volumeChanged():
		displayLine4(lcd,radio,"Volume " + str(radio.getVolume()))
		interrupt = checkTimer(radio)

	if not interrupt:
		interrupt = checkState(radio)

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
	interrupt = False       # Interrupt display
	switch = radio.getSwitch()
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()
	option = radio.getOption()

	if switch == MENU_SWITCH:
		log.message("MENU switch", log.DEBUG)
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
			display_mode = radio.MODE_TIME

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = GPIO.input(MENU_SWITCH)
		count = 15
		while MenuSwitch:
			time.sleep(0.2)
			MenuSwitch = GPIO.input(MENU_SWITCH)
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

		interrupt = True

	elif switch == UP_SWITCH:
		log.message("UP switch", log.DEBUG)

		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				unmuteRadio(lcd,radio)

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				scroll_search(radio,UP)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,UP)

			else:
				radio.channelUp()

			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == DOWN_SWITCH:
		log.message("DOWN switch", log.DEBUG)

		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				unmuteRadio(lcd,radio)

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				scroll_search(radio,DOWN)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,DOWN)

			else:
				radio.channelDown()
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
				# Decrease volume
				volChange = True
				while volChange:
					# Mute function (Both buttons depressed)
					if GPIO.input(RIGHT_SWITCH):
						radio.mute()
						if radio.alarmActive():
							radio.setDisplayMode(radio.MODE_SLEEP)
							interrupt = True
						displayLine4(lcd,radio,"Sound muted")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.decreaseVolume()
						displayLine4(lcd,radio,"Volume " + str(volume))
						volChange = GPIO.input(LEFT_SWITCH)
						if volume <= 0:
							volChange = False
						time.sleep(0.1)
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
				# Increase volume
				volChange = True
				while volChange:
					# Mute function (Both buttons depressed)
					if GPIO.input(LEFT_SWITCH):
						radio.mute()
						if radio.alarmActive():
							radio.setDisplayMode(radio.MODE_SLEEP)
							interrupt = True
						displayLine4(lcd,radio,"Sound muted")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.increaseVolume()
						displayLine4(lcd,radio,"Volume " + str(volume))
						volChange =  GPIO.input(RIGHT_SWITCH)
						if volume >= 100:
							volChange = False
						time.sleep(0.1)
		else:
			DisplayExitMessage(lcd)

	return interrupt

# Sleep exit message
def DisplayExitMessage(lcd):
	lcd.line3("Press menu button to")
	lcd.line4("exit sleep mode")
	time.sleep(1)
	lcd.line3("")
	lcd.line4("")
	return

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

	# Don't display reload if not player mode
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


# Toggle random mode (Certain options not allowed if RADIO)
def toggle_option(radio,lcd,direction):
	option = radio.getOption() 
	log.message("toggle_option option="+ str(option), log.DEBUG)

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
					TimerChange = GPIO.input(RIGHT_SWITCH)
				else:
					radio.decrementTimer(1)
					lcd.line2("Timer " + radio.getTimerString())
					TimerChange = GPIO.input(LEFT_SWITCH)
				time.sleep(0.1)
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		log.message("toggle_option radio.ALARM", log.DEBUG)
		radio.alarmCycle(direction)
		
	elif option == radio.ALARMSET:

		# Buttons held in
		AlarmChange = True
		value = 1
		twait = 0.4
		while AlarmChange:
			if direction == UP:
				radio.incrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime())
				AlarmChange = GPIO.input(RIGHT_SWITCH)
			else:
				radio.decrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime())
				AlarmChange = GPIO.input(LEFT_SWITCH)
			time.sleep(twait)
			twait = 0.1
			value = 5

	elif option == radio.STREAMING:
		radio.toggleStreaming()
			
	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			radio.setUpdateLibOff()
		else:
			radio.setUpdateLibOn()

	radio.optionChangedTrue()
	#time.sleep(0.3)
	return

# Update music library
def update_library(lcd,radio):
	log.message("Initialising music library", log.INFO)
	lcd.line2("Initialising Library")
	lcd.line3("Please wait")
	lcd.line4("Can take some time!")
	exec_cmd("/bin/umount /media")
	exec_cmd("/bin/umount /share")
	radio.updateLibrary()
	mount_usb(lcd)
	mount_share()
	log.message("Updatimg music library", log.INFO)
	lcd.line2("Updating Library")
	radio.updateLibrary()
	radio.loadMusic()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
	lcd.line1("Loading Playlist!!!")
	exec_cmd("/bin/umount /media")	# Unmount USB stick
	exec_cmd("/bin/umount /share")	# Unmount network drive

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
	lcd.setScrollSpeed(0.2) # Scroll RSS a bit faster
	lcd.scroll2(rss_line,interrupt)
	return

# Display the currently playing station or track
def display_current(lcd,radio):
	current = radio.getCurrentStation()
	current_id = radio.getCurrentID()
	source = radio.getSource()
	leng = len(current)

	if source == radio.RADIO:
		if current_id <= 0:
			lcd.line2("No stations found")
		else:
			lcd.line2("Radio station " + str(current_id))
	else:
		index = radio.getSearchIndex()
		playlist = radio.getPlayList()
		current_artist = radio.getCurrentArtist()
		lcd.line2(current_artist)

	# Display stream error 
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll3(errorStr,interrupt)
		radio.clearError()
	else:
		if leng > 20:
			lcd.scroll3(current[0:160],interrupt)
		elif  leng < 1:
			lcd.line3("No input!")
			time.sleep(1)
		else:
			lcd.line3(current)

	# Display progress of the currently playing track
	if radio.muted():
		displayLine4(lcd,radio,"Sound muted")
	else:
		if source == radio.PLAYER:
			lcd.line4(radio.getProgress()) 
		else:
			displayLine4(lcd,radio,"Volume " + str(radio.getStoredVolume())) 

	return

# Display if in sleep
def display_sleep(lcd,radio):
	message = 'Sleep mode'
	lcd.line2('')
	lcd.line3('')
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
	lcd.line4(message)
	return

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

	progress = radio.getProgress()
	if radio.muted():
		lcd.line4('Sound muted')
	else:
		# Is the radio actually playing ?
		if progress.find('/0:00') > 0:
			lcd.line4("Volume " + str(radio.getVolume()))
		else:
			lcd.line4(radio.getProgress()) 
	return

# Display search (Station or Track)
def display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
	current_id = radio.getCurrentID()
	lcd.line1("Search:" + str(index + 1))

	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		lcd.scroll2(current_artist[0:160],interrupt) 
		lcd.scroll3(radio.getTrackNameByIndex(index),interrupt) 
		lcd.line4(radio.getProgress())
	else:
		current_station = radio.getStationName(index)
		lcd.line3("Current station:" + str(radio.getCurrentID()))
		lcd.scroll2(current_station[0:160],interrupt) 
	return


# Unmute radio and get stored volume
def unmuteRadio(lcd,radio):
	radio.unmute()
	volume = radio.getVolume()
	lcd.line4("Volume " + str(volume))
	radio.setDisplayMode(radio.MODE_TIME)
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
		lcd.line1("Set timer function:")
		if radio.getTimer():
			lcd.line2("Timer " + radio.getTimerString())
		else:
			lcd.line2("Timer off")

	elif option == radio.ALARM:
		alarmString = "off"
		lcd.line1("Set alarm function:")
		alarmType = radio.getAlarmType()

		if alarmType == radio.ALARM_ON:
			alarmString = "on"
		elif alarmType == radio.ALARM_REPEAT:
			alarmString = "repeat"
		elif alarmType == radio.ALARM_WEEKDAYS:
			alarmString = "weekdays only"
		lcd.line2("Alarm " + alarmString)

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
			lcd.line2("Update playlist: Yes")
		else:
			lcd.line2("Update playlist: No")

	if  radio.getSource() == radio.PLAYER:
		lcd.line4(radio.getProgress())

	return

# Display volume and timer
def displayLine4(lcd,radio,msg):
	message = msg

	if radio.getTimer():
		message = msg + " " + radio.getTimerString()
	if radio.alarmActive():
		message = message + ' ' + radio.getAlarmTime()

	lcd.line4(message)
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
	lcd.line4(message)
	time.sleep(3)
	return

def displayShutdown(lcd):
	lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop")
	lcd.line3(" ")
	lcd.line4(" ")
	radio.execCommand("shutdown -h now")
	lcd.line2("Shutdown issued")
	time.sleep(3)
	lcd.line1("Radio stopped")
	lcd.line2("Power off radio")
	return

def displayInfo(lcd,ipaddr,mpd_version):
	lcd.line2("Radio version " + radio.getVersion())
	lcd.line3(mpd_version)
	lcd.line4("GPIO version " + GPIO.VERSION)
	if ipaddr is "":
		lcd.line3("No IP network")
	else:
		lcd.scroll1("IP "+ ipaddr,interrupt)
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

# Check state (pause or play)
# If external client such as mpc or MPDroid issue a pause or play command 
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

