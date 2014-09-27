#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.125 2014/08/21 06:42:18 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  Music Player Daemon 'mpd' and the python-mpd library
# Use "apt-get install python-mpd" to install the library
# Modified to use python-mpd2 library mpd.wikia.com
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import string
import time,datetime
import re
from log_class import Log
from translate_class import Translate
from mpd import MPDClient

# System files
RadioLibDir = "/var/lib/radiod"
CurrentStationFile = RadioLibDir + "/current_station"
CurrentTrackFile = RadioLibDir + "/current_track"
VolumeFile = RadioLibDir + "/volume"
TimerFile = RadioLibDir + "/timer" 
AlarmFile = RadioLibDir + "/alarm" 
StreamFile = RadioLibDir + "/streaming"
MpdPortFile = RadioLibDir + "/mpdport"
BoardRevisionFile = RadioLibDir + "/boardrevision"

log = Log()
translate = Translate()

Mpd = "/usr/bin/mpd"	# Music Player Daemon
Mpc = "/usr/bin/mpc"	# Music Player Client
client = MPDClient()	# Create the MPD client

class Radio:
	# Input source
	RADIO = 0
	PLAYER = 1

	# Player options
	RANDOM = 0
	CONSUME = 1
	REPEAT = 2
	TIMER = 3
	ALARM = 4
	ALARMSET = 5
	STREAMING = 6
	RELOADLIB = 7
	OPTION_LAST = RELOADLIB

	# Display Modes
	MODE_TIME = 0
	MODE_SEARCH  = 1
	MODE_SOURCE  = 2
	MODE_OPTIONS  = 3
	MODE_RSS  = 4
	MODE_IP  = 5
	MODE_LAST = MODE_IP	# Last one a user can select
	MODE_SLEEP = 6		# Sleep after timer or waiting for alarm
	MODE_SHUTDOWN = -1

	# Alarm definitions
	ALARM_OFF = 0
	ALARM_ON = 1
	ALARM_REPEAT = 2
	ALARM_WEEKDAYS = 3
	ALARM_LAST = ALARM_WEEKDAYS

	# Other definitions
	UP = 0
	DOWN = 1
	ONEDAYSECS = 86400	# Day in seconds
	ONEDAYMINS = 1440	# Day in minutes

	boardrevision = 2 # Raspberry board version type
	mpdport = 6600  # MPD port number
	volume = 80	# Volume level 0 - 100%
	pause = False   # Is radio state "pause"
	playlist = []	# Play list (tracks or radio stations)
	current_id = 1	# Currently playing track or station
	source = RADIO	# Source RADIO or Player
	reload = False	# Reload radio stations or player playlists
	option = ''     # Any option you wish
	artist = ""	# Artist (Search routines)
	error = False 	# Stream error handling
	errorStr = ""   # Error string
	switch = 0	# Switch just pressed
	updateLib = False    # Reload radio stations or player
	numevents = 0	     # Number of events recieved for a rotary switch
	volumeChange = False	# Volume change flag (external clients)

	display_mode = MODE_TIME	# Display mode
	display_artist = False		# Display artist (or tracck) flag
	current_file = ""  		# Currently playing track or station
	option_changed = False		# Option changed
	channelChanged = True		# Used to display title
	
	# MPD Options
	random = False	# Random play
	repeat = False	# Repeat play
	consume = False	# Consume tracks

	# Clock and timer options
	timer = False	  # Timer on
	timerValue = 30   # Timer value in minutes
	timeTimer = 0  	  # The time when the Timer was activated in seconds 
	volumetime = 0	  # Last volume check time

	alarmType = ALARM_OFF	# Alarm on
	alarmTime = "0:7:00"    # Alarm time default type,hours,minutes
	alarmTriggered = False	# Alarm fired

	stationName = ''		# Radio station name
	stationTitle = ''		# Radio station title

	option = RANDOM	 # Player option
	search_index = 0	# The current search index
	loadnew = False	 # Load new track from search
	streaming = False	# Streaming (Icecast) disabled
	VERSION	= "3.11"	# Version number

	def __init__(self):
		log.init('radio')

		# Set up MPD port file
		if not os.path.isfile(MpdPortFile) or os.path.getsize(MpdPortFile) == 0:
			self.execCommand ("echo 6600 > " + MpdPortFile)

		if not os.path.isfile(CurrentStationFile):
			self.execCommand ("mkdir -p " + RadioLibDir )

		# Set up current radio station file
		if not os.path.isfile(CurrentStationFile) or os.path.getsize(CurrentStationFile) == 0:
			self.execCommand ("echo 1 > " + CurrentStationFile)

		# Set up current track file
		if not os.path.isfile(CurrentTrackFile) or os.path.getsize(CurrentTrackFile) == 0:
			self.execCommand ("echo 1 > " + CurrentTrackFile)

		# Set up volume file
		if not os.path.isfile(VolumeFile) or os.path.getsize(VolumeFile) == 0:
			self.execCommand ("echo 75 > " + VolumeFile)

		# Set up timer file
		if not os.path.isfile(TimerFile) or os.path.getsize(TimerFile) == 0:
			self.execCommand ("echo 30 > " + TimerFile)

		# Set up Alarm file
		if not os.path.isfile(AlarmFile) or os.path.getsize(AlarmFile) == 0:
			self.execCommand ("echo 0:7:00 > " + AlarmFile)

		# Set up Streaming (Icecast) file
		if not os.path.isfile(StreamFile) or os.path.getsize(StreamFile) == 0:
			self.execCommand ("echo off > " + StreamFile)

		# Create mount point for USB stick link it to the music directory
		if not os.path.isfile("/media"):
			self.execCommand("mkdir -p /media")
			if not os.path.ismount("/media"):
				self.execCommand("chown pi:pi /media")
			self.execCommand("ln -f -s /media /var/lib/mpd/music")

		# Create mount point for networked music library (NAS)
		if not os.path.isfile("/share"):
			self.execCommand("mkdir -p /share")
			if not os.path.ismount("/share"):
				self.execCommand("chown pi:pi /share")
			self.execCommand("ln -f -s /share /var/lib/mpd/music")

		self.execCommand("chown -R pi:pi " + RadioLibDir)
		self.execCommand("chmod -R 764 " + RadioLibDir)
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)
                
                print("Radioklasse initialisiert")

	# Start the MPD daemon
	def start(self):
		# Start the player daemon
                print ("starte mpd")
		#self.execCommand("service mpd start")
		# Connect to MPD
		self.boardrevision = self.getBoardRevision()
		self.mpdport = self.getMpdPort()
		self.connect(self.mpdport)
		#client.clear()
		self.randomOff()
		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.current_id = self.getStoredID(self.current_file)
		log.message("radio.start current ID " + str(self.current_id), log.DEBUG)
		self.volume = self.getStoredVolume()
		self.setVolume(self.volume)
		self.timeTimer = int(time.time())
		self.timerValue = self.getStoredTimer()
		self.alarmTime = self.getStoredAlarm()
		sType,sHours,sMinutes = self.alarmTime.split(':')
		self.alarmType = int(sType)
		self.streaming = self.getStoredStreaming()
		if self.streaming:
			self.streamingOn()
		else:
			self.streamingOff()
		return


	# Connect to MPD
	def connect(self,port):
		global client
		connection = False
		retry = 2
		while retry > 0:
			client = MPDClient()	# Create the MPD client
			try:
				client.timeout = 10
				client.idletimeout = None
				client.connect("localhost", port)
				log.message("Connected to MPD port " + str(port), log.INFO)
				connection = True
				retry = 0
			except:
				log.message("Failed to connect to MPD on port " + str(port), log.ERROR)
				time.sleep(0.5)	# Wait for interrupt in the case of a shutdown
				log.message("Restarting MPD",log.DEBUG)
				if retry < 2:
					self.execCommand("service mpd restart") 
				else:
					self.execCommand("service mpd start") 
				time.sleep(2)	# Give MPD time to restart
				retry -= 1

		return connection

	# Input Source RADIO, NETWORK or PLAYER
	def getSource(self):
		return self.source

	def setSource(self,source):
		self.source = source

	# Reload playlists flag
	def getReload(self):
		return self.reload

	def setReload(self,reload):
		self.reload = reload

	# Reload music library flag
	def getUpdateLibrary(self):
		return self.updateLib

	def setUpdateLibOn(self):
		self.updateLib = True

	def setUpdateLibOff(self):
		self.updateLib = False

	# Load new track flag
	def loadNew(self):
		return self.loadnew

	def setLoadNew(self,loadnew):
		self.loadnew = loadnew
		return

	# Get the Raspberry pi board version from /proc/cpuinfo
	def getBoardRevision(self):
		revision = 1
		with open("/proc/cpuinfo") as f:
			cpuinfo = f.read()
		rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo).group(1)
		rev_int = int(rev_hex,16)
		if rev_int > 3:
			revision = 2
		self.boardrevision = revision
		log.message("Board revision " + str(self.boardrevision), log.INFO)
		return self.boardrevision

	# Get the MPD port number
	def getMpdPort(self):
		port = 6600
		if os.path.isfile(MpdPortFile):
			try:
				port = int(self.execCommand("cat " + MpdPortFile) )
			except ValueError:
				port = 6600
		else:
			log.message("Error reading " + MpdPortFile, log.ERROR)

		return port

	# Get options (synchronise with external mpd clients)
	def getOptions(self,stats):
		try:
			random = int(stats.get("random"))
			if random == 1:
				self.random = True
			else:
				self.random = False

			repeat = int(stats.get("repeat"))
			if repeat == 1:
				self.repeat = True
			else:
				self.repeat = False

			consume = int(stats.get("consume"))
			if consume == 1:
				self.consume = True
			else:
				self.consume = False

		except:
			log.message("radio.getOptions get error" + MpdPortFile, log.ERROR)
		return

	# Get volume and check if it has been changed by any MPD external client
	# Slug MPD calls to no more than  per 0.5 second
	def getVolume(self):
		volume = 0
		try:
			now = time.time()	
			if now > self.volumetime + 0.5:
				stats = self.getStats()
				volume = int(stats.get("volume"))
				self.volumetime = time.time()
			else:
				volume = self.volume
		except:
			log.message("radio.getVolume failed", log.ERROR)
			volume = 0
		if volume == str("None"):
			volume = 0

		if volume != self.volume:
			log.message("radio.getVolume external client changed volume " + str(volume),log.DEBUG)
			self.setVolume(volume)
			self.volumeChange = True
		return self.volume

	# Check for volume change
	def volumeChanged(self):
		volumeChange = self.volumeChange
		self.volumeChange = False
		return volumeChange

	# Set volume (Called from the radio client or external mpd client via getVolume())
	def setVolume(self,volume):
		log.message("radio.setVolume " + str(volume),log.DEBUG)
		if self.muted(): 
			self.unmute()
		else:
			if volume > 100:
				 volume = 100
			elif volume < 0:
				 volume = 0

			self.volume = volume
			self.execMpc(client.setvol(self.volume))

			# Don't change stored volume (Needed for unmute function)
			if not self.muted():
				self.storeVolume(self.volume)
		return self.volume


	# Increase volume 
	def increaseVolume(self):
		if self.muted(): 
			self.unmute()
		self.volume = self.volume + 1
		self.setVolume(self.volume)
		return  self.volume

	# Decrease volume 
	def decreaseVolume(self):
		if self.muted(): 
			self.unmute()
		self.volume = self.volume - 1
		self.setVolume(self.volume)
		return  self.volume

	# Mute sound functions (Also stops MPD if not streaming)
	def mute(self):
		log.message("radio.mute streaming=" + str(self.streaming),log.DEBUG)
		self.execMpc(client.setvol(0))
		self.volume = 0
		self.execMpc(client.pause(1))
		return

	# Unmute sound fuction, get stored volume
	def unmute(self):
		self.volume = self.getStoredVolume()
		log.message("radio.unmute volume=" + str(self.volume),log.DEBUG)
		self.execMpc(client.pause(0))
		self.execMpc(client.setvol(self.volume))
		return self.volume

	def muted(self):
		muted = True
		if self.volume > 0:
			muted = False
		return muted

	# Get the stored volume
	def getStoredVolume(self):
		volume = 75
		if os.path.isfile(VolumeFile):
			try:
				volume = int(self.execCommand("cat " + VolumeFile) )
			except ValueError:
				volume = 75
		else:
			log.message("Error reading " + VolumeFile, log.ERROR)

		return volume

	# Store volume in volume file
	def storeVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + VolumeFile)
		return

	# Random
	def getRandom(self):
		return self.random

	def randomOn(self):
		self.random = True
		self.execMpc(client.random(1))
		return

	def randomOff(self):
		self.random = False
		self.execMpc(client.random(0))
		return

	# Repeat
	def getRepeat(self):
		return self.repeat

	def repeatOn(self):
		self.repeat = True
		self.execMpc(client.repeat(1))
		return

	def repeatOff(self):
		self.repeat = False
		self.execMpc(client.repeat(0))
		return

	# Consume
	def getConsume(self):
		return self.consume

	def consumeOn(self):
		self.consume = True
		self.execMpc(client.consume(1))
		return

	def consumeOff(self):
		self.consume = False
		self.execMpc(client.consume(0))
		return

	# Timer functions
	def getTimer(self):
		return self.timer

	def timerOn(self):
		self.timerValue = self.getStoredTimer()
		self.timeTimer = int(time.time())
		self.timer = True
		return self.timer

	def timerOff(self):
		self.timer = False
		self.timerValue = 0
		return self.timer

	def getTimerValue(self):
		return self.timerValue

	def fireTimer(self):
		fireTimer = False
		if self.timer and self.timerValue > 0:
			now = int(time.time())
			if now > self.timeTimer + self.timerValue * 60:
				fireTimer = True
				# Store fired value
				self.storeTimer(self.timerValue)
				self.timerOff()
		return fireTimer

	# Display the amount of time remaining
	def getTimerString(self):
		tstring = ''
		now = int(time.time())
		value = self.timeTimer + self.timerValue * 60  - now
		if value > 0:
			minutes,seconds = divmod(value,60)
			hours,minutes = divmod(minutes,60)
			if hours > 0:
				tstring = '%d:%02d:%02d' % (hours,minutes,seconds)
			else:
				tstring = '%d:%02d' % (minutes,seconds)
		return  tstring

	# Increment timer.   
	def incrementTimer(self,inc):
		if self.timerValue > 120:
			inc = 10
		self.timerValue += inc
		if self.timerValue > self.ONEDAYMINS:
			self.timerValue = self.ONEDAYMINS
		self.timeTimer = int(time.time())
		return self.timerValue

	def decrementTimer(self,dec):
		if self.timerValue > 120:
			dec = 10
		self.timerValue -= dec
		if self.timerValue < 0:
			self.timerValue = 0	
			self.timer = False
		self.timeTimer = int(time.time())
		return self.timerValue

	# Get the stored timer value
	def getStoredTimer(self):
		timerValue = 0
		if os.path.isfile(TimerFile):
			try:
				timerValue = int(self.execCommand("cat " + TimerFile) )
			except ValueError:
				timerValue = 30
		else:
			log.message("Error reading " + TimerFile, log.ERROR)
		return timerValue

	# Store timer time in timer file
	def storeTimer(self,timerValue):
		self.execCommand ("echo " + str(timerValue) + " > " + TimerFile)
		return

	# Radio Alarm Functions
	def alarmActive(self):
		alarmActive = False
		if self.alarmType != self.ALARM_OFF:
			alarmActive = True
		return alarmActive

	def alarmCycle(self,direction):
		if direction == self.UP:
			self.alarmType += 1
		else:
			self.alarmType -= 1

		if self.alarmType > self.ALARM_LAST:
			self.alarmType = self.ALARM_OFF
		elif self.alarmType < self.ALARM_OFF:
			self.alarmType = self.ALARM_LAST

		if self.alarmType > self.ALARM_OFF:
			self.alarmTime = self.getStoredAlarm()
		
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)

		return self.alarmType

	# Switch off the alarm unless repeat or days of the week
	def alarmOff(self):
		if self.alarmType == self.ALARM_ON:
			self.alarmType = self.ALARM_OFF
		return self.alarmType

	# Increment alarm time
	def incrementAlarm(self,inc):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) + inc
		if minutes >= 60:
			minutes = minutes - 60 
			hours += 1
		if hours >= 24:
			hours = 0
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Decrement alarm time
	def decrementAlarm(self,dec):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) - dec
		if minutes < 0:
			minutes = minutes + 60 
			hours -= 1
		if hours < 0:
			hours = 23
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Fire alarm if current hours/mins matches time now
	def alarmFired(self):

		fireAlarm = False
		if self.alarmType > self.ALARM_OFF:
			sType,sHours,sMinutes = self.alarmTime.split(':')
			type = int(sType)
			hours = int(sHours)
			minutes = int(sMinutes)
			t1 = datetime.datetime.now()
			t2 = datetime.time(hours, minutes)
			weekday =  t1.today().weekday()

			if t1.hour == t2.hour and t1.minute == t2.minute and not self.alarmTriggered:
				# Is this a weekday
				if type == self.ALARM_WEEKDAYS and weekday < 5: 
					fireAlarm = True
				elif type < self.ALARM_WEEKDAYS:	
					fireAlarm = True

				if fireAlarm:
					self.alarmTriggered = fireAlarm 
					if type == self.ALARM_ON:
						self.alarmOff()
					log.message("radio.larmFired type " + str(type), log.DEBUG)
			else:
				self.alarmTriggered = False 

		return  fireAlarm

	# Get the stored alarm value
	def getStoredAlarm(self):
		alarmValue = '' 
		if os.path.isfile(AlarmFile):
			try:
				alarmValue = self.execCommand("cat " + AlarmFile)
			except ValueError:
				alarmValue = "0:7:00"
		else:
			log.message("Error reading " + AlarmFile, log.ERROR)
		return alarmValue

	# Store alarm time in alarm file
	def storeAlarm(self,alarmString):
		self.execCommand ("echo " + alarmString + " > " + AlarmFile)
		return

	# Get the actual alarm time
	def getAlarmTime(self):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		return '%d:%02d' % (hours,minutes) 
		
	# Get the alarm type
	def getAlarmType(self):
		return  self.alarmType
		
	# Get the stored streaming value
	def getStoredStreaming(self):
		streamValue = "off" 
		streaming = False
		if os.path.isfile(StreamFile):
			try:
				streamValue = self.execCommand("cat " + StreamFile)
			except ValueError:
				streamValue = "off"
		else:
			log.message("Error reading " + StreamFile, log.ERROR)

		if streamValue == "on":
			streaming = True	
		else:
			streaming = False	

		return streaming

	# Toggle streaming on off
	# Stream number is 2 
	def toggleStreaming(self):
		if self.streamingAvailable():
			if self.streaming:
				self.streamingOff()
			else:
				self.streamingOn()
		else:
			self.streaming = False
			self.storeStreaming("off")

		return self.streaming

	# Switch on Icecast2 streaming
	def streamingOn(self):
		output_id = 2
		self.streaming = True
		self.execCommand("service icecast2 start")
		self.execMpcCommand("enable " + str(output_id))
		self.storeStreaming("on")
		self.streamingStatus()
		return self.streaming

	# Switch off Icecast2 streaming
	def streamingOff(self):
		output_id = 2
		self.streaming = False
		self.execMpcCommand("disable " + str(output_id))
		self.execCommand("service icecast2 stop")
		self.storeStreaming("off")
		self.streamingStatus()
		return self.streaming

	# Display streaming status
	def streamingStatus(self):
		status = self.execCommand("mpc outputs | grep -i stream")
		if len(status)<1:
			status = "No Icecast streaming"
		log.message(status, log.INFO)
		return

	# Check if icecast streaming installed
	def streamingAvailable(self):
		fpath = "/usr/bin/icecast2"
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	# Store stram on or off in streaming file
	def storeStreaming(self,onoff):
		self.execCommand ("echo " + onoff + " > " + StreamFile)
		return

	# Get the streaming value
	def getStreaming(self):
		return self.streaming

	# Option changed 
	def optionChanged(self):
		return self.option_changed

	def optionChangedTrue(self):
		self.option_changed = True
		return

	def optionChangedFalse(self):
		self.option_changed = False
		return

	# Set  and get Display mode
	def getDisplayMode(self):
		return self.display_mode

	# Mode string for debugging
	def getDisplayModeString(self):
		sMode = ["MODE_TIME", "MODE_SEARCH", "MODE_SOURCE",
			 "MODE_OPTIONS", "MODE_RSS", "MODE_IP", "MODE_SLEEP"] 
		return sMode[self.display_mode]

	def setDisplayMode(self,display_mode):
		self.display_mode = display_mode
		return
	
	# Set any option you like here 
	def getOption(self):
		return self.option

	def setOption(self,option):
		self.option = option
		return
	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand via OS
	# Some commands are easier using mpc and don't have 
	# an effect adverse on performance
	def execMpcCommand(self,cmd):
		return self.execCommand(Mpc + " " + cmd)

	# Execute MPC comnmand using mpd library - Connect client if required
	def execMpc(self,cmd):
		try:
			ret = cmd
		except:
			log.message("execMpc exception", log.ERROR)
			if self.connect(self.mpdport):
				ret = cmd
		return ret

	# Get the ID  of the currently playing track or station ID
	def getCurrentID(self):
		try:
			currentsong = self.getCurrentSong()
			currentid = int(currentsong.get("pos")) + 1
			if self.current_id != currentid:
				log.message("radio.getCurrentID New ID " + str(currentid), log.DEBUG)
				self.current_id = currentid
				self.execCommand ("echo " + str(currentid) + " > " + self.current_file)
		except:
			self.current_id = 0
		return self.current_id

	# Check to see if an error occured
	def gotError(self):
		return self.error

	# Get the error string if a bad channel
	def getErrorString(self):
		self.error = False
		return self.errorStr

	# See if any error
	def checkStatus(self):
		try:
			status = client.status()
			self.errorStr = str(status.get("error"))
			if  self.errorStr != "None":
				if not self.error:
					self.errorStr = (self.errorStr 
						+ " (Station " + str(self.current_id) + ")")
					log.message(self.errorStr, log.DEBUG)
				self.error = True
			else:
				self.errorStr = ""
		except:
			log.message("checkStatus exception", log.ERROR)
			self.errorStr = "Status exception"
		return self.error

	# Get the progress of the currently playing track
	def getProgress(self):
		line = self.execMpcCommand("status | grep \"\[playing\]\" ")
		lineParts = line.split('/',1)
		if len(lineParts) >= 2:
			line = lineParts[1]
			while line.find('  ') > 0:
				line = line.replace('  ', ' ')
			lineParts = line.split(' ')
			progress = lineParts[1] + ' ' + lineParts[2]	
		else:
			progress =  ''
		return progress
		
	# Set the new ID  of the currently playing track or station (Also set search index)
	def setCurrentID(self,newid):
		log.message("radio.setCurrentID " + str(newid), log.DEBUG)
		self.current_id = newid

		# If an error (-1) reset to 1
		if self.current_id <= 0:
			self.current_id = 1
			log.message("radio.setCurrentID reset to " + str(self.current_id), log.DEBUG)

		# Don't allow an ID greater than the playlist length
		if self.current_id >= len(self.playlist):
			self.current_id = len(self.playlist)
			log.message("radio.setCurrentID reset to" + str(self.current_id), log.DEBUG)
		
		self.search_index = self.current_id - 1
		log.message("radio.setCurrentID index= " + str(self.search_index), log.DEBUG)
		self.execCommand ("echo " + str(self.current_id) + " > " + self.current_file)
		self.execCommand("/usr/bin/mpc status > /var/lib/radiod/status")
		name = self.getCurrentTitle()
		log.message("radio.getCurrentID (" + str(self.current_id) + ") " + name, log.INFO)
		return

	# Get stats array
	def getStats(self):
		try:
			stats = client.status()
		except:
			log.message("radio.getStats failed", log.ERROR)

		self.getOptions(stats)	# Get options 
		return stats

	# Get current state (play or pause) 
	# Slug this to only allow one per second
	def getState(self):
		state = "play"
		try:
			stats = self.getStats()
			state = str(stats.get("state"))
		except:
			log.message("radio.getState failed", log.ERROR)
			state = "unknown"

		if state == "pause":
			self.pause = True
		else:
			self.pause = False
			
		return state

	# Get paused state
	def paused(self):
		self.getState()
		return self.pause

	# Get current song information (Only for use within this module)
	def getCurrentSong(self):
		try:
			currentsong = self.execMpc(client.currentsong())
		except:
			# Try re-connect and status
			try:
				if self.connect(self.mpdport):
					currentsong = self.execMpc(client.currentsong())
			except:
				log.message("radio.getCurrentSong failed", log.ERROR)
		return currentsong

	# Get the currently playing radio station from mpd 
	# This is usually from "name"but some stations use the "title" field
	def getRadioStation(self):
		currentsong = self.getCurrentSong()
		try:
			name = str(currentsong.get("name"))
		except:
			name = "No name"
		# If no name returned check that the file name is returned OK 
		# and use name from the search index
		if name == "None":
			try:
				time.sleep(0.2)
				currentsong.get("file")
				name = self.getStationName(self.search_index) 
			except:
				name = "Bad stream (" + str(self.current_id) + ")"

		self.stationName = translate.escape(name)
		return self.stationName

	# Get the title of the currently playing station or track from mpd 
	def getCurrentTitle(self):
		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
			#log.message("Title: " + title, log.DEBUG)
			title = translate.escape(title)
		except:
			title = ''

		if title == 'None':
			title = ''

		try:
			genre = str(currentsong.get("genre"))
		except:
			genre = ''
		if genre == 'None':
			genre = ''

		# If the title contained the station name blank it out
		if title == self.stationName:
			title = ''

		if title == '':
			# Usually used if this is a podcast
			if len(genre) > 0:
				title = genre	
		if self.channelChanged and len(title) > 0: 
			log.message( "Title: "+ title,log.INFO)
			self.channelChanged = False

		return title

	# Get the currently playing radio station from mpd 
 	# Returns the same format as the mpc current command
	# Used for two line displays only
	def getCurrentStation(self):
		name = self.getRadioStation() + ' (' + str(self.current_id) + ')'
		title = self.getCurrentTitle()
		if len(title) > 0:
			currentPlaying = name + ": " + title
		else:
			currentPlaying = name
		self.checkStatus()
		return currentPlaying

	# Get the name of the current artist mpd (Music librarry only)
	def getCurrentArtist(self):
		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
			title = translate.escape(title)
			artist = str(currentsong.get("artist"))
		except:
			artist = "Unknown artist!"
		if str(artist) == 'None':
			artist = "Unknown artist"
		return artist

	# Get the last ID stored in /var/lib/radiod
	def getStoredID(self,current_file):
		current_id = 0
		if os.path.isfile(self.current_file):
			current_id = 1
			try:
				current_id = int(self.execCommand("cat " + self.current_file) )
			except ValueError:
				current_id = 1
		else:
			log.message("Error reading " + self.current_file, log.ERROR)

		if current_id <= 0:
			current_id = 1
		return current_id

	# Change radio station up
	def channelUp(self):
		new_id = self.getCurrentID() + 1
		log.message("radio.channelUp " + str(new_id), log.DEBUG)
		if new_id > len(self.playlist):
			new_id = 1
			self.play(new_id)
		else:
			self.execMpc(client.next())
				
		new_id = self.getCurrentID()
		self.setCurrentID(new_id)

		# If any error MPD will skip to next channel
		self.checkStatus()
		self.channelChanged = True
		return new_id

	# Change radio station down
	def channelDown(self):
		new_id = self.getCurrentID() - 1
		log.message("radio.channelDown " + str(new_id), log.DEBUG)
		if new_id <= 0:
			new_id = len(self.playlist)
			self.play(new_id)
		else:
			self.execMpc(client.previous())

		new_id = self.getCurrentID()
		self.setCurrentID(new_id)

		# Check if error if so try next channel down
		if self.checkStatus():
			new_id -= 1
			if new_id <= 0:
				new_id = len(self.playlist)
			self.play(new_id)
		self.channelChanged = True
		return new_id

	# Toggle the input source (Reload is done when Reload requested)
	def toggleSource(self):
		if self.source == self.RADIO:
			self.source = self.PLAYER

		elif self.source == self.PLAYER:
			self.source = self.RADIO

		return

	# Load radio stations
	def loadStations(self):
		log.message("radio.loadStations", log.DEBUG)
		self.execMpc(client.clear())

		dirList = os.listdir("/var/lib/mpd/playlists")
		for fname in dirList:
			cmd = "load \"" + fname.strip("\n") + "\""
			log.message(cmd, log.DEBUG)
			fname = fname.strip("\n")
			try:
				self.execMpc(client.load(fname))
			except:
				log.message("Failed to load playlist " + fname, log.ERROR)

		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.playlist = self.createPlayList()
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)
		self.play(self.current_id)
		self.search_index = self.current_id - 1
		self.source = self.RADIO
		return

	# Load music library 
	def loadMusic(self):
		log.message("radio.loadMusic", log.DEBUG)
		self.execMpcCommand("stop")
		self.execMpcCommand("clear")
		directory = "/var/lib/mpd/music/"

		dirList=os.listdir(directory)
		for fname in dirList:
			fname = fname.strip("\n")
			path = directory +  fname
			nfiles = len(os.listdir(path))
			if nfiles > 0:
				cmd = "add \"" + fname + "\""
				log.message(cmd,log.DEBUG)
				log.message(str(nfiles) + " files/directories found",log.DEBUG)
				try:
					self.execMpcCommand(cmd)
				except:
					log.message("Failed to load music directory " + fname, log.ERROR)
			else:
				log.message(path + " is empty", log.INFO)

		self.playlist = self.createPlayList()
		self.current_file = CurrentTrackFile
		self.current_id = self.getStoredID(self.current_file)

		# Old playlists may have been longer.
		length = len(self.playlist)
		if self.current_id > length:
			self.current_id = 1
			log.message("radio.loadMusic ID " + str(self.current_id), log.DEBUG)

		# Important use mpc not python-mpd calls as these give problems
		if length > 0:
			log.message("radio.loadMusic play " + str(self.current_id), log.DEBUG)
			self.execMpcCommand("play " + str(self.current_id))
			self.search_index = self.current_id - 1
			self.execMpcCommand("random on")
			self.execMpcCommand("repeat off")
			self.execMpcCommand("consume off")
			self.random = True  # Random play
			self.repeat = False  # Repeat play
			self.consume = False # Consume tracks
		else:
			log.message("radio.loadMusic playlist length =  " + str(length), log.ERROR)

		log.message("radio.loadMusic complete", log.DEBUG)
		return length

	# Update music library 
	def updateLibrary(self):
		log.message("radio.updateLibrary", log.DEBUG)
		self.execMpcCommand("-w update")
		self.setUpdateLibOff()
		return

	# Play a new track using search index
	def playNew(self,index):
		self.setLoadNew(False)
		self.play(index + 1)
		return

	# Play a track number  (Starts at 1)
	def play(self,number):
		log.message("radio.play " + str(number), log.DEBUG)
		log.message("radio.play Playlist len " + str(len(self.playlist)), log.DEBUG)
		if number > 0 and number <= len(self.playlist):
			self.current_id = number
			self.setCurrentID(self.current_id)
		else:	
			log.message("play invalid station/track number "+ str(number), log.ERROR)
			self.setCurrentID(1)

		# Client play function starts at 0 not 1
		log.message("play station/track number "+ str(self.current_id), log.DEBUG)
		self.execMpc(client.play(self.current_id-1))
		self.checkStatus()
		return

	# Clear streaming and other errors
	def clearError(self):
		log.message("clearError()", log.DEBUG)
		client.clearerror()
		self.errorStr = ""
		self.error = False 
		return

	# Get list of tracks or stations
	def getPlayList(self):
		return self.playlist

	# Create list of tracks or stations
	def createPlayList(self):
		log.message("radio.createPlaylist", log.DEBUG)
		list = []
		line = ""
		cmd = "playlist"	
		p = os.popen(Mpc + " " + cmd)
		while True:
			line =  p.readline().strip('\n')
			if line.__len__() < 1:
				break
			line = translate.escape(line)
			list.append(line)
		self.playlist = list
		log.message("radio.createPlaylist length " + str(len(self.playlist)), log.DEBUG)
		return self.playlist

	# Get the length of the current list
	def getListLength(self):
		return len(self.playlist)	

	# Display artist True or False
	def displayArtist(self):
		return self.display_artist

	def setDisplayArtist(self,dispArtist):
		self.display_artist = dispArtist

	# Set Search index
	def getSearchIndex(self):
		return self.search_index

	def setSearchIndex(self,index):
		self.search_index = index
		return

	# Get Radio station name by Index
	def getStationName(self,index):
		if self.source == self.RADIO:
			station = "No stations found"
		else:
			station = "No tracks found"
		if len(self.playlist) > 0:
			station = self.playlist[index] 
		return station

	# Get track name by Index
	def getTrackNameByIndex(self,index):
		if len(self.playlist) < 1:
			track = "No tracks"
		else:
			sections = self.playlist[index].split(' - ')
			leng = len(sections)
			if leng > 1:
				track = sections[1]
			else:
				track = "No track"
			track = translate.escape(track)
		if str(track) == 'None':
			track = "Unknown track"
		return track

	# Get artist name by Index
	def getArtistName(self,index):
		if len(self.playlist) < 1:
			artist = "No playlists"
		else:
			sections = self.playlist[index].split(' - ')
			leng = len(sections)
			if leng > 1:
				artist = sections[0]
			else:
				artist = "Unknown artist"
			artist = translate.escape(artist)
		return artist

	# Switch store and retrieval routines
	def setSwitch(self,switch):
		self.switch = switch
		return

	def getSwitch(self):
		return self.switch

	# Routines for storing rotary encoder events
	def incrementEvent(self):
		self.numevents += 1
		return self.numevents
	
	def decrementEvent(self):
		self.numevents -= 1
		if self.numevents < 0:
			self.numevents = 0
		return self.numevents
	
	def getEvents(self):
		return self.numevents
	
	def resetEvents(self):
		self.numevents = 0
		return self.numevents
	
	# Version number
	def getVersion(self):
		return self.VERSION

# End of Radio Class

### Test routine ###
if __name__ == "__main__":
	print ("Test radio_class.py")
	radio = Radio()
	print  ("Version",radio.getVersion())
	print ("Board revision", radio.getBoardRevision())

	# Start radio and load the radio stations
	radio.start()
	radio.loadStations()
	radio.play(1)
	current_id = radio.getCurrentID()
	index = current_id - 1
	print ("Current ID ", current_id )
	print ("Station",current_id,":", radio.getStationName(index))

	# Test volume controls
	print ("Stored volume", radio.getStoredVolume())
	radio.setVolume(75)
	radio.increaseVolume()
	radio.decreaseVolume()
	radio.getVolume()
	time.sleep(5)
	print ("Mute")
	radio.mute()
	time.sleep(3)
	print ("Unmute")
	radio.unmute()
	print ("Volume", radio.getVolume())
	time.sleep(5)

	# Test channel functions
	current_id = radio.channelUp()
	print ("Channel up")
	index = current_id - 1
	print ("Station",current_id,":", radio.getStationName(index))
	time.sleep(5)
	current_id = radio.channelDown()
	print ("Channel down")
	index = current_id - 1
	print ("Station",current_id,":", radio.getStationName(index))

	# Check library load
	print ("Load music library")
	radio.loadMusic()

	# Check state
	print ("Paused  " +  str(radio.paused()))

	# Check timer
	print ("Set Timer 1 minute")
	radio.timerValue = 1
	radio.timerOn()

	while not radio.fireTimer():
		time.sleep(1)
	print ("Timer fired")

	# Exit 
	sys.exit(0)
	
# End of __main__ routine


