#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using a Piface backlit LCD plate for Raspberry Pi.
# $Id: radio_piface.py,v 1.8 2016/07/23 16:13:10 bob Exp $
#
# Author : Patrick Zacharias 
# based on Bob Rathbone's Adafruit code
# Site   : N/A
# 
# Bob Rathbone's site: http://bobrathbone.com
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
import signal
import subprocess
import sys
import time
import string
import datetime 
import atexit
import shutil
from lcd_piface_class import Lcd
from time import strftime

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from log_class import Log
from rss_class import Rss

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile
PlaylistsDirectory = "/var/lib/mpd/playlists/"

# Instantiate classes
log = Log()
radio = Radio()
rss = Rss()
lcd = Lcd()

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global lcd
	global log
	radio.execCommand("umount /media > /dev/null 2>&1")
	radio.execCommand("umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	lcd.line1("Radio stopped")
	lcd.line2("")
	lcd.line3("")
	lcd.line4("")
	GPIO.cleanup()
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		global CurrentFile
		log.init('radio')
		signal.signal(signal.SIGTERM,signalHandler)

		progcall = str(sys.argv)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I') # Debian-like IP check
		log.message("IP " + ipaddr, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.init(1)
		lcd.line1(message)
		lcd.line2("IP " + ipaddr)
		time.sleep(4)
		log.message("Restarting MPD", log.INFO)
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

		# Main processing loop
		count = 0 
		while True:
			get_switch_states(lcd,radio,rss)
			radio.setSwitch(0)

			display_mode = radio.getDisplayMode()
			lcd.setScrollSpeed(0.3) # Scroll speed normal 
			ipaddr = exec_cmd('hostname -I') #Same as above
#			ipaddr = exec_cmd('hostname -i')

			# Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			if ipaddr is "":
				lcd.line1("No IP network")

			elif display_mode == radio.MODE_TIME:
				if radio.getReload():
					log.message("Reload ", log.DEBUG)
					reload(lcd,radio)
					radio.setReload(False)

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
				displayTime(lcd,radio)
				display_rss(lcd,rss)

			elif display_mode == radio.MODE_SLEEP:
				displayTime(lcd,radio)
				display_sleep(lcd,radio)
				time.sleep(0.3)

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
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()	
	option = radio.getOption()
	
	if lcd.buttonPressed(lcd.MENU):
		log.message("MENU switch mode=" + str(display_mode), log.DEBUG)
		if radio.muted():
			unmuteRadio(lcd,radio)
		display_mode = display_mode + 1

		if display_mode > radio.MODE_LAST:
			display_mode = radio.MODE_TIME

		if display_mode == radio.MODE_RSS and not radio.alarmActive():
			if not rss.isAvailable():
				display_mode = display_mode + 1
			else:
				lcd.line2("Getting RSS feed")

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+ 
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = lcd.buttonPressed(lcd.MENU)
		count = 15
		while MenuSwitch:
			time.sleep(0.2)
			MenuSwitch = lcd.buttonPressed(lcd.MENU)
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
			lcd.line2("Please wait ")
			reload(lcd,radio)
			radio.setReload(False)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.optionChanged():
			#radio.setDisplayMode(radio.MODE_TIME)
			#radio.optionChangedFalse()

                        log.message("optionChanged", log.DEBUG)
                        if radio.alarmActive() and not radio.getTimer() and \
					(option == radio.ALARMSETHOURS \
					or option == radio.ALARMSETMINS):
                                radio.setDisplayMode(radio.MODE_SLEEP)
                                radio.mute()
                        else:
				display_mode = radio.MODE_TIME
				

                        radio.optionChangedFalse()


		elif radio.loadNew():
			log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
			radio.playNew(radio.getSearchIndex())
			radio.setDisplayMode(radio.MODE_TIME)

		time.sleep(0.2)
		interrupt = True

	elif lcd.buttonPressed(lcd.UP):
		log.message("UP switch", log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:

			radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

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


	elif lcd.buttonPressed(lcd.DOWN):
		log.message("DOWN switch", log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			radio.unmute()

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

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

	elif lcd.buttonPressed(lcd.LEFT):
		log.message("LEFT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,DOWN)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(DOWN)
				interrupt = True

			else:
				# Decrease volume
				volChange = True
				while volChange:

					# Mute function (Both buttons depressed)
					if lcd.buttonPressed(lcd.RIGHT):
						radio.mute()
						lcd.line2("Mute")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.decreaseVolume()
						displayVolume(lcd,radio)
						volChange = lcd.buttonPressed(lcd.LEFT)

						if volume <= 0:
							volChange = False
						time.sleep(0.05)
		else:
			DisplayExitMessage(lcd)

	elif lcd.buttonPressed(lcd.RIGHT):
		log.message("RIGHT switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(UP)
				interrupt = True
			else:
				# Increase volume
				volChange = True
				while volChange:

					# Mute function (Both buttons depressed)
					if lcd.buttonPressed(lcd.LEFT):
						radio.mute()
						lcd.line2("Mute")
						time.sleep(2)
						volChange = False
						interrupt = True
					else:
						volume = radio.increaseVolume()
						displayVolume(lcd,radio)
						volChange = lcd.buttonPressed(lcd.RIGHT) 

						if volume >= 100:
							volChange = False
						time.sleep(0.05)
		else:
			DisplayExitMessage(lcd)

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
					TimerChange = lcd.buttonPressed(lcd.RIGHT)
				else:
					radio.decrementTimer(1)
					lcd.line2("Timer " + radio.getTimerString())
					TimerChange = lcd.buttonPressed(lcd.LEFT)
				time.sleep(0.1)
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		radio.alarmCycle(direction)

	elif option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS:

		# Buttons held in
		AlarmChange = True
		value = 1
		twait = 0.4

                if option == radio.ALARMSETHOURS:
                        value = 60

		while AlarmChange:
			if direction == UP:
				radio.incrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime())
				AlarmChange = lcd.buttonPressed(lcd.RIGHT)
			else:
				radio.decrementAlarm(value)
				lcd.line2("Alarm " + radio.getAlarmTime())
				AlarmChange = lcd.buttonPressed(lcd.LEFT)
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
	return

# Update music library
def update_library(lcd,radio):
	log.message("Updating library", log.INFO)
	lcd.line1("Updating library")
	lcd.line2("Please wait")
	radio.updateLibrary()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
	lcd.line1("Loading:")

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
	lcd.setScrollSpeed(0.2) # Display rss feeds a bit quicker
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
		lcd.scroll1("(" + str(index+1) + ")" + current_artist[0:160],interrupt)
		current_track = radio.getTrackNameByIndex(index)
		lcd.scroll2(current_track,interrupt)
	else:
		lcd.line1("Search:" + str(index+1))
		current_station = radio.getStationName(index)
		lcd.scroll2(current_station[0:160],interrupt)

	time.sleep(0.25)
	return


# Unmute radio and get stored volume
def unmuteRadio(lcd,radio):
	radio.unmute()
	displayVolume(lcd,radio)
	return

# Display volume and streaming on indicator
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
	if option != radio.TIMER and option != radio.ALARM \
		and option != radio.ALARMSETHOURS and option != radio.ALARMSETMINS:
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

        elif option == radio.ALARMSETHOURS:
                lcd.line1("Set alarm time:")
                lcd.line2("Alarm " + radio.getAlarmTime() + " hours")

        elif option == radio.ALARMSETMINS:
                lcd.line1("Set alarm time:")
                lcd.line2("Alarm " + radio.getAlarmTime() + " mins")

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

# Display if in sleep
def display_sleep(lcd,radio):
	message = 'Sleep mode'
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
	lcd.line2(message)
	return

# Display time and timer/alarm
def displayTime(lcd,radio):
        dateFormat = radio.getDateFormat()
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


# Display shutdown message
def displayShutdown(lcd):
	lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop") # default way to start services under Debian
#	radio.execCommand("systemctl stop mpd") # uncomment this line and comment above if you're using systemd
	radio.execCommand("shutdown -h now")
	lcd.line2("Shutdown issued")
	time.sleep(3)
	lcd.line1("Radio stopped")
	lcd.line2("Power off radio")
	return

def displayInfo(lcd,ipaddr,mpd_version):
	lcd.line1("Radio version " + radio.getVersion())
	if ipaddr is "":
		lcd.line2("No IP network")
	else:
		lcd.scroll2("IP "+ ipaddr,interrupt)
	return

# Sleep exit message
def DisplayExitMessage(lcd):
	lcd.line1("Hit menu button")
	lcd.line2("to exit sleep")
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
#			os.system("systemctl stop mpd") # Again systemd stuff
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version " + radio.getVersion()
		elif 'run' == sys.argv[1]:
			daemon.run() # Used for debug purposes
			print "Run executed"
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|nodaemon|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 



