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
import config
import threading
import copy
from log_class import Log
from translate_class import Translate
from mpd import MPDClient
import mpd
import socket

def _(text): text

# System files
# RadioLibDir = "/var/lib/piradio"
# CurrentStationFile = RadioLibDir + "/current_station"
# CurrentTrackFile = RadioLibDir + "/current_track"
# VolumeFile = RadioLibDir + "/volume"
# TimerFile = RadioLibDir + "/timer" 
# AlarmFile = RadioLibDir + "/alarm" 
# StreamFile = RadioLibDir + "/streaming"
# MpdPortFile = RadioLibDir + "/mpdport"
# BoardRevisionFile = RadioLibDir + "/boardrevision"

log = Log()
translate = Translate()

#Mpd = "/usr/bin/mpd"	# Music Player Daemon
#Mpc = "/usr/bin/mpc"	# Music Player Client
client = MPDClient(use_unicode = True)	# Create the MPD client
client.timeout = None

class RadioState(threading.Thread):
        _playlist = None
        _state = None
        _state_time = 0
        _currentsong = None
        _outputs = None

        _client = None
        _lock = None

        _thread = None
        _running = False

        _callbacks = {
        }
        
        def __init__(self):
                super(RadioState,self).__init__(group=None)
                self._action_list = {
                        'database' : self.database_changed,
                        'update' : self.update_changed,
                        'stored_playlist' : self.stored_playlist_changed,
                        'playlist' : self.playlist_changed,
                        'player' : self.player_changed,
                        'mixer' : self.mixer_changed,
                        'output' : self.output_changed,
                        'options' : self.options_changed
                }
                self._lock = threading.Lock()
                self.connect()
                self.setDaemon(True)

        def addCallback(self,change,cb):
                if change in self._callbacks:
                        self._callbacks[change].append(cb)
                else:
                        self._callbacks[change]=[cb]
                log.message("added callback: " + unicode(self._callbacks),
                            log.DEBUG)
        
        
        def connect(self,callback=None):
                self._client = MPDClient(use_unicode = True)
                host = config.get("Server","host")
                port = config.get("Server","port")
                connection = False
		while not connection:
			try:
                                if callback:
                                        callback("Connect to MPD")
				self._client.timeout = None
				self._client.idletimeout = None
                                log.message("connecting to {0}:{1}".format(host,port),
                                            log.DEBUG)
                                log.message("types: {0}:{1}".format(type(host),type(port)),
                                            log.DEBUG)
				self._client.connect(host, str(port))
                                log.message("connected",log.DEBUG)
                                self._fetch_status()
                                self._fetch_playlist()
                                self._fetch_currentsong()
                                
                                if callback:
                                        callback("Connected")
				log.message("Connected to MPD at {0}:{1}".format(host,port), log.INFO)
				connection = True
			except Exception as e:
				log.message("Failed to connect to MPD on {0}:{1}".\
                                            format(config.get("Server","host"),
                                                   config.get("Server","port")),
                                            log.ERROR)
                                log.message(unicode(e),log.ERROR)
                                if callback:
                                        callback("Waiting for MPD")
                                connection = False
				time.sleep(2)	# Wait for interrupt in the case of a shutdown

                return connection

	# Execute MPC comnmand using mpd library - Connect client if required
	def execMpdCmd(self,cmd, repeat=True):
                log.message("locking connection",log.DEBUG)
                ok = False
                ret = None
                while repeat:
                        try:
                                log.message("executing command",log.DEBUG)
                                ret = cmd()
                                repeat = False
                        except mpd.ConnectionError:
                                log.message("execMpc: connection lost", log.ERROR)
                                try:
                                        client.disconnect()
                                except mpd.ConnectionError:
                                        pass
                                        if self.connect():
                                                ret = cmd()
                                repeat = False

                        except socket.timeout:
                                log.message("execMpc: connection timeout", log.ERROR)
                                client.timeout=client.timeout+60
                                try:
                                        client.disconnect()
                                except mpd.ConnectionError:
                                        pass
                                if self.connect():
                                        ret = cmd()
                        except:
                                self.connection_lock.release()
                                raise
                return ret


        def run(self):
                self._running = True
                while self._running:
                        changes = self.execMpdCmd(lambda: self._client.idle())
                        log.message("MPD state changed: " + unicode(changes),
                                    log.DEBUG)
                        for change in changes:
                                if change in self._action_list:
                                        self._action_list[change]()
                                else:
                                        log.message("Unknown MPD change: " + change,
                                                    log.WARNING)
                                if change in self._callbacks:
                                        for cb in self._callbacks[change]:
                                                cb()

        def _fetch_status(self):
                with self._lock:
                        self._state = self.execMpdCmd(lambda: self._client.status())
                        self._state_time = time.time()
                        log.message("MPD state: " + unicode(self._state),
                                    log.DEBUG)

        def update_status(self):
                self._fetch_status()

        def get_status(self):
                with self._lock:
                        return copy.deepcopy(self._state)

        def get_status_time(self):
                with self._lock:
                        return copy.deepcopy(self._state_time)

        def _fetch_currentsong(self):
                with self._lock:
                        self._currentsong = self.execMpdCmd(lambda: self._client.currentsong())
                        log.message("MPD current song: " + unicode(self._currentsong),
                                    log.DEBUG)

        def get_currentsong(self):
                with self._lock:
                        return copy.deepcopy(self._currentsong)

        def _fetch_playlist(self):
                with self._lock:
                        self._playlist = self.execMpdCmd(lambda: self._client.playlistinfo())
                        log.message("MPD current song: " + unicode(self._playlist),
                                    log.DEBUG)

        def get_playlist(self):
                with self._lock:
                        return copy.deepcopy(self._playlist)


        def _fetch_outputs(self):
                with self._lock:
                        self._outputs = self.execMpdCommand(lambda: client.outputs())
        def get_outputs(self):
                with self.lock:
                        return copy.deepcopy(self._outputs)
                                    
        def database_changed(self):
                return
        def update_changed(self):
                self._fetch_status()
                return
        def stored_playlist_changed(self):
                return
        def playlist_changed(self):
                self._fetch_status()
                self._fetch_playlist()
                self._fetch_currentsong()
                return
        def player_changed(self):
                self._fetch_status()
                self._fetch_currentsong()
                return
        def mixer_changed(self):
                self._fetch_status()
                return
        def output_changed(self):
                self._fetch_outputs()
                return
        def options_changed(self):
                self._fetch_status()
                return

        # queries
        def has_playlist(self):
                with self._lock:
                        return bool(len(self._playlist))

        def is_updating(self):
                with self._lock:
                        return 'updatings_db' in self._state

        def get_volume(self):
                with self._lock:
                        if 'volume' in self._state:
                                return self._state['volume']
                        else: return None

        def get_random(self):
                with self.lock:
                        if 'random' in self._state:
                                return bool(self._state['random'])
                        else: return None

        def get_repeat(self):
                with self.lock:
                        if 'repeat' in self._state:
                                return bool(self._state['repeat'])
                        else: return None
                
        def get_consume(self):
                with self.lock:
                        if 'consume' in self._state:
                                return bool(self._state['consume'])
                        else: return None

        def get_current_id(self):
                with self.lock:
                        if self._currentsong and \
                           'pos' in self._currentsong:
                                return int(self._currentsong['pos'])
                        else: return None
        def get_output(self,output_id):
                with self.lock:
                        for output in self._outputs:
                                if int(output['outputid']) == output_id:
                                        return output
                        return None
                
        def get_playlistlength(self):
                with self._lock:
                        return len(self._playlist)
                
class Radio:
        _radiostate = None
        
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
	error = False 	# Stream error handling
	errorStr = ""   # Error string
	updateLib = False    # Reload radio stations or player

	# Clock and timer options
	timer = False	  # Timer on
	timerValue = 30   # Timer value in minutes
	timeTimer = 0  	  # The time when the Timer was activated in seconds 

	alarmType = ALARM_OFF	# Alarm on
        alarmDay = 0     # Alarm time default type,hours,minutes
        alarmHour = 7
        alarmMinute = 0
	alarmTriggered = False	# Alarm fired

	search_index = 0	# The current search index
	streaming = False	# Streaming (Icecast) disabled
	VERSION	= "3.13-ts"	# Version number

        last_playlist = {
                'type':'radio',
                'path':None,
                'index':0
        }
        mute_volume = 0

        connection_lock = threading.Lock()

	def __init__(self):
		log.init('radio')
                self._radiostate = RadioState()
                self._playlist_types = {
                        'playlist'  : self.load_playlist,
                        'directory' : self.load_directory,
                        'radio'     : lambda (dummy): self.load_radio()
                }

	# Start the MPD daemon
	def start(self, callback=None):
		# Start the player daemon
		#self.execCommand("service mpd start")
		# Connect to MPD
                self._radiostate.start()
		self.boardrevision = self.getBoardRevision()
		self.mpdport = self.getMpdPort()
		self.connect(callback)

                port = config.get("Server","port")                
		self.timeTimer = int(time.time())
		self.timerValue = self.getStoredTimer()
		self.streaming = self.getStoredStreaming()
		self.setStreaming(self.streaming)

                if not self._radiostate.has_playlist():
                        volume = self.getStoredVolume()
                        self.setVolume(volume)
                        self.setRandom(config.libget_boolean("Settings","random"))
                        last_playlist = {}
                        last_playlist['type']  = config.libget("Current Track",
                                                               "type")
                        last_playlist['path']  = config.libget("Current Track",
                                                               "path")
                        last_playlist['index'] = config.libget("Current Track",
                                                               "index")
                        last_update = self._radiostate.get_status_time()
                        self._playlist_types[last_playlist['type']](last_playlist['path'])
                        while last_update >= self._radiostate.get_status_time():
                                time.sleep(0.001)
                        self.play(last_playlist['index'])
		return

	def connect(self,callback=None):
		global client
		connection = False
                host = config.get("Server","host")
                port = config.get("Server","port")
		while not connection:
			try:
                                if callback:
                                        callback("Connect to MPD")
				client.timeout = 60
				client.idletimeout = None
                                log.message("connecting to {0}:{1}".format(host,port),
                                            log.DEBUG)
                                log.message("types: {0}:{1}".format(type(host),type(port)),
                                            log.DEBUG)
				client.connect(host, str(port))
                                log.message("connected",log.DEBUG)
                                client.status() # do something to ensure the server is online
                                if callback:
                                        callback("Connected")
				log.message("Connected to MPD at {0}:{1}".format(host,port), log.INFO)
				connection = True
			except Exception as e:
				log.message("Failed to connect to MPD on {0}:{1}".\
                                            format(config.get("Server","host"),
                                                   config.get("Server","port")),
                                            log.ERROR)
                                log.message(unicode(e),log.ERROR)
                                if callback:
                                        callback("Waiting for MPD")
                                connection = False
				time.sleep(2)	# Wait for interrupt in the case of a shutdown

                return connection


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
                try:
                        port = int(config.get("Server","port") )
                except:
                        port = 6600
			log.message("Error reading mpd port", log.ERROR)

		return port

	def getVolume(self):
                return self._radiostate.get_volume()

	# Set volume (Called from the radio client or external mpd client via getVolume())
	def setVolume(self,volume):
                self.execMpc(lambda: client.setvol(volume))
                if (volume): self.storeVolume(volume)
		return


	# Increase volume 
	def increaseVolume(self, count = 1):
		if self.muted(): 
			self.unmute()
                volume = self.getVolume()
                volume = volume + count
                setVolume(volume)
                return self.volume

	# Decrease volume 
	def decreaseVolume(self, count = 1):
		if self.muted(): 
			self.unmute()
                volume = self.getVolume()
                volume = volume - count
                setVolume(volume)
                return self.volume

	# Mute sound functions (Also stops MPD if not streaming)
	def mute(self):
		log.message("radio.mute streaming=" + str(self.streaming),log.DEBUG)
                if not self.streaming:
                        self.doPause()
		self.execMpc(lambda: client.setvol(0))
		return

	# Unmute sound fuction, get stored volume
	def unmute(self):
		volume = self.getStoredVolume()
		log.message("radio.unmute volume=" + str(self.volume),log.DEBUG)
                self.setVolume(volume)
                self.doPlay()
		return volume

	def muted(self):
		return bool(self.getVolume())

	# Get the stored volume
	def getStoredVolume(self):
		volume = 75
                try:
                        volume = int(config.libget('Settings','volume'))
                except:
                        volume = 75
			log.message("Error reading volume", log.ERROR)

		return volume

	# Store volume in volume file
	def storeVolume(self,volume):
		config.libset('Settings','volume',str(volume))
                config.save_libconfig()
                config.save_libconfig()
		return

	# Random
	def getRandom(self):
		return self._radiostate.get_random()

	def setRandom(self, value):
		self.execMpc(lambda: client.random(int(value)))
                config.libset('Settings','random',str(value))
                config.save_libconfig()
		return

	# Repeat
	def getRepeat(self):
		return self._radiostate.get_repeat()

	def setRepeat(self, value):
		self.execMpc(lambda: client.repeat(value))
                config.libset('Settings','repeat',value)
                config.save_libconfig()
		return

	# Consume
	def getConsume(self):
		return self._radiostate.get_consume()

	def setConsume(self, value):
		self.execMpc(lambda: client.consume(value))
                config.libset('Settings','consume',value)
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
                self.storeTimer(timerValue)
		return self.timerValue

	def decrementTimer(self,dec):
		if self.timerValue > 120:
			dec = 10
		self.timerValue -= dec
		if self.timerValue < 0:
			self.timerValue = 0	
			self.timer = False
		self.timeTimer = int(time.time())
                self.storeTimer(timerValue)
		return self.timerValue

	# Get the stored timer value
	def getStoredTimer(self):
		timerValue = 0
                try:
                        timerValue = int(config.libget("Settings",'timer'))
                except:
                        timerValue = 30
                        log.message("Error reading Timer", log.ERROR)
                return timerValue

	# Store timer time in timer file
	def storeTimer(self,timerValue):
                config.libset("Settings",'timer',str(timerValue))
                config.save_libconfig()
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
                try:
                        alarmType = config.libget('Settings','alarm_type')
                except:
                        alarmType = 0
			log.message("Error reading alarm day", log.ERROR)
                try:
                        alarmHour = config.libget('Settings','alarm_hour')
                except:
                        alarmHour = 7
			log.message("Error reading alarm hour", log.ERROR)
                try:
                        alarmMinute = config.libget('Settings','alarm_minute')
                except:
                        alarmMinute = 0
			log.message("Error reading alarm day", log.ERROR)
                return

	# Store alarm time in alarm file
	def storeAlarm(self,alarmString):
                config.libset('Settings','alarm_type',unicode(self.alarmType))
                config.libset('Settings','alarm_hour',unicode(self.alarmHour))
                config.libset('Settings','alarm_minute',unicode(self.alarmMinute))
                config.save_libconfig()
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
                try:
                        streaming = config.libget_boolean('Settings',
                                                          'streaming')
                except Exception as e:
			streaming = False	
			log.message("Error reading streaming parameter: "
                                    + unicode(e), log.ERROR)
		return streaming

	# Toggle streaming on off
	# Stream number is 2 
	def toggleStreaming(self):
		return self.setStreaming(not self.getStreaming())

        def setStreaming(self, on = True):
                if self.streamingAvailable():
                        output_id = 2
                        if on:
                                self.execCommand("service icecast2 start")
                        else:
                                self.execCommand("service icecast2 stop")
                        output = self._radiostate.get_output(output_id)
                        if output:
                                self.execMpc(lambda: client.enableoutput(output_id))
		self.storeStreaming("on")
		return

	# Display streaming status
	def getStreaming(self):
                return self._radiostate.get_output(output_id)

	# Check if icecast streaming installed
	def streamingAvailable(self):
		fpath = "/usr/bin/icecast2"
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	# Store stram on or off in streaming file
	def storeStreaming(self,onoff):
                config.libset('Settings','streaming',onoff)
                config.save_libconfig()
		return
	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand using mpd library - Connect client if required
	def execMpc(self,cmd, repeat=True):
                log.message("locking connection",log.DEBUG)
                self.connection_lock.acquire()
                ok = False
                ret = None
                while repeat:
                        try:
                                log.message("executing command",log.DEBUG)
                                ret = cmd()
                                repeat = False
                        except mpd.ConnectionError:
                                log.message("execMpc: connection lost", log.ERROR)
                                try:
                                        client.disconnect()
                                except mpd.ConnectionError:
                                        pass
                                        if self.connect():
                                                ret = cmd()
                                repeat = False

                        except socket.timeout:
                                log.message("execMpc: connection timeout", log.ERROR)
                                client.timeout=client.timeout+60
                                try:
                                        client.disconnect()
                                except mpd.ConnectionError:
                                        pass
                                if self.connect():
                                        ret = cmd()
                        except:
                                self.connection_lock.release()
                                raise
                self.connection_lock.release()
                return ret

        def getCurrentId(self):
                return self._radiostate.get_current_id()

	# Get the ID  of the currently playing track or station ID
	def getCurrentSong(self):
                return self._radiostate.get_currentsong()

	# Check to see if an error occured
	def gotError(self):
		return self.error

	# Get the error string if a bad channel
	def getErrorString(self):
		self.error = False
		return self.errorStr

	# Get stats array
	def getStatus(self):
                return self._radiostate.get_status()


	# Get current song information (Only for use within this module)
	def getCurrentSong(self):
                return self._radiostate.get_currentsong()

	# Get the last ID stored in /var/lib/radiod
	def getStoredID(self,current_file):
                current_id = config.libget('Current Track','id')

		if current_id <= 0:
			current_id = 1
		return current_id

	# Change radio station up
	def channelUp(self):
		new_id = self.getCurrentID() + 1
		log.message("radio.channelUp " + str(new_id), log.DEBUG)
		if new_id > len(self.playlist):
			new_id = 0
			self.play(new_id)
		else:
			self.execMpc(lambda: client.next())
				
		return new_id

	# Change radio station down
	def channelDown(self):
		new_id = self.getCurrentID() - 1
		log.message("radio.channelDown " + str(new_id), log.DEBUG)
		if new_id < 0:
			new_id = len(self.playlist) - 1
			self.play(new_id)
		else:
			self.execMpc(lambda: client.previous())

		return new_id

	# Load radio stations
	def startRadio(self):
		log.message("radio.loadStations", log.DEBUG)
                self.load_radio()
		self.randomOff()
		self.consumeOff()
		self.repeatOff()
                log.message("This is somehow wrong: We must store also the menu path",
                            log.ERROR)
		self.current_id = config.libget('Radio','current')
		self.play(self.current_id)
		self.search_index = self.current_id - 1
		return
        
        def load_radio(self):
		self.execMpc(lambda: client.clear())
                try:
                        self.execMpc(lambda: client.load(_("Radio")))
                except:
                        log.message("Failed to load Radio playlist",
                                    log.WARNING)


        def listNode(self,path):
                try:
                        retval =  self.execMpc(lambda: client.lsinfo(path))
                except mpd.CommandError as error:
                        retval = []
                return retval
                
	# Load music library 
#	def loadMusic(self):
#                return
# 		log.message("radio.loadMusic", log.DEBUG)
# 		self.execMpcCommand("stop")
# 		self.execMpcCommand("clear")
# 		directory = "/var/lib/mpd/music/"
# 
# 		dirList=os.listdir(directory)
# 		for fname in dirList:
# 			fname = fname.strip("\n")
# 			path = directory +  fname
# 			nfiles = len(os.listdir(path))
# 			if nfiles > 0:
# 				cmd = "add \"" + fname + "\""
# 				log.message(cmd,log.DEBUG)
# 				log.message(str(nfiles) + " files/directories found",log.DEBUG)
# 				try:
# 					self.execMpcCommand(cmd)
# 				except:
# 					log.message("Failed to load music directory " + fname, log.ERROR)
# 			else:
# 				log.message(path + " is empty", log.INFO)
# 
# 		self.playlist = self.createPlayList()
# 		self.current_file = CurrentTrackFile
# 		self.current_id = self.getStoredID(self.current_file)
# 
# 		# Old playlists may have been longer.
# 		length = len(self.playlist)
# 		if self.current_id > length:
# 			self.current_id = 1
# 			log.message("radio.loadMusic ID " + str(self.current_id), log.DEBUG)
# 
# 		# Important use mpc not python-mpd calls as these give problems
# 		if length > 0:
# 			log.message("radio.loadMusic play " + str(self.current_id), log.DEBUG)
# 			self.execMpcCommand("play " + str(self.current_id))
# 			self.search_index = self.current_id - 1
# 			self.execMpcCommand("random on")
# 			self.execMpcCommand("repeat off")
# 			self.execMpcCommand("consume off")
# 			self.random = True  # Random play
# 			self.repeat = False  # Repeat play
# 			self.consume = False # Consume tracks
# 		else:
# 			log.message("radio.loadMusic playlist length =  " + str(length), log.ERROR)
# 
# 		log.message("radio.loadMusic complete", log.DEBUG)
#		return length

	# Update music library 
	def updateLibrary(self):
		log.message("radio.updateLibrary", log.DEBUG)
		self.execMpc(lambda: client.update())
		return

        def changePlaylist(self,path):
                self.load_playlist(path)
                config.libset("Current Track","type",'playlist');
                config.libset("Current Track","path",path);
                return;

        def load_playlist(self,node):
                self.execMpc(lambda: client.clear())
                try:
                        self.execMpc(lambda: client.load(_("Radio")))
                except:
                        log.message("Failed to load Radio playlist",
                                    log.WARNING)
                return

        # change into a directory
        def changeDir(self, path):
                log.message("radio.changeDir: " + path, log.DEBUG)
                config.libset("Current Track","type",'path');
                config.libset("Current Track","path",path);
                return self.load_directory(path);

        def load_directory(self,path):
                self.execMpc(lambda: client.clear())
                try:
                        return self.execMpc(lambda: client.add(path))
                except:
                        log.message("Failed to load Radio playlist",
                                    log.WARNING)
                return None

                
        def playNode(self,node):
                if 'file' in node:
                        index = 0
                        for i in self.getPlayList():
                                index += 1
                                if 'file' in i:
                                        if i['file'] == node['file']:
                                                self.play(index)
                                                return
                play(0)

        def doPlay(self):
                self.play(self.getCurrentID())

        def doStop(self):
                self.execMpc(lambda: client.stop())

        def doPause(self):
                res = self.execMpc(lambda: client.pause())
                log.message("pause: " + unicode(res), log.DEBUG)

	# Play a track number  (Starts at 1)
	def play(self,number):
                maxnumber = self._radiostate.get_playlistlength()
                if not maxnumber:
                        return;
		log.message("radio.play " + str(number), log.DEBUG)
		if number < 0 or \
                   number >= maxnumber :
			log.message("play invalid station/track number "+ str(number), log.ERROR)
                        number = 0

		# Client play function starts at 0 not 1
		log.message("play station/track number "+ str(number), log.DEBUG)
		self.execMpc(lambda: client.play(number + 1))
		return

	# Clear streaming and other errors
	def clearError(self):
		log.message("clearError()", log.DEBUG)
		self.execMpc(lambda: client.clearerror())
		self.errorStr = ""
		self.error = False 
		return

        def addToStoredPlaylist(self,path,list_path):
                log.message("addtostoredplaylist", log.DEBUG)
                self.execMpc(lambda: client.playlistadd(list_path,path))

        def listPlaylists(self,path):
                return self.execMpc(lambda: client.listplaylists())

        def listPlaylist(self,path):
                return self.execMpc(lambda: client.listplaylistinfo(path))


	# Get list of tracks or stations
	def getPlayList(self):
		return self._radiostate.get_playlist()

	# Get the length of the current list
	def getListLength(self):
		return self._radiostae.get_playlist_length()

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
	def getStation(self,index):
                station = { 'message': _("Empty playlist.") }
                if len(self.playlist) > index:
			station = self.playlist[index] 
                return station
	
	# Version number
	def getVersion(self):
		return self.VERSION

        def getMpdVersion(self):
                return self.execMpc(lambda: client.mpd_version)

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


