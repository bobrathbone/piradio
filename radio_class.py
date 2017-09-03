#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.306 2017/07/24 06:27:17 bob Exp $
# 
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
#	      The authors shall not be liable for any loss or damage however caused.
#

import os
import sys,pwd
import string
import time,datetime
import re
import SocketServer
from time import strftime
import pdb

from udp_server_class import UDPServer
from udp_server_class import RequestHandler
from log_class import Log
from translate_class import Translate
from config_class import Configuration
from airplay_class import AirplayReceiver
from language_class import Language
from mpd import MPDClient

# System files
ConfigFile = "/etc/radiod.conf"
RadioLibDir = "/var/lib/radiod"
PlaylistsDirectory = "/var/lib/mpd/playlists"
MusicDirectory = "/var/lib/mpd/music"
CurrentStationFile = RadioLibDir + "/current_station"
CurrentTrackFile = RadioLibDir + "/current_track"
RandomSettingFile = RadioLibDir + "/random"
VolumeFile = RadioLibDir + "/volume"
TimerFile = RadioLibDir + "/timer" 
AlarmFile = RadioLibDir + "/alarm" 
StreamFile = RadioLibDir + "/streaming"
BoardRevisionFile = RadioLibDir + "/boardrevision"
Icecast = "/usr/bin/icecast2"

log = Log()
translate = Translate()
config = Configuration()
airplay = AirplayReceiver()
language = None
server = None

Mpd = "/usr/bin/mpd"	# Music Player Daemon
Mpc = "/usr/bin/mpc"	# Music Player Client
client = MPDClient()	# Create the MPD client

class Radio:
	# Input source
	RADIO = 0
	PLAYER = 1
	AIRPLAY = 2

	# Rotary class
	ROTARY_STANDARD = config.STANDARD
	ROTARY_ALTERNATIVE = config.ALTERNATIVE

	# Player options
	RANDOM = 0
	CONSUME = 1
	REPEAT = 2
	RELOADLIB = 3
	TIMER = 4
	ALARM = 5
	ALARMSETHOURS = 6
	ALARMSETMINS = 7
	STREAMING = 8
	SELECTCOLOR = 9
	OPTION_LAST = STREAMING
	OPTION_ADA_LAST = SELECTCOLOR

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
	LEFT = 2
	RIGHT = 3

	ONEDAYSECS = 86400	# Day in seconds
	ONEDAYMINS = 1440	# Day in minutes

	audio_error = False 	# No sound device
	boardrevision = 2 # Raspberry board version type
	udphost = 'localhost'  # Remote IR listener UDP Host
	udpport = 5100  # Remote IR listener UDP port number
	mpdport = 6600  # MPD port number
	volume = 80	# Volume level 0 - 100%
	device_error_cnt = 0	# Device error causes an abort
	isMuted = False # Is radio state "pause" or "stop"
	playlist = []	# Play list (tracks or radio stations)
	current_id = 1	# Currently playing track or station
	source = RADIO	# Source RADIO or Player
	reload = False	# Reload radio stations or player playlists
	artist = ""	# Artist (Search routines)
	airplay = False # Airplay (shairport-sync) installed
	error = False 	# Stream error handling
	errorStr = ""   # Error string
	switch = 0	# Switch just pressed
	updateLib = False    # Reload radio stations or player
	numevents = 0	     # Number of events recieved for a rotary switch
	volumeChange = False	# Volume change flag (external clients)
	interrupt = False	# Was IR remote interrupt received
	stats = None		# MPD Stats array
	currentsong = None	# Current song / station
	state = 'play'		# State (used if get state fails) 
	getIdError = False	# Prevent repeated display of ID error
	StationNamesSource = config.LIST # Use own names from playlist
	use_playlist_extensions = False # MPD 0.16 requires playlist.<ext>
	rotary_class = config.STANDARD  # Rotary class standard all alternate
	mode_last = MODE_IP	 	# Last mode a user can select
	option_last = OPTION_LAST	# Last available option
	display_mode = MODE_TIME	# Display mode
	display_artist = False		# Display artist (or tracck) flag
	current_file = ""  		# Currently playing track or station
	option_changed = False		# Option changed
	channelChanged = True		# Used to display title
	configOK = False		# Do we have a configuration file
	display_playlist_number = False # Display playlist number
	
	# MPD Options
	random = False	# Random play
	repeat = False	# Repeat play
	consume = False	# Consume tracks

	# Clock and timer options
	timer = False	  # Timer on
	timerValue = 30   # Timer value in minutes
	timeTimer = 0  	  # The time when the Timer was activated in seconds 
	volumetime = 0	  # Last volume check time
	dateFormat = "%H:%M %d/%m/%Y"   # Date format

	alarmType = ALARM_OFF	# Alarm on
	alarmTime = "0:7:00"    # Alarm time default type,hours,minutes
	alarmTriggered = False	# Alarm fired

	stationName = ''		# Radio station name
	stationTitle = ''		# Radio station title

	option = RANDOM	  # Player option
	search_index = 0	 # The current search index
	loadnew = False	  # Load new track from search
	streaming = False	# Streaming (Icecast) disabled
	VERSION	= "5.11"		# Version number

	ADAFRUIT = 1		# I2C backpack type AdaFruit
	PCF8574  = 2 		# I2C backpack type PCF8574
	i2c_backpack = ADAFRUIT
	i2c_address = 0x00	# Use default I2C address

	speech = False 		# Speech for visually impaired or blind persons

	# Configuration files 
	ConfigFiles = {
 		CurrentStationFile: 1,
 		CurrentTrackFile: 1,
 		VolumeFile: 75,
 		TimerFile: 30,
		AlarmFile: "0:07:00", 
		StreamFile: "off", 
 		RandomSettingFile: 0,
		}

	# Initialisation routine
	def __init__(self):
		if pwd.getpwuid(os.geteuid()).pw_uid > 0:
			print "This program must be run with sudo or root permissions!"
			sys.exit(1)

		log.init('radio')
		self.setupConfiguration()
		return

	# Set up configuration files
	def setupConfiguration(self):
		# Create directory 
		if not os.path.isfile(CurrentStationFile):
			self.execCommand ("mkdir -p " + RadioLibDir )

		# Initialise configuration files from ConfigFiles list
		for file in self.ConfigFiles:
			value = self.ConfigFiles[file]
			if not os.path.isfile(file) or os.path.getsize(file) == 0:
				self.execCommand ("echo " + str(value) + " > " + file)

		# Create mount point for USB stick and link it to the music directory
		if not os.path.isfile("/media"):
			self.execCommand("mkdir -p /media")
			if not os.path.ismount("/media"):
				self.execCommand("chown pi:pi /media")
			self.execCommand("sudo ln -f -s /media /var/lib/mpd/music")

		# Create mount point for networked music library (NAS)
		if not os.path.isfile("/share"):
			self.execCommand("mkdir -p /share")
			if not os.path.ismount("/share"):
				self.execCommand("chown pi:pi /share")
			self.execCommand("sudo ln -f -s /share /var/lib/mpd/music")

		# Is Airplay installed (shairport-sync)
		self.airplay = config.getAirplay()
		if self.airplay:
			self.stopAirplay()

		self.execCommand("chown -R pi:pi " + RadioLibDir)
		self.execCommand("chmod -R 764 " + RadioLibDir)
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)
		return

	# Call back routine for the IR remote
	def remoteCallback(self):
		global server
		key = server.getData()
		log.message("IR remoteCallback " + key, log.DEBUG)

		if key == 'KEY_MUTE':
			if self.muted():	
				self.unmute()
			else:
				self.mute()
			self.setInterrupt()

		elif key == 'KEY_VOLUMEUP':
			self.increaseVolume()
			self.setInterrupt()
			self.volumeChange = True

		elif key == 'KEY_VOLUMEDOWN':
			self.decreaseVolume()
			self.setInterrupt()
			self.volumeChange = True

		elif key == 'KEY_CHANNELUP':
			self.channelUp()
			self.setInterrupt()

		elif key == 'KEY_CHANNELDOWN':
			self.channelDown()
			self.setInterrupt()

		elif key == 'KEY_MENU' or key == 'KEY_OK':
			self.cycleMenu()
			self.setInterrupt()

		elif key == 'KEY_LANGUAGE':
			self.toggleSpeech()	
			self.setInterrupt()

		elif key == 'KEY_INFO':
			self.speakInformation()	
			self.setInterrupt()

		# These come from the Web CGI script
		elif key == 'MEDIA':
			self.loadMedia()
			self.setInterrupt()

		elif key == 'RADIO':
			self.loadStations()
			self.setInterrupt()

		elif key == 'AIRPLAY':
			self.startAirplay()
			self.setInterrupt()

		elif key == 'INTERRUPT':
			self.setInterrupt()

		# Handle left,right, up and down keys
		else:
			self.handle_key(key)
			self.setInterrupt()

		return 

	# Set up radio configuration and start the MPD daemon
	def start(self):
		global server
		global language

		config.display()
		# Get Configuration parameters /etc/radiod.conf
		self.boardrevision = self.getBoardRevision()
		self.mpdport = config.getMpdPort()
		self.udpport = config.getRemoteUdpPort()
		self.udphost = config.getRemoteListenHost()
		self.display_playlist_number = config.getDisplayPlaylistNumber()
		self.source = config.getSource()
		self.speech = config.getSpeech()
		self.stationNamesSource = config.getStationNamesSource()
		language = Language(self.speech) # language is a global
		self.use_playlist_extensions = config.getPlaylistExtensions()
		self.rotary_class = config.getRotaryClass()

		# Log OS version information 
		OSrelease = self.execCommand("cat /etc/os-release | grep NAME")
		OSrelease = OSrelease.replace("PRETTY_NAME=", "OS release: ")
		OSrelease = OSrelease.replace('"', '')
		log.message(OSrelease, log.INFO)
		myos = self.execCommand('uname -a')
		log.message(myos, log.INFO)

		# Start the player daemon
		self.execCommand("service mpd start")
		# Connect to MPD
		self.connect(self.mpdport)
		client.clear()
		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.current_id = self.getStoredID(self.current_file)
		log.message("radio.start current ID " + str(self.current_id), log.DEBUG)
		self.volume = self.getStoredVolume()
		self._setVolume(self.volume)

		# Alarm and timer settings
		self.timeTimer = int(time.time())
		self.timerValue = self.getStoredTimer()
		self.alarmTime = self.getStoredAlarm()
		sType,sHours,sMinutes = self.alarmTime.split(':')
		self.alarmType = int(sType)
		if self.alarmType > self.ALARM_OFF:
			self.alarmType = self.ALARM_OFF

		# Icecast Streaming settings
		self.streaming = self.getStoredStreaming()
		if self.streaming:
			self.streamingOn()
		else:
			self.streamingOff()

		# Start the remote control listener
		try:
			server = UDPServer((self.udphost,self.udpport),RequestHandler)
			msg = "UDP Server listening on " + self.udphost + " port " + str(self.udpport)
			log.message(msg, log.INFO)
			server.listen(server,self.remoteCallback)
		except:
			log.message("UDP server could not bind to " + self.udphost
					+ " port " + str(self.udpport), log.ERROR)
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
				time.sleep(2.5)	# Wait for interrupt in the case of a shutdown
				time.sleep(0.2)	# Give MPD time 
				retry -= 1

		return connection

	# Handle IR remote key
	def handle_key(self,key):
		if self.display_mode == self.MODE_OPTIONS:
			self.handle_options(key)

		elif self.display_mode == self.MODE_SOURCE:
			self.handle_source(key)

		elif self.display_mode == self.MODE_SEARCH:
			self.handle_search(key)

		self.optionChangedTrue()

		return

	# Handle stepping through menu options and changing them
	def handle_options(self,key):
		direction = -1

		if key == 'KEY_UP':	
			direction = self.UP
		elif key == 'KEY_DOWN':	
			direction = self.DOWN
		elif key == 'KEY_LEFT':	
			direction = self.LEFT
		elif key == 'KEY_RIGHT':	
			direction = self.RIGHT
		
		if direction == self.UP or direction == self.DOWN:
			self.cycleOptions(direction)
		elif direction == self.LEFT or direction == self.RIGHT:	
			self.changeOption(direction)
		return

	# Handle stepping through menu options
	def cycleOptions(self,direction):
		option = self.getOption()

		log.message("radio.cycleOptions option=" + str(option) \
			+ " direction=" + str(direction), log.DEBUG)

		# Cycle through option
		if direction == self.UP:
			option += 1
		elif direction == self.DOWN:
			option -= 1


		# Skip reload if not in player mode
		if option == self.RELOADLIB and self.source != self.PLAYER:
			if direction == self.UP:
				option += 1
			else:
				option -= 1
 
		if option > self.option_last:
				option = self.RANDOM

		elif option < 0:
			option = self.option_last
			if option == self.RELOADLIB and self.source != self.PLAYER:
				option -= 1

		self.setOption(option)
		return

	# Handle search (IR routine)
	def handle_search(self,key):
		direction = self.UP
		if key == 'KEY_LEFT' or key == 'KEY_DOWN':
			direction = self.DOWN

		if self.source == self.RADIO:
			self.getNext(direction)
		else:
			# Step through tracks
			if key == 'KEY_LEFT' or key == 'KEY_RIGHT':
				self.getNext(direction)
			else:
				# Step through artist
				self.findNextArtist(direction)
		return

	# Toggle speech
	def toggleSpeech(self):
		sVoice = language.getText('voice')
		if self.speech:
			sOff = language.getText('off')
			self.speak(sVoice  + ' ' + sOff)
			self.speech = False 
		else:
			self.speech = True 
			sOn = language.getText('on')
			self.speak(sVoice  + ' ' + sOn)
		return

	# Scroll up and down between stations/tracks
	def getNext(self,direction):
		playlist = self.getPlayList()
		index = self.getSearchIndex()

		# Artist displayed then don't increment track first time in

		if not self.displayArtist():
			leng = len(playlist)
			if leng > 0:
				if direction == self.UP:
					index = index + 1
					if index >= leng:
						index = 0
				else:
					index = index - 1
					if index < 0:
						index = leng - 1

		self.setSearchIndex(index)
		self.setLoadNew(True)
		name = self.getStationName(index)
		if name.startswith("http:") and '#' in name: 
			url,name = name.split('#')
		msg = "radio.getNext index " + str(index) + " "+ name
		log.message(msg, log.DEBUG)
		if self.speech: 
			self.speak(language.getText('search') + " " +  str(index+1)
				 + " " + name)
		return

	# Scroll through tracks by artist
	def findNextArtist(self,direction):
		self.setLoadNew(True)
		index = self.getSearchIndex()
		playlist = self.getPlayList()
		current_artist = self.getArtistName(index)

		found = False
		leng = len(playlist)
		count = leng
		while not found:
			if direction == self.UP:
				index = index + 1
				if index >= leng:
					index = 0
			else:
				index = index - 1
				if index < 1:
					index = leng - 1

			new_artist = self.getArtistName(index)
			if current_artist != new_artist:
				found = True

			count = count - 1

			# Prevent everlasting loop
			if count < 1:
				found = True
				index = self.current_id

		# If a Backward Search find start of this list
		found = False
		if direction == self.DOWN:
			self.current_artist = new_artist
			while not found:
				index = index - 1
				new_artist = self.getArtistName(index)
				if self.current_artist != new_artist:
					found = True
			index = index + 1
			if index >= leng:
				index = leng-1

		self.setSearchIndex(index)

		if self.speech: 
			self.speak( str(index+1) + " " + new_artist)
		return

	# Change option (Used by remote control and non display radio only)
	def changeOption(self,direction):

		option = self.getOption()
		sOptions = language.getOptionText()
		sOption = sOptions[option]

		log.message("radio.changeOption " + str(option) + " " + sOption, log.DEBUG)

		if option == self.RANDOM:
			if self.getRandom():
				self.randomOff()
			else:
				self.randomOn()

		elif option == self.CONSUME:
			if self.getConsume():
				self.consumeOff()
			else:
				self.consumeOn()

		elif option == self.REPEAT:
			if self.getRepeat():
				self.repeatOff()
			else:
				self.repeatOn()

		elif option == self.ALARM:
			self.alarmCycle(direction)

		elif option == self.STREAMING:
			self.toggleStreaming()

		elif option == self.RELOADLIB:
			if self.getUpdateLibrary():
				self.setUpdateLibOff()
			else:
				self.setUpdateLibOn()

		elif option == self.TIMER:
			if self.getTimer():
				if direction == self.UP:
					self.incrementTimer(1)
				else:
					self.decrementTimer(1)
			else:
				self.timerOn()

		elif option == self.ALARMSETHOURS or option == self.ALARMSETMINS :
		 	value = 1	
			if option == self.ALARMSETHOURS:
				value = 60	
			if direction == self.UP:
				self.incrementAlarm(value)
			else:
				self.decrementAlarm(value)

		self.optionChangedTrue()
		self.speakOption(option)
		return

	# Handle toggling of source
	def handle_source(self,key):
		if key == 'KEY_UP':
			self.cycleSource(self.UP)
		elif key == 'KEY_DOWN':	
			self.cycleSource(self.DOWN)
		return

	# Input Source RADIO, NETWORK or PLAYER
	def getSource(self):
		return self.source

	def setSource(self,source):
		self.source = source

	# Reload playlists flag
	def getReload(self):
		return self.reload

	def setReload(self,reload):
		log.message("radio.setReload " + str(reload), log.DEBUG)
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
		log.message("radio.setLoadNew " + str(loadnew), log.DEBUG)
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

	# Get MPD version
	def getMpdVersion(self):
		sVersion = self.execCommand('mpd -V | grep Daemon')
		return sVersion.split()[3]

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
	def _getVolume(self):
		volume = 0
		error = False
		try:
			now = time.time()	
			if now > self.volumetime + 0.5:
				stats = self.getStats()
				volume = int(stats.get("volume"))
				self.volumetime = time.time()
			else:
				volume = self.volume
		except:
			log.message("radio._getVolume failed", log.ERROR)
			volume = 1
			error = True

		if volume == str("None"):
			volume = -1
			error = True
		if volume < 0:
			error = True

		if volume != self.volume:
			if not error:
				self.device_error_cnt = 0
				if self.source != self.AIRPLAY:
					self.volume = volume
			else:
				self.device_error_cnt += 1
				log.message("radio._getVolume audio device error " 
						+ str(volume), log.ERROR)

				if self.device_error_cnt > 10:	
					msg =  "Sound device error - Run select_audio.sh"
					log.message("radio._getVolume " + msg , log.ERROR)
					print msg
					self.audio_error = True	

		return self.volume

	def getVolume(self):
		increment = config.getVolumeIncrement()
		return self._getVolume()/increment

	# Check for volume change
	def volumeChanged(self):
		volumeChange = self.volumeChange
		self.volumeChange = False
		return volumeChange

	# Return the volume range
	def getVolumeRange(self):
		return config.getVolumeRange()

	# Set volume (Called from the radio client or external mpd client via getVolume())
	def setVolume(self,volume):
		range = config.getVolumeRange()
		log.message("radio.setVolume vol=" + str(volume)
				+ " (range 0-" + str(range) + ")",log.DEBUG)
		increment = config.getVolumeIncrement()
		volume = self._setVolume(volume * increment)
		return volume/increment

	# Set volume 0-100 (only called from in this class)
	def _setVolume(self,volume):
		if self.muted(): 
			self.unmute()
		else:
			if volume > 100:
				 volume = 100
			elif volume < 0:
				 volume = 0

			try:
				if volume != self.volume:
					log.message("radio._setVolume vol=" + str(volume),log.DEBUG)
					client.setvol(volume)
					self.volume = volume
					# Don't change stored volume (Needed for unmute function)
					if not self.muted():
						self.storeVolume(self.volume)
			except:
				log.message("radio._setVolume error vol=" + str(self.volume),log.ERROR)

		return self.volume

	# Increase volume 
	def increaseVolume(self):
		increment = config.getVolumeIncrement()
		volume = self.volume + increment
		log.message("radio.increaseVolume vol=" + str(volume),log.DEBUG)
		volume = self._setVolume(volume)
		return volume/increment

	# Decrease volume 
	def decreaseVolume(self):
		increment = config.getVolumeIncrement()
		volume = self.volume - increment
		log.message("radio.decreaseVolume vol=" + str(volume),log.DEBUG)
		volume = self._setVolume(volume)
		return volume/increment

	def mute(self):
		log.message("radio.mute streaming=" + str(self.streaming),log.DEBUG)
		try:
			if self.source == self.RADIO:
				client.stop() # Disconnect from stream
			elif self.source == self.PLAYER:
				client.pause(1) # Pause playing track
			elif self.source == self.AIRPLAY:
				airplay.muteMixer()
			self.isMuted = True
		except:
			log.message("radio.mute error",log.DEBUG)
		return

	# Unmute sound fuction, get stored volume
	def unmute(self):
		volume = 0
		if self.muted():
			try:
				if  self.source == self.AIRPLAY: 
					log.message("radio.unmute Airplay",log.DEBUG)
					airplay.unmuteMixer()
					volume = self.getMixerVolume()
				else:
					log.message("radio.unmute MPD",log.DEBUG)
					self.volume = self.getStoredVolume()
					log.message("radio.unmute volume=" 
						+ str(self.volume),log.DEBUG)
					client.play()
					client.setvol(self.volume)
					volume = self.volume

				# Unmute succesvol
				self.isMuted = False
			except:
				log.message("radio.unmute error",log.ERROR)
		return volume

	def muted(self):
		return self.isMuted

	# Get mixer volume
	def getMixerVolume(self):
		return airplay.getMixerVolume()
		
	# Increase mixer volume
	def increaseMixerVolume(self):
		return airplay.increaseMixerVolume()

	# Decrease mixer volume
	def decreaseMixerVolume(self):
		return airplay.decreaseMixerVolume()

	# Start MPD (Alarm mode)
	def startMPD(self):
		try:
			client.play()
		except:
			log.message("radio.startMPD error",log.ERROR)
		return

	# Stop MPD (Alarm mode)
	def stopMPD(self):
		try:
			client.stop()
		except:
			log.message("radio.stopMPD error",log.ERROR)
		return

	# Stop the radio and exit
	def exit(self):
		log.message("Stopping MPD",log.INFO)
		self.execCommand("sudo service mpd stop")
		if self.getSource() == self.AIRPLAY:
			self.stopAirplay()	
		radio.execCommand("sudo umount /media > /dev/null 2>&1")
		radio.execCommand("sudo umount /share > /dev/null 2>&1")
		log.message("Exiting radio",log.INFO)
		sys.exit(0)

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

	# Store mixer volume 
	def storeMixerVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + MixerVolumeFile)
		return

	# Random setting
	def getRandom(self):
		self.random = self.getStoredRandomSetting()
		return self.random

	def randomOn(self):
		try:
			self.random = True
			self.execCommand ("echo " + str(1) + " > " + RandomSettingFile)
			if self.source == self.PLAYER:
				client.random(1)
			else:
				client.random(0) # Off for radio
		except:
			log.message("radio.randomOn error",log.ERROR)
		log.message("radio.randomOn " + str(self.random),log.DEBUG)
		return self.random

	def randomOff(self):
		try:
			client.random(0)
			self.random = False
			self.execCommand ("echo " + str(0) + " > " + RandomSettingFile)
		except:
			log.message("radio.randomOff error",log.ERROR)
		log.message("radio.randomOn " + str(self.random),log.DEBUG)
		return self.random

	# Get the stored random setting 0=off 1=on
	def getStoredRandomSetting(self):
		random = 0
		if os.path.isfile(RandomSettingFile):
			try:
				random = int(self.execCommand("cat " + RandomSettingFile) )
			except ValueError:
				random = 0
		else:
			log.message("Error reading " + RandomSettingFile, log.ERROR)

		if random is 1:
			self.random = True
		else:
			self.random = False

		return self.random

	# Repeat
	def getRepeat(self):
		return self.repeat

	def repeatOn(self):
		try:
			client.repeat(1)
			self.repeat = True
		except:
			log.message("radio.repeatOn error",log.ERROR)
		return

	def repeatOff(self):
		try:
			client.repeat(0)
			self.repeat = False
		except:
			log.message("radio.repeatOff error",log.ERROR)
		return

	# Consume
	def getConsume(self):
		return self.consume

	def consumeOn(self):
		try:
			client.consume(1)
			self.consume = True
		except:
			log.message("radio.consumeOn error",log.ERROR)
		return

	def consumeOff(self):
		try:
			client.consume(0)
			self.consume = False
		except:
			log.message("radio.consumeOff error",log.ERROR)
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
		else:
			tstring = 'off'
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

	# Cycle through alarm types
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
		if self.alarmType > self.ALARM_LAST:
			self.alarmType = self.ALARM_OFF
		return  self.alarmType
		
	# Get the date format
	def getDateFormat(self):
		return config.getDateFormat()

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
		self.streaming = False
		if os.path.isfile(Icecast):
			self.execCommand("service icecast2 start")
			self.execMpcCommand("enable " + str(output_id))
			self.storeStreaming("on")
			self.streaming = True
			self.streamingStatus()
		return self.streaming

	# Switch off Icecast2 streaming
	def streamingOff(self):
		output_id = 2
		self.streaming = False
		if os.path.isfile(Icecast):
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
		#if self.speech and self.display_mode != self.MODE_SEARCH: 
		#	self.speakOption(self.option)
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

	# Set display mode from menu button or IR remote
	def setDisplayMode(self,display_mode):
		if self.display_mode >= 0:
			log.message("radio.setDisplayMode " + str(display_mode), log.DEBUG)
			self.display_mode = display_mode
		if self.speech:
			self.speakMenu(display_mode)
		return
	
	# Speak menu
	def speakMenu(self,display_mode):
		# Speak menu
		sMenu = language.getMenuText()
		if display_mode != self.MODE_SLEEP:
			msg = sMenu[display_mode]
			self.speak(msg)

		if display_mode is self.MODE_OPTIONS:
			if not self.reload:
				self.speakOption(self.option)

	# Speak option
	def speakOption(self,option):

		sYes = language.getText("yes") 
		sNo = language.getText("no") 
		sOn = language.getText("on") 
		sOff = language.getText("off") 
		sParam = sOff

		sOptions = language.getOptionText()
		sOption = sOptions[option]

		if option == self.RANDOM:
			if self.getRandom():
				sParam = sOn

		elif option == self.CONSUME:
			if self.getConsume():
				sParam = sOn

		elif option == self.REPEAT:
			if self.getRepeat():
				sParam = sOn

		#elif option == self.ALARM:

		elif option == self.STREAMING:
			if self.streaming:
				sParam = sOn

		elif option == self.RELOADLIB:
			if self.updateLib:
				sParam = sYes
			else:
				sParam = sNo

		elif option == self.TIMER:
			sOption = "Timer"
			sParam = self.getTimerString()
			sParam = sParam.replace(':', ' ')

		elif option == self.ALARM:
			sTypes = ['off', 'on', 'repeat', 'week days only']
			type = self.getAlarmType()
			sOption = "Alarm"
			sParam = sTypes[type]

		elif option == self.ALARMSETHOURS or self.ALARMSETMINS:
			sType,sHours,sMinutes = self.alarmTime.split(':')
			hours = int(sHours)
			minutes = int(sMinutes)
			sOption = "Hours"
			if option == self.ALARMSETMINS:
				sOption = "Minutes"
			sParam = '%d %02d' % (hours,minutes) 

		self.speak(sOption + ' ' + sParam)
		return

	# Cycle through the menu
	def cycleMenu(self):
		# If a reload has been issued return to TIME display
		if self.getReload():
			display_mode = self.MODE_TIME

		elif self.search_index+1 != self.current_id:
			self.current_id =  self.search_index+1
			self.play(self.current_id)
			display_mode = self.MODE_TIME
		else:
			display_mode = self.getDisplayMode() + 1
			if display_mode > self.mode_last:
				display_mode = self.MODE_TIME

		if self.optionChanged():
			display_mode = self.MODE_TIME
			self.optionChangedFalse()
		
		self.setDisplayMode(display_mode)
		return

	# Set any option you like here 
	def getOption(self):
		return self.option

	def setOption(self,option):
		log.message("radio.setOption option " + str(option), log.DEBUG)
		self.option = option
		self.speakOption(self.option)
		return
	
	# Set the menu restriction for radios without a display (retro_radio.py)
	def setLastMode(self,mode_last):
		if mode_last >= self.MODE_OPTIONS and mode_last <= self.MODE_LAST:
			self.mode_last = mode_last
		return self.mode_last

	# Set the options restriction for radios without a display (retro_radio.py)
	def setLastOption(self,option_last):
		if option_last >= self.REPEAT and option_last <= self.RELOADLIB:
			self.option_last = option_last
		return self.option_last


	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand via OS
	# Some commands are easier using mpc and don't have 
	# an effect adverse on performance
	def execMpcCommand(self,cmd):
		return self.execCommand(Mpc + " " + cmd)

	# Get the ID  of the currently playing track or station ID
	def getCurrentID(self):
		try:
			currentsong = self.getCurrentSong()
			currentid = int(currentsong.get("pos")) + 1

			# Only update if the Current ID has changed
			if self.current_id != currentid:
				log.message("radio.getCurrentID New ID " + str(currentid), log.DEBUG)
				self.current_id = currentid
				# Write to current ID file
				self.execCommand ("echo " + str(currentid) + " > " + self.current_file)
				self.getIdError = False
		except:
			if not self.getIdError:
				log.message("radio.getCurrentID failed", log.ERROR)
				self.getIdError = True

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
					log.message(self.errorStr, log.DEBUG)
				self.error = True
			else:
				# No error
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
			log.message("radio.setCurrentID reset to " + str(self.current_id), log.DEBUG)
		
		self.search_index = self.current_id - 1
		self.execCommand ("echo " + str(self.current_id) + " > " + self.current_file)
		name = self.getCurrentTitle()
		return

	# Get stats array
	def getStats(self):
		try:
			stats = client.status()
			self.stats = stats # Only if above call works
		except:
			log.message("radio.getStats failed", log.ERROR)

		self.getOptions(self.stats)	# Get options 
		return self.stats

	# Get current state (play or pause or stop) if changed externally 
	def getState(self):
		state = "play"
		try:
			stats = self.getStats()
			state = str(stats.get("state"))
		except:
			log.message("radio.getState failed", log.ERROR)
			self.connect(self.mpdport)
			state = self.state

		# Mute if pause or stop but not if there are no playlists
		if (state == "pause" or state == "stop") and self.current_id != 0:
			self.isMuted = True
		else:
			self.isMuted = False

		if self.source == self.AIRPLAY:
			self.isMuted = airplay.mixerIsMuted()

		self.state = state 
		return state

	# Get paused state (REDUNDANT)
	def paused(self):
		self.getState()
		return self.pause

	# Get current song information (Only for use within this module)
	def getCurrentSong(self):
		try:
			currentsong = client.currentsong()
			self.currentsong = currentsong
		except:
			# Try re-connect and status
			try:
				if self.connect(self.mpdport):
					currentsong = client.currentsong()
					self.currentsong = currentsong
			except:
				log.message("radio.getCurrentSong failed", log.ERROR)
		return self.currentsong

	# Get the currently playing radio station from mpd 
	# This is usually from "name" but some stations use the "title" field
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

		if self.display_playlist_number:
			name = name + ' (' + str(self.current_id) + ')'
		self.stationName = translate.escape(name)

		# Use name from the playlist as the station name
		if self.stationNamesSource == config.LIST :
			self.stationName = self.getStationName(self.current_id -1)

		return self.stationName

	# Get the title of the currently playing station or track from mpd 
	def getCurrentTitle(self):
		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
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


		if self.channelChanged: 
			self.channelChanged = False
			if config.verbose():
				if self.source == self.RADIO:
					sSource = "Station "
				else: 
					sSource = "Track "
				if self.speech: 
					self.speak(sSource + str(self.current_id) 
						+ ' ' + self.stationName)
		if title != self.stationTitle and len(title) > 0:
			log.message ("Title: " + str(title), log.DEBUG)	
			
		self.stationTitle = title
		return title

	# Get the currently playing radio station from mpd 
 	# Returns the same format as the mpc current command
	def getCurrentStation(self):
		name = self.getRadioStation()
		title = self.getCurrentTitle()
		if len(title) > 0:
			currentPlaying = name + ": " + title
		else:
			currentPlaying = name
		self.checkStatus()
		return currentPlaying

	# Get the name of the current artist mpd (Music library only)
	def getCurrentArtist(self):
		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
			title = translate.escape(title)
			artist = str(currentsong.get("artist"))
			if str(artist) == 'None':
				artist = "Unknown artist"
			self.artist = artist
		except:
			log.message ("radio.getCurrentArtist error", log.ERROR)	
		return self.artist

	# Get bit rate - aways returns 0 in diagnostic mode 
	def getBitRate(self):
		try:
			status = client.status()
			bitrate = int(status.get('bitrate'))
		except:
			bitrate = -1
		return bitrate

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
			try:
				client.next()
			except:
				log.message("radio.channelUp error", log.ERROR)
				
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
			try:
				client.previous()
			except:
				log.message("radio.channelDown error", log.ERROR)

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

	# Toggle source retained for compatibiility
	def toggleSource(self):
		return self.cycleSource(self.UP)

	# Toggle the input source (Reload is done when Reload requested)
	def cycleSource(self, direction):
		airplay = config.getAirplay()

		if direction == self.UP:
			self.source += 1	
		elif direction == self.DOWN:
			self.source -= 1	

		if self.source < self.RADIO:
			if airplay:
				self.source = self.AIRPLAY
			else:
				self.source = self.PLAYER

		elif self.source > self.AIRPLAY:
				self.source = self.RADIO

		elif self.source > self.PLAYER and not airplay:
				self.source = self.RADIO

		if self.source == self.RADIO:
			sSource = language.getText('source_radio')

		elif self.source == self.PLAYER:
			sSource = language.getText('source_media')

		elif self.source == self.AIRPLAY:
			sSource = language.getText('source_airplay')

		self.setReload(True)	
		log.message("Selected source " + sSource, log.DEBUG)

		if self.speech: 
			self.speak(sSource)

		return self.source

	# Load radio stations
	def loadStations(self):
		log.message("radio.loadStations", log.DEBUG)

		# Restore default volume and mixer settings
		airplay.setMixerPreset()
		self.volume = self.getStoredVolume()
		self._setVolume(self.volume)

		if self.speech: 
			self.speak(language.getText('loading_radio'))
		try:
			client.clear()
		except:
			log.message("radio.loadStations mpc clear error", log.ERROR)

		dirList = os.listdir(PlaylistsDirectory)
		dirList.sort()
		for fname in dirList:
			fname = fname.rstrip()
			if fname is "share":
				continue
			if os.path.isdir(fname):
				continue

			# MPD version 0.19 plus does not require extions such as m3u, pls
			if not self.use_playlist_extensions:
				try:
					fname,ext = fname.split('.')
				except:
					log.message("radio.loadStations missing file extension in" + fname, log.ERROR)
					continue

			log.message("load " + fname, log.DEBUG)
			try:
				client.load(fname)
			except:
				log.message("radio.loadStations failed " + fname, log.ERROR)

		if airplay.isRunning():
			self.stopAirplay()

		self.randomOff()
		self.consumeOff()
		self.repeatOff()
		self.playlist = self.createPlayList()
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)
		self.play(self.current_id)
		self.search_index = self.current_id - 1
		self.setSource(self.RADIO)
		return

	# Load music library 
	def loadMusic(self):
		log.message("radio.loadMusic", log.DEBUG)
		
		# Restore default volume and mixer settings
		airplay.setMixerPreset()
		self.volume = self.getStoredVolume()
		self._setVolume(self.volume)
		
		if self.speech: 
			self.speak(language.getText('loading_media'))
		self.execMpcCommand("stop")
		self.execMpcCommand("clear")
		directory = "/var/lib/mpd/music/"

		dirList=os.listdir(directory)
		dirList.sort()
		for fname in dirList:
			fname = fname.strip("\n")
			if os.path.isfile(directory+fname):
				continue
			path = directory +  fname
			nfiles = len(os.listdir(path))
			if nfiles > 0:
				cmd = "add \"" + fname + "\""
				log.message("radio.loadMusic " + cmd,log.DEBUG)
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
		self.loadMusic()
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
		try:
			client.play(self.current_id-1)
			self.checkStatus()
		except:
			log.message("radio.play error", log.ERROR)
		return

	# Clear streaming and other errors
	def clearError(self):
		log.message("radio.clearError", log.DEBUG)
		try:
			client.clearerror()
			self.errorStr = ""
			self.error = False 
		except:
			log.message("radio.clearError failed", log.ERROR)
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
			if line.startswith("http:") and '#' in line: 
				url,line = line.split('#')
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

	# Get Radio station name by Index (Used in search routines)
	def getStationName(self,index):
		station = ""
		if self.source == self.RADIO:
			station = "No stations found"
		else:
			station = "No tracks found"
		try:
			if len(self.playlist) > 0:
				station = self.playlist[index] 
		except:
			log.message("radio.getStationName bad index " + str(index), log.ERROR)
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

	# Get the the backlight color number (option = bg_color etc)
	def getBackColor(self,option):	
		return config.getBackColor(option)

	# Get the the backlight color number
	def getBackColorName(self,iColor):	
		return config.getBackColorName(iColor)

	# Cycle colors
	def cycleColor(self,direction):
		return config.cycleColor(direction)

	# Get I2C backpack type
	def getBackPackType(self):
		self.i2c_backpack = config.getBackPackType()
		log.message("Backpack type " + str(self.i2c_backpack), log.DEBUG)
		return self.i2c_backpack

	# Get I2C address
	def getI2Caddress(self):
		self.i2c_address = config.getI2Caddress()
		log.message("I2C address " + hex(self.i2c_address), log.DEBUG)
		return self.i2c_address

	# Set an interrupt received
	def setInterrupt(self):
		self.interrupt = True
		return

	# See if interrupt received from IR remote control
	def getInterrupt(self):
		interrupt = self.interrupt or airplay.getInterrupt()
		self.interrupt =  False
		return interrupt

	# Load media
	def loadMedia(self):
		log.message("radio.loadMedia", log.DEBUG)
		self.unmountAll()
		self.mountUsb()
		self.mountShare()
		if airplay.isRunning():
			self.stopAirplay()
		self.loadMusic()
		self.random = self.getStoredRandomSetting()
		self.setSource(self.PLAYER)
		return

	# Start Airlpay
	def startAirplay(self):
		self.execMpcCommand("stop")
		started = airplay.start()
		log.message("radio.startAirplay " + str(started), log.DEBUG)
		if started:
			self.setSource(self.AIRPLAY)
		else:
			log.message("radio.startAirplay FAILED" , log.ERROR)
			self.execMpcCommand("play")
		return

	# Stop Airlpay
	def stopAirplay(self):
		airplay.stop()
		return

	# Airplay information scrolling - decides which line to control
	def scrollAirplay(self):
		return airplay.scroll()

	# Get Airplay information
	def getAirplayInfo(self):
		return airplay.info()


	# Mount the USB stick
	def mountUsb(self):
		usbok = False
		if os.path.exists("/dev/sda1"):
			device = "/dev/sda1"
			usbok = True

		elif os.path.exists("/dev/sdb1"):
			device = "/dev/sdb1"
			usbok = True

		if usbok:
			self.execCommand("/bin/mount -o rw,uid=1000,gid=1000 "+ device + " /media")
			log.message(device + " mounted on /media", log.DEBUG)
			dirList=os.listdir(MusicDirectory)
			for fname in dirList:
				file = MusicDirectory + '/' + fname
				# Skip playlist files
				if os.path.isfile(file):
					continue
				log.message("Loading " + file, log.DEBUG)
		else:
			msg = "No USB stick found!"
			log.message(msg, log.WARNING)
		return


	# Mount any remote network drive
	def mountShare(self):
		if os.path.exists("/var/lib/radiod/share"):
			myshare = self.execCommand("cat /var/lib/radiod/share")
			if myshare[:1] != '#':
				self.execCommand(myshare)
				log.message(myshare,log.DEBUG)
		return

	# Unmount all drives
	def unmountAll(self):
		self.execCommand("sudo /bin/umount /dev/sda1 2>&1 >/dev/null")  # Unmount USB stick
		self.execCommand("sudo /bin/umount /dev/sdb1 2>&1 >/dev/null")  # Unmount USB stick
		self.execCommand("sudo /bin/umount /share 2>&1 >/dev/null")  # Unmount network drive
		return

	# Speak a message (Disabled if Airplay running - not compatible)
	def speak(self, msg):	
		if not airplay.isRunning():
			msg = msg.lstrip()
			if self.speech and len(msg) > 1:
				if msg[0] != '!':
					speech_volume = config.getSpeechVolume()
					volume = self.volume * speech_volume/100
					if volume < 5:
						volume = 5
					client.pause()
					language.speak(msg,volume)
					client.play()
		return

	# Speak a message
	def speakInformation(self):	
		log.message("radio.speakInformation" , log.DEBUG)
		msg = ''
		if self.source == self.RADIO:
			current = "Station " + str(self.current_id )
			name = self.getStationName(self.search_index)
			title = self.getCurrentTitle()
		else: 
			current = "Track " + str(self.current_id )
			name = self.getCurrentArtist()
			title = self.getCurrentTitle()

		sTime  = strftime("%H %M")
		time = language.getText('the_time') + " " + sTime
		self.speak(time)
		msg = current + ", " + name + ", " + title 
		self.speak(msg)
		return

	# Is speech enabled
	def speechEnabled(self):
		return self.speech

	# Get language text
	def getLangText(self,label):
		return language.getText(label)
	
	# Get switch  GPIO configuration
	def getSwitchGpio(self,label):
		return config.getSwitchGpio(label)

	# Get RGB LED GPIO configuration (Retro radio)
	def getRgbLed(self,label):
		return config.getRgbLed(label)

	# Get Menu swich values configuration (Retro radio)
	def getMenuSwitch(self,label):
		return config.getMenuSwitch(label)

	# Get rotary class
	def getRotaryClass(self):
		return config.getRotaryClass()

	# Get auto load player if no Internet True or False
	def autoload(self):
		return config.autoload()

	def dummy(self): 
		log.message("dummy" , log.DEBUG)
		return

	# Detect audio error
	def audioError(self):
		return self.audio_error

# End of Radio Class

### Test routine ###
if __name__ == "__main__":
	print "Test radio_class.py"
	radio = Radio()
	print "MPD version",radio.getMpdVersion() 
	radio.mountUsb()
	print  "Version",radio.getVersion()
	print "Board revision", radio.getBoardRevision()
	iColor = radio.getBackColor('bg_color')
	colorName = radio.getBackColorName(iColor)
	print 'bg_color',colorName, iColor

	# Start radio and load the radio stations
	backpack = radio.getBackPackType()
	print "Backpack", backpack
	i2c_address = radio.getI2Caddress()
	print "I2C address", hex(i2c_address)
	radio.start()
	radio.loadStations()
	radio.play(1)
	current_id = radio.getCurrentID()
	index = current_id - 1
	print "Current ID ", current_id 
	print "Station",current_id,":", radio.getStationName(index)
	print "Bitrate", radio.getBitRate()

	# Test volume controls
	print "Stored volume", radio.getStoredVolume()
	radio.setVolume(15)
	radio.increaseVolume()
	radio.decreaseVolume()
	radio.getVolume()
	time.sleep(5)
	print "Mute"
	radio.mute()
	time.sleep(3)
	print "Unmute"
	radio.unmute()
	print "Volume", radio.getVolume()
	time.sleep(5)
	# Test channel functions
	current_id = radio.channelUp()
	print "Channel up"
	index = current_id - 1
	print "Station",current_id,":", radio.getStationName(index)
	time.sleep(5)
	current_id = radio.channelDown()
	print "Channel down"
	index = current_id - 1
	print "Station",current_id,":", radio.getStationName(index)

	# Check library load
	print "Load music library"
	radio.loadMusic()

	# Check state
	print "State  " +  radio.getState()

	# Check timer
	print "Set Timer 1 minute"
	radio.storeTimer(1)
	radio.timerOn()

	while not radio.fireTimer():
		time.sleep(1)
	print "Timer fired"

	# Exit 
	print "Exit test"
	sys.exit(0)
	
# End of __main__ routine


