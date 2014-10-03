#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an Adafruit RGB-backlit LCD plate for Raspberry Pi.
# $Id: ada_radio.py,v 1.36 2014/08/02 05:27:08 bob Exp $
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
import subprocess
import sys
import time
import string
import datetime 
import atexit
import shutil
import threading
import lirc
import pifacecommon
import pifacecad
import piface_lcd_class
from piface_lcd_class import Piface_lcd

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from log_class import Log
from rss_class import Rss
import menu

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile

# Instantiate classes
log = Log()
piface_lcd_class.log = log
menu.log = log
radio = Radio()
rss = Rss()
lcd = Piface_lcd()
listener = False 
interrupt = False

# Register exit routine
def finish():
	lcd.clear()
        listener.deactivate()
        if irlistener_activated: irlistenter.deactivate()
	radio.execCommand("umount /media  > /dev/null 2>&1")
	radio.execCommand("umount /share  > /dev/null 2>&1")
	lcd.line(0,0, "Radio stopped")
        lcd.backlight_off()


# Daemon class
class MyDaemon(Daemon):
	def run(self):
		global CurrentFile
                lcd.lock()
		log.init('radio')

		progcall = str(sys.argv)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)

		hostname = exec_cmd('hostname')
		ipaddr = exec_cmd('hostname -I')
		log.message("IP " + ipaddr, log.INFO)
		myos = exec_cmd('uname -a')
		log.message(myos, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.line(0,0, message)
		lcd.line(0,1, "IP " + ipaddr)
                lcd.backlight(True)
		time.sleep(4)
		log.message("Restarting MPD", log.INFO)
		lcd.line(0,1, "Starting MPD")
		radio.start()
		log.message("MPD started", log.INFO)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line(0,0, "Radio ver "+ radio.getVersion())
		lcd.scroll(0,1, mpd_version)
		time.sleep(1)
                lcd.unlock()

                menu.set_rss(rss)
                menu.set_radio(radio)
                menu.set_lcd(lcd)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
                menu.submenu(menu.date_play_menu())
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)

                listener = lcd.get_listener()
                listener.register(lcd.BUTTON1,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.button1)
                listener.register(lcd.BUTTON2,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.button2)
                listener.register(lcd.BUTTON3,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.button3)
                listener.register(lcd.BUTTON4,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.button4)
                listener.register(lcd.BUTTON5,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.button5)
                listener.register(lcd.LEFT,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.leftswitch)
                listener.register(lcd.RIGHT,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.rightswitch)
                listener.register(lcd.ENTER,
                                  pifacecad.IODIR_ON,
                                  menu.menukeys.leftrightbutton)
                listener.register(lcd.BUTTON1,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.button1_off)
                listener.register(lcd.BUTTON2,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.button2_off)
                listener.register(lcd.BUTTON3,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.button3_off)
                listener.register(lcd.BUTTON4,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.button4_off)
                listener.register(lcd.BUTTON5,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.button5_off)
                listener.register(lcd.LEFT,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.leftswitch_off)
                listener.register(lcd.RIGHT,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.rightswitch_off)
                listener.register(lcd.ENTER,
                                  pifacecad.IODIR_OFF,
                                  menu.menukeys.leftrightbutton_off)
                listener.activate()
                irlistener = pifacecad.IREventListener(
                        prog="pifacecad-radio-ts",
                        lircrc="/home/pi/radio/radiolircrc")
                for i in range(10):
                        irlistener.register(str(i), menu.menukeys.key)
                try:
                        irlistener.activate()
                except lirc.InitError:
                        log.message("Could not initialise IR, radio running without IR contorls.",log.WARNING)
                        irlistener_activated = False
                else:
                        irlistener_activated = True

		# Main processing loop
		count = 0 
		while True:
                        time.sleep(0.1)
                        menu.heartbeat()
                        
        
        def old_displayMode(self):
                radio.setSwitch(0)

                #lcd.update_display()

                display_mode = radio.getDisplayMode()
                lcd.setScrollSpeed(0.3) # Scroll speed normal 
                ipaddr = exec_cmd('hostname -I')

                # Shutdown command issued
                if display_mode == radio.MODE_SHUTDOWN:
                        displayShutdown(lcd)
                        while display_mode == radio.MODE_SHUTDOWN:
                                time.sleep(1)

                lcdlock.acquire()
                lcd.backlight(True)
                lcdlock.release()
                if ipaddr is "":
                        lcd.line(0,0, "No IP network")

                elif display_mode == radio.MODE_TIME:
                        displayTime(lcd,radio)
                        if radio.muted():
                                msg = "Sound muted"
                                if radio.getStreaming():
                                        msg = msg + ' *'
                                lcdlock.acquire()
                                lcd.line(0,1, msg)
                                lcdlock.release()
                        else:
                                display_current(lcd,radio)

                elif display_mode == radio.MODE_SEARCH:
                        display_search(lcd,radio)

                elif display_mode == radio.MODE_SOURCE:
                        display_source_select(lcd,radio)

                elif display_mode == radio.MODE_OPTIONS:
                        display_options(lcd,radio)

                elif display_mode == radio.MODE_IP:
                        lcdlock.acquire()
                        lcd.line(0,1, "Radio v" + radio.getVersion())
                        if ipaddr is "":
                                lcd.line(0,0, "No IP network")
                        else:
                                lcd.scroll(0,0, "IP " + ipaddr, interrupt)
                        lcdlock.release()

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
                        lcdlock.acquire()
                        lcd.line(0,1, "Volume " + str(radio.getVolume()))
                        lcdlock.release()

	def old_status(self):
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

        def left_button(self,event = None):
                log.message("LEFT switch" ,log.DEBUG)
                display_mode = radio.getDisplayMode()
                input_source = radio.getSource()
                if  display_mode != radio.MODE_SLEEP:
                        if display_mode == radio.MODE_OPTIONS:
                                toggle_option(radio,lcd,DOWN)
                                interrupt = True
                                self.displayMode()

                        elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
                                scroll_artist(radio,DOWN)
                                interrupt = True
                                self.displayMode()
                        else:
                                # Decrease volume
                                volChange = True
                                while volChange:

                                        # Mute function (Both buttons depressed)
                                        if lcd.buttonPressed(lcd.BUTTON2):
                                                radio.mute()
                                                lcdlock.acquire()
                                                lcd.line(0,1, "Mute")
                                                self.fix_display = 3
                                                lcdlock.release()
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
        def left_button_off(self,event = None):
                self.displayMode()


        def button2(self, event=None):
                display_mode = radio.getDisplayMode()
                input_source = radio.getSource()
		log.message("2nd switch" ,log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True
                                self.displayMode()

			elif display_mode == radio.MODE_SEARCH \
                             and input_source == radio.PLAYER:
				scroll_artist(radio,UP)
				interrupt = True
                                self.displayMode()
			else:
				# Increase volume
				volChange = True
				while volChange:
                                        lcd.backlight(True)

                                        # Mute function (Both buttons depressed)
					if lcd.buttonPressed(lcd.LEFTBUTTON):
						radio.mute()
                                                lcdlock.acquire()
						lcd.line(0,1, "Mute")
                                                self.fix_display = 3
                                                lcdlock.release()
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
        def button2_off(self, event=None):
                self.displayMode()

        def enter_button(self, event = None):
                display_mode = radio.getDisplayMode()
                input_source = radio.getSource()

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
                                lcdlock.aquire()
				lcd.line(0,1, "Getting RSS feed")
                                self.fix_display = -1
                                lcdlock.release

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+ 
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = lcd.buttonPressed(lcd.ENTER)
		count = 15
		while MenuSwitch:
			time.sleep(0.2)
			MenuSwitch = lcd.buttonPressed(lcd.ENTER)
                        lcd.backlight(True)
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
                        lcdlock.acquire()
			log.message("Reload " + str(source), log.INFO)
			lcd.line(0,1, "Please wait ")
                        lcdlock.release()
			reload(lcd,radio)
			radio.setReload(False)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.optionChanged():
			radio.setDisplayMode(radio.MODE_TIME)
			radio.optionChangedFalse()

		elif radio.loadNew():
			log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
			radio.playNew(radio.getSearchIndex())
			radio.setDisplayMode(radio.MODE_TIME)

		time.sleep(0.2)
		interrupt = True
        def enter_button_off(self, event = None):
                self.displayMode()

        def go_right(self, event=None):
                display_mode = radio.getDisplayMode()

		log.message("right", log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:

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
        def go_right_off(self, event=None):
                self.displayMode()

        def go_left(self, event=None):
                display_mode = radio.getDisplayMode()
		log.message("left", log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
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
        def go_left_off(self, event=None):
                self.displayMode()
                        

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
		lcd.line(0,1, "Volume " + str(radio.getVolume()))
		time.sleep(0.5)

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
                        lcdlock.acquire()
			lcd.line(0,1, "Not allowed")
			time.sleep(2)
                        lcdlock.release()

	elif option == radio.REPEAT:
		if radio.getRepeat():
			radio.repeatOff()
		else:
			radio.repeatOn()

	elif option == radio.TIMER:
		TimerChange = True

		# Buttons held in
		if radio.getTimer():
                        lcdlock.acquire()
			while TimerChange:
				if direction == UP:
					radio.incrementTimer(1)
					lcd.line(0,1, "Timer " + radio.getTimerString())
					TimerChange = lcd.buttonPressed(lcd.RIGHT)
				else:
					radio.decrementTimer(1)
					lcd.line(0,1, "Timer " + radio.getTimerString())
					TimerChange = lcd.buttonPressed(lcd.LEFT)
				time.sleep(0.1)
                        lcdlock.release()
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		radio.alarmCycle(direction)

	elif option == radio.ALARMSET:

		# Buttons held in
		AlarmChange = True
		value = 1
		twait = 0.4
                lcdlock.auqire()
		while AlarmChange:
			if direction == UP:
				radio.incrementAlarm(value)
				lcd.line(0,1, "Alarm " + radio.getAlarmTime())
				AlarmChange = lcd.buttonPressed(lcd.RIGHT)
			else:
				radio.decrementAlarm(value)
				lcd.line(0,1, "Alarm " + radio.getAlarmTime())
				AlarmChange = lcd.buttonPressed(lcd.LEFT)
			time.sleep(twait)
			twait = 0.1
			value = 5
                lcdlock.release()

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
	log.message("Initialising music library", log.INFO)
	lcd.line(0,0, "Initialising")
	lcd.line(0,1, "Please wait")
	exec_cmd("/bin/umount /media")
	exec_cmd("/bin/umount /share")
	radio.updateLibrary()
	mount_usb(lcd)
	mount_share()
	log.message("Updatimg music library", log.INFO)
	lcd.line(0,0, "Updating Library")
	lcd.line(0,1, "Please wait")
	radio.updateLibrary()
	radio.loadMusic()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
        lcd.lock()
	lcd.line(0,0, "Loading:")
	exec_cmd("/bin/umount /media")  # Unmount USB stick
	exec_cmd("/bin/umount /share")  # Unmount network drive

	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line(0,1, "Radio Stations")
		dirList=os.listdir("/var/lib/mpd/playlists")
		for fname in dirList:
			log.message("Loading " + fname, log.DEBUG)
			lcd.line(0,1, fname)
			time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		mount_usb(lcd)
		mount_share()
		radio.loadMusic()
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			update_library(lcd,radio)
        lcd.line(0,1, "Finished")
        lcd.unlock()
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
			lcd.line(0,1, fname)
			time.sleep(0.1)
	else:
		msg = "No USB stick found!"
		lcd.line(0,1, msg)
		time.sleep(2)
		log.message(msg, log.WARNING)
	return

# Mount any remote network drive
def old_mount_share():
	if os.path.exists("/var/lib/radiod/share"):
		myshare = exec_cmd("cat /var/lib/radiod/share")
		if myshare[:1] != '#':
			exec_cmd(myshare)
			log.message(myshare,log.DEBUG)
	return

# Display the RSS feed
def old_display_rss(lcd,rss):
	rss_line = rss.getFeed()
	lcd.setScrollSpeed(0.2) # Display rss feeds a bit quicker
	lcd.scroll(0,1, rss_line,interrupt)
	return

# Display the currently playing station or track
def old_display_current(lcd,radio):
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

        lcdlock.acquire()
	# Display any stream error
	leng = len(current)
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll(0,1, errorStr,interrupt)
		radio.clearError()
	else:
		leng = len(current)
		if leng > 16:
			lcd.scroll(0,1, current[0:160],interrupt)
		elif  leng < 1:
			lcd.line(0,1, "No input!")
			time.sleep(1)
			radio.play(1) # Reset station or track
		else:
			lcd.line(0,1, current)
        lcdlock.release()
	return

# Get currently playing station or track number from MPC
def old_get_current_id():
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
def old_get_mpc_list(cmd):
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
def old_scroll_search(radio,direction):
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
def old_scroll_artist(radio,direction):
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
def old_display_source_select(lcd,radio):
        lcdlock.acquire()
	lcd.line(0,0, "Input Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line(0,1, "Internet Radio")
	elif source == radio.PLAYER:
		lcd.line(0,1, "Music library")
        lcdlock.release()
	return

# Display search (Station or Track)
def old_display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
        lcdlock.acquire()
	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		lcd.scroll(0,0, "(" + str(index+1) + ")" + current_artist[0:160],interrupt)
		current_track = radio.getTrackNameByIndex(index)
		lcd.scroll(0,1, current_track,interrupt)
	else:
		lcd.line(0,0, "Search:" + str(index+1))
		current_station = radio.getStationName(index)
		lcd.scroll(0,1, current_station[0:160],interrupt)
        lcdlock.release()
	time.sleep(0.25)
	return


# Unmute radio and get stored volume
def old_unmuteRadio(lcd,radio):
	radio.unmute()
	displayVolume(lcd,radio)
	return

# Display volume and streaming on indicator
def old_displayVolume(lcd,radio):
	volume = radio.getVolume()
	msg = "Volume " + str(volume)
	if radio.getStreaming():
		msg = msg + ' *'
        lcdlock.acquire()
	lcd.line(0,1, msg)
        lcdlock.release()
	return

# Options menu
def old_display_options(lcd,radio):

        lcdlock.acquire()
	option = radio.getOption()
	if option != radio.TIMER and option != radio.ALARM and option != radio.ALARMSET:
			lcd.line(0,0, "Menu selection:")

	if option == radio.RANDOM:
		if radio.getRandom():
			lcd.line(0,1, "Random on")
		else:
			lcd.line(0,1, "Random off")

	elif option == radio.CONSUME:
		if radio.getConsume():
			lcd.line(0,1, "Consume on")
		else:
			lcd.line(0,1, "Consume off")

	elif option == radio.REPEAT:
		if radio.getRepeat():
			lcd.line(0,1, "Repeat on")
		else:
			lcd.line(0,1, "Repeat off")

	elif option == radio.TIMER:
		lcd.line(0,0, "Set timer:")
		if radio.getTimer():
			lcd.line(0,1, "Timer " + radio.getTimerString())
		else:
			lcd.line(0,1, "Timer off")

	elif option == radio.ALARM:
		alarmString = "Alarm off"
		lcd.line(0,0, "Set alarm:")
		alarmType = radio.getAlarmType()

		if alarmType == radio.ALARM_ON:
			alarmString = "Alarm on"
		elif alarmType == radio.ALARM_REPEAT:
			alarmString = "Alarm repeat"
		elif alarmType == radio.ALARM_WEEKDAYS:
			alarmString = "Weekdays only"
		lcd.line(0,1, alarmString)

	elif option == radio.ALARMSET:
		lcd.line(0,0, "Set alarm time:")
		lcd.line(0,1, "Alarm " + radio.getAlarmTime())

	elif option == radio.STREAMING:
		if radio.getStreaming():
			lcd.line(0,1, "Streaming on")
		else:
			lcd.line(0,1, "Streaming off")


	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			lcd.line(0,1, "Update list:Yes")
		else:
			lcd.line(0,1, "Update list:No")
        lcdlock.release()
	return

# Display if in sleep
def old_display_sleep(lcd,radio):
	message = 'Sleep mode'
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
        lcdlock.acquire()
	lcd.line(0,1, message)
        lcdlock.release()
	return

# Display time and timer/alarm
def old_displayTime(lcd,radio):
	todaysdate = strftime("%d.%m.%Y %H:%M")
	timenow = strftime("%H:%M")
	message = todaysdate
	if radio.getTimer():
		message = timenow + " " + radio.getTimerString()
		if radio.alarmActive():
			message = message + " " + radio.getAlarmTime()
        lcdlock.acquire()
	lcd.line(0,0, message)
        lcdlock.release()
	return

# Display wake up message
def old_displayWakeUpMessage(lcd):
	message = 'Good day'
	t = datetime.datetime.now()
	if t.hour >= 0 and t.hour < 12:
		message = 'Good morning'
	if t.hour >= 12 and t.hour < 18:
		message = 'Good afternoon'
	if t.hour >= 16 and t.hour <= 23:
		message = 'Good evening'
        lcdlock.acquire()
	lcd.line(0,1, message)
        lcdlock.release()
	time.sleep(3)
	return


# Display shutdown message
def old_displayShutdown(lcd):
        lcdlock.acquire()
	lcd.line(0,0, "Stpoping radio")
	radio.execCommand("service mpd stop")
	radio.execCommand("shutdown -h now")
	lcd.line(0,1, "Shutdown issued")
	time.sleep(3)
	lcd.line(0,0, "Radio stopped")
	lcd.line(0,1, "Power off radio")
        lcdlock.release()
	return

def old_displayInfo(lcd,ipaddr,mpd_version):
        lcdlock.acquire()
	lcd.line(0,0, "Radio version " + radio.getVersion())
	if ipaddr is "":
		lcd.line(0,1, "No IP network")
	else:
		lcd.scroll(0,1, "IP "+ ipaddr,interrupt)
        lcdlock.release()
	return

# Sleep exit message
def old_DisplayExitMessage(lcd):
        lcdlock.acquiere()
	lcd.line(0,0, "Hit menu button")
	lcd.line(0,1, "to exit sleep")
	time.sleep(1)
        lcdlock.release()
	return

# Check Timer fired
def old_checkTimer(radio):
	interrupt = False
	if radio.fireTimer():
		log.message("Timer fired", log.INFO)
		radio.mute()
		radio.setDisplayMode(radio.MODE_SLEEP)
		interrupt = True
	return interrupt

# Check state (play or pause)
# Returns paused True if paused
def old_checkState(radio):
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
        global daemon
	daemon = MyDaemon('/var/run/radiod.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
                        lcd.init()
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

