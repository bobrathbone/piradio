#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.128 2014/10/14 17:59:34 bob Exp $
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
import inspect
import traceback
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

def radioStateUpdater(state):
        log.message("radioStateUpdater: " + unicode(state),
                    log.DEBUG)
        while True:
                time.sleep(state._check_interval)
#                log.message("radioStateUpdater",log.DEBUG)
                if state._terminate:
                        state._terminate += 1
                        state.unidle()
                        return
                state.update()

class RadioState(threading.Thread):
        _radio = None

        _playlist = None
        _playlist_time = 0
        _state = None
        _state_time = 0
        _check_interval = 0.1
        _update_interval = 10
        _currentsong = None
        _outputs = None

        _client = None
        _update_client = None
        _lock = None
        _change_lock = None
        _changed = {}

        _thread = None
        _terminate = 0 # 1 stop updater, 2 return
        _running = False

        _callbacks = {
        }

        callback_init = {
                'status'          : 'update_status',
                'database'        : 'database_changed',
                'update'          : 'update_changed',
                'stored_playlist' : 'stored_playlist_changed',
                'playlist'        : 'playlist_changed',
                'player'          : 'player_changed',
                'mixer'           : 'mixer_changed',
                'output'          : 'output_changed',
                'options'         : 'options_changed'
        }
        def __init__(self):
                super(RadioState,self).__init__(group=None,name="MPD-idle")
                for key in RadioState.callback_init:
                        value = RadioState.callback_init[key]
                        self.addCallback(key,getattr(self,value))
                self._lock = threading.Lock()
                self._change_lock = threading.Lock()
                self.setDaemon(True)
                self._thread = threading.Thread(name="MPD-updater",
                                                group = None,
                                                target=radioStateUpdater,
                                                args=(self,))

        def start(self):
                self._client = self.connect()
                self._update_client = self.connect()
                self._fetch_status()
                self._fetch_playlist()
                self._fetch_currentsong()
                self._thread.start()
                super(RadioState,self).start()

        def run(self):
                self._running = True
                while self._running:
                        if self._terminate:
                                _thread.join()
                                return
                        changes = self.execMpdCmd(self._client,lambda(client): client.idle())
                        log.message("RadioState changed: " + unicode(changes),
                                    log.DEBUG)
                        if changes:
                                with self._change_lock:
                                        for change in changes:
                                                self._changed[change] = True

        def addCallback(self,change,cb):
                if change in self._callbacks:
                        self._callbacks[change].append(cb)
                else:
                        self._callbacks[change]=[cb]
                log.message("added callback: " + unicode(self._callbacks),
                            log.DEBUG)

        def get_callbacks(self):
                return self._callbacks
        
        
        def connect(self):
                client = MPDClient(use_unicode = True)
                host = config.get("Server","host")
                port = config.get("Server","port")
                connection = False
		while not connection:
			try:
				client.timeout = None
				client.idletimeout = None
                                log.message("connecting to {0}:{1}".format(host,port),
                                            log.DEBUG)
                                log.message("types: {0}:{1}".format(type(host),type(port)),
                                            log.DEBUG)
				client.connect(host, str(port))
                                log.message("connected",log.DEBUG)
                                
				log.message("Connected to MPD at {0}:{1}".format(host,port), log.INFO)
				connection = True
			except Exception as e:
				log.message("Failed to connect to MPD on {0}:{1}".\
                                            format(config.get("Server","host"),
                                                   config.get("Server","port")),
                                            log.ERROR)
                                log.message(unicode(e),log.ERROR)
                                connection = False
				time.sleep(2)	# Wait for interrupt in the case of a shutdown

                return client

	# Execute MPC comnmand using mpd library - Connect client if required
	def execMpdCmd(self,client, cmd, repeat=True):
                log.message("RadioState: execMpdCmd ({0},{1})".
                            format(inspect.getsource(cmd),repeat),log.DEBUG)
                if not client:
                        log.message("Client not set", log.ERROR)
                        log.message(string.join(traceback.format_stack()),log.ERROR)
                ok = False
                ret = None
                while repeat and not ok:
                        try:
                                log.message("RadioState: executing command",
                                            log.DEBUG)
                                ret = cmd(client)
                                ok = True
                        except mpd.ConnectionError:
                                log.message("RadioState: connection lost",
                                            log.WARNING)
                                try:
                                        client.disconnect()
                                        log.message("RadioState: connection was active",
                                                    log.ERROR)
                                except mpd.ConnectionError:
                                        pass
                                ok = False

                        except socket.timeout:
                                log.message("RadioState: connection timeout",
                                            log.ERROR)
                                client.timeout=client.timeout+60
                                try:
                                        client.disconnect()
                                except mpd.ConnectionError:
                                        pass
                                ok = False

                        except socket.error, e:
				log.message("Connection to MPD lost: ".\
                                            str(e),
                                            log.ERROR)
                                if isinstance(e.args, tuple):
                                        if e[0] == errno.EPIPE:
                                                try:
                                                        client.disconnect()
                                                except mpd.ConnectionError:
                                                        pass
                                                ok = False
                                        else:
                                                # determine and handle different error
                                                pass
                                else:
                                        client.disconnect()
                                break

                log.message("RadioState: execMpdCmd end", log.DEBUG)
                return ret

        def unidle(self):
                self.execMpdCmd(self._client,lambda(client): client.unidle())


        def update(self):
                do_repeat = True
                with self._change_lock:
                        while do_repeat:
                                do_repeat = False
                                if (self._state_time + self._update_interval < time.time()):
                                        self._changed['status'] = True
                                try : 
                                        for change in self._changed:
                                                if self._changed[change]:
                                                        if change in self._callbacks:
                                                                self._change_lock.release()
                                                                try:
                                                                        for cb in self._callbacks[change]:
                                                                                cb()

                                                                except Exception as e:
                                                                        self._change_lock.acquire()
                                                                        raise

                                                                self._change_lock.acquire()
                                                        else:
                                                                log.message("Unknown MPD change: " + change,
                                                                    log.WARNING)
                                                        self._changed[change] = False
                                except RuntimeError as e:
                                        do_repeat=True
                                        log.message(unicode(e),log.ERROR)
                                        log.message(string.join(traceback.format_stack()),log.ERROR)

        def _fetch_status(self):
                with self._lock:
                        self._state = self.execMpdCmd(self._update_client,
                                                      lambda(client): client.status())
                        self._state_time = time.time()
                        log.message("MPD state: " + unicode(self._state),
                                    log.DEBUG)

                        if 'song' in self._state:
                                songid = int(self._state['song'])
                        else:
                                songid = None

                if songid is not None:
                        oldsong = config.libget('Current Track',
                                                'id')
                        oldsong = int(oldsong) if oldsong != 'None' else None

                        if songid != oldsong:
                                config.libset('Current Track',
                                              'id',
                                              str(songid))
                                config.save_libconfig()

        def update_status(self):
                self._fetch_status()

        def get_status(self):
                with self._lock:
                        return copy.deepcopy(self._state)

        def get_status_time(self):
                with self._lock:
                        return copy.deepcopy(self._state_time)

        def get_status_field(self,field):
                with self._lock:
                        if field in self._state:
                                return copy.deepcopy(self._state[field])
                        else: return None

        def _fetch_currentsong(self):
                with self._lock:
                        self._currentsong = self.execMpdCmd(self._update_client,
                                                            lambda(client): client.currentsong())
                        log.message("MPD current song: " + unicode(self._currentsong),
                                    log.DEBUG)

        def get_currentsong(self):
                with self._lock:
                        return copy.deepcopy(self._currentsong)

        def _fetch_playlist(self):
                with self._lock:
                        self._playlist = self.execMpdCmd(self._update_client,
                                                         lambda(client): client.playlistinfo())
                        self._playlist_time = time.time()
                        log.message("MPD current song: " + unicode(self._playlist),
                                    log.DEBUG)

        def get_playlist(self):
                with self._lock:
                        return copy.deepcopy(self._playlist)
                
        def get_playlist_time(self):
                with self._lock:
                        return copy.deepcopy(self._playlist_time)

        def get_playlist_entry(self,index):
                with self._lock:
                        if index < 0 or index >= len(self._playlist):
                                return None
                        return copy.deepcopy(self._playlist[index])

        def _fetch_outputs(self):
                with self._lock:
                        self._outputs = self.execMpdCmd(self._update_client,
                                                        lambda(client): client.outputs())
        def get_outputs(self):
                with self._lock:
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

        def force_volume(self,volume):
                with self._lock:
                        if self._state is not None:
                                self._state['volume'] = volume

        def get_random(self):
                with self._lock:
                        if 'random' in self._state:
                                return bool(int(self._state['random']))
                        else: return None

        def get_repeat(self):
                with self._lock:
                        if 'repeat' in self._state:
                                return bool(int(self._state['repeat']))
                        else: return None
                
        def get_consume(self):
                with self._lock:
                        if 'consume' in self._state:
                                return bool(int(self._state['consume']))
                        else: return None

        def get_current_id(self):
                with self._lock:
                        if self._currentsong and \
                           'pos' in self._currentsong:
                                return int(self._currentsong['pos'])
                        else: return None
        def get_output(self,output_id):
                with self._lock:
                        if not self._outputs: return None
                        for output in self._outputs:
                                if int(output['outputid']) == output_id:
                                        return output
                        return None

        def get_playlistlength(self):
                with self._lock:
                        if 'playlistlength' in self._state:
                                return int(self._state['playlistlength'])
                        else: return None

        def get_elapsed_time(self):
                with self._lock:
                        if 'elapsed' in self._state:
                                return float(self._state['elapsed']) \
                                        + time.time() - self._state_time
                        else: return None
                                

                
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
                'id':0
        }
        mute_volume = 0

        connection_lock = threading.Lock()

	def __init__(self):
		log.init('radio')
                self._radiostate = RadioState()
                self._playlist_types = {
                        'playlist'  : lambda(path): self.loadPlaylist(path,True),
                        'directory' : self.changeDir,
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
                        last_playlist['id'] = config.libget("Current Track",
                                                               "id")
                        last_update = self._radiostate.get_status_time()
                        log.message("last playlist: " + unicode(last_playlist),
                                    log.DEBUG)
                        log.message("_playlist_types: " + unicode(self._playlist_types),
                                    log.DEBUG)
                        self._playlist_types[last_playlist['type']](last_playlist['path'])
                        while last_update >= self._radiostate.get_status_time():
                                time.sleep(0.001)
                        self.play(last_playlist['id'])
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

        def addUpdateCallback(self, change, callback):
                self._radiostate.addCallback(change, callback)

        def getUpdateCallbacks(self):
                return self._radiostate.get_callbacks(self)

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
                vol = self._radiostate.get_volume()
                log.message("Volume got: {0}".format(vol),
                            log.DEBUG)
                return int(vol)

	# Set volume (Called from the radio client or external mpd client via getVolume())
	def setVolume(self,volume):
                self._radiostate.force_volume(volume)
                self.execMpc(lambda: client.setvol(volume))
                if (volume): self.storeVolume(volume)
		return


	# Increase volume 
	def increaseVolume(self, count = 1):
		if self.muted(): 
			self.unmute()
                volume = int(self.getVolume())
                volume = volume + count
                self.setVolume(volume)
                return volume

	# Decrease volume 
	def decreaseVolume(self, count = 1):
		if self.muted(): 
			self.unmute()
                volume = int(self.getVolume())
                volume = volume - count
                self.setVolume(volume)
                return volume

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
		log.message("radio.unmute volume=" + str(volume),log.DEBUG)
                self.setVolume(volume)
                self.doPlay()
		return volume

	def muted(self):
		return not bool(self.getVolume())

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
		self.execMpc(lambda: client.repeat(int(value)))
                config.libset('Settings','repeat',str(value))
                config.save_libconfig()
		return

	# Consume
	def getConsume(self):
		return self._radiostate.get_consume()

	def setConsume(self, value):
		self.execMpc(lambda: client.consume(int(value)))
                config.libset('Settings','consume',str(value))
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
		
		self.storeAlarm()
		return

	# Switch off the alarm unless repeat or days of the week
	def alarmOff(self):
		if self.alarmType == self.ALARM_ON:
			self.alarmType = self.ALARM_OFF
		return self.alarmType

	# Increment alarm time
	def incrementAlarm(self,inc):
                self.alarmMinute -= inc
		if self.alarmMinute > 60:
                        (hours,minutes) = divmod(self.alarmMinute,60)
			self.alarmMinute = minutes
                        self.alarmHour += hours
		if self.alarmHour > 23:
			self.alarmHour = 0
		self.storeAlarm()

	# Decrement alarm time
	def decrementAlarm(self,dec):
                self.alarmMinute -= dec
		if self.alarmMinute < 0:
                        (hours,minutes) = divmod(-self.alarmMinute,60)
			self.alarmMinute = 60 - minutes
                        if minutes:
                                self.alarmHour -= hours + 1
                        else:
                                self.alarmHour -= hours
		if self.alarmHour < 0:
			self.alarmHour = 23
		self.storeAlarm()
		return

	# Fire alarm if current hours/mins matches time now
	def alarmFired(self):

		fireAlarm = False
		if self.alarmType > self.ALARM_OFF:
			sType,sHours,sMinutes = self.alarmTime.split(':')
			t1 = datetime.datetime.now()
			t2 = datetime.time(self.alarmHour, self.alarmMinute)
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
	def storeAlarm(self):
                config.libset('Settings','alarm_type',unicode(self.alarmType))
                config.libset('Settings','alarm_hour',unicode(self.alarmHour))
                config.libset('Settings','alarm_minute',unicode(self.alarmMinute))
                config.save_libconfig()
		return

	# Get the actual alarm time
	def getAlarmTime(self):
                if self.alarmDay:
                        return '{0}d {1}:{2}'.format(self.alarmDay,
                                                     self.alarmHour,
                                                     self.alarmMinute)
                else:
                        return '{0}:{1}'.format(self.alarmHour,
                                                self.alarmMinute)
		
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
                                if on:
                                        self.execMpc(lambda: client.enableoutput(output_id))
                                else: 
                                        self.execMpc(lambda: client.disableoutput(output_id))
		self.storeStreaming(on)
		return

	# Display streaming status
	def getStreaming(self):
                output_id = 2
                return self._radiostate.get_output(output_id)

	# Check if icecast streaming installed
	def streamingAvailable(self):
		fpath = "/usr/bin/icecast2"
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	# Store stram on or off in streaming file
	def storeStreaming(self,onoff):
                config.libset('Settings','streaming',str(onoff))
                config.save_libconfig()
		return
	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand using mpd library - Connect client if required
	def execMpc(self,cmd, repeat=True):
                log.message("Radio: execMpc ({0},{1})".
                            format(inspect.getsource(cmd),repeat),log.DEBUG)
                with self.connection_lock:
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
                                except socket.error, e:
                                        log.message("Connection to MPD lost: ".\
                                                    str(e),
                                                    log.ERROR)
                                        if isinstance(e.args, tuple):
                                                if e[0] == errno.EPIPE:
                                                        try:
                                                                client.disconnect()
                                                        except mpd.ConnectionError:
                                                                pass
                                                        ok = False
                                                else:
                                                        # determine and handle different error
                                                        pass
                                        else:
                                                client.disconnect()
                                        break

                log.message("Radio: execMpc end", log.DEBUG)
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
        def getStatusTime(self):
                return self._radiostate.get_status_time()
        def getStatusField(self,field):
                return self._radiostate.get_status_field(field)
        def getElapsedTime(self):
                return self._radiostate.get_elapsed_time()


	# Get current song information (Only for use within this module)
	def getCurrentSong(self):
                return self._radiostate.get_currentsong()

	# Get the last ID stored in /var/lib/radiod
	def getStoredID(self,current_file):
                current_id = config.libget('Current Track','id')

		if current_id < 0:
			current_id = 0
		return current_id

	# Change radio station up
	def channelUp(self):
		new_id = self.getCurrentId()
                if new_id == None:
                        new_id = 0
                else:
                        new_id += 1
		log.message("radio.channelUp " + str(new_id), log.DEBUG)
		if new_id >= self._radiostate.get_playlistlength():
			new_id = 0
			self.play(new_id)
		else:
			self.execMpc(lambda: client.next())
				
		return new_id

	# Change radio station down
	def channelDown(self):
		new_id = self.getCurrentId()
                if new_id == None:
                        new_id = 0
                else:
                        new_id -= 1
		log.message("radio.channelDown " + str(new_id), log.DEBUG)
		if new_id < 0:
			new_id = self._radiostate.get_playlistlength() - 1
			self.play(new_id)
		else:
			self.execMpc(lambda: client.previous())

		return new_id

	# Load radio stations
	def startRadio(self):
		log.message("radio.startRadio", log.DEBUG)
                self.load_radio()
		self.randomOff()
		self.consumeOff()
		self.repeatOff()
                log.message("This is somehow wrong: We must store also the menu path",
                            log.ERROR)
		current_id = config.libget('Radio','current')
		self.play(current_id)
		self.search_index = current_id
		return
        
        def load_radio(self):
		self.execMpc(lambda: client.clear())
                radiopath = config.libget('Radio','place_uri')
                radiotype = config.libget('Radio','place_type')
                if not radiopath or not radiotype: return
                try:
                        if radiotype == 'directory':
                                self.changeDir(radiopath)
                        elif radiotype == 'playlist':
                                self.loadPlaylist(radiopath)
                except Exception as e:
                        log.message('top_menu.load_radio: Exception: '+unicode(e),
                                    log.ERROR)
                        log.message(string.join(traceback.format_stack()),log.ERROR)
                        
        def save_current_dir(self, dirtype, entryid, path = None):
                config.libset('Current Track','type',dirtype)
                if path is not None:
                        config.libset('Current Track','path',path)
                config.libset('Current Track','id',str(entryid))
                config.save_libconfig()

                        
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

        def loadPlaylist(self,path, wait = False):
                length = self._radiostate.get_playlistlength()
                log.message("Clearing playlist of length {0}".
                            format(length), log.DEBUG)
                if length:
                        self.execMpc(lambda: client.clear())
                        while wait:
                                if not self._radiostate.get_playlistlength():
                                        break
                                time.sleep(0.001)
                if wait:
                        playlist_time = time.time()
                        log.message("Starting load at {0}".
                                    format(playlist_time),
                                    log.DEBUG)
                try:
                        self.execMpc(lambda: client.load(path))
                except:
                        log.message("Failed to load Radio playlist",
                                    log.WARNING)
                log.message("Waiting for playlist change.",
                            log.DEBUG)
                if wait:
                        
                        while (playlist_time > self._radiostate.get_playlist_time()):
                                time.sleep(0.001)
                return

        # change into a directory
        def changeDir(self, path):
                log.message("radio.changeDir: " + path, log.DEBUG)
                config.libset("Current Track","type",'directory');
                config.libset("Current Track","path",path);
                last_changed = time.time()
                retval = self.load_directory(path);
                while last_changed >= \
                      self._radiostate.get_playlist_time():
                        time.sleep(0.001);
                return retval

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
                                if 'file' in i:
                                        if i['file'] == node['file']:
                                                self.play(index)
                                                return index
                                index += 1
                self.play(0)

        def doPlay(self):
                self.play(self.getCurrentId())

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
		self.execMpc(lambda: client.play(number))
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

	# Get list of tracks or stations
	def getPlayListEntry(self,index):
		return self._radiostate.get_playlist_entry(index)

	# Get the length of the current list
	def getListLength(self):
		return self._radiostate.get_playlistlength()

	# Display artist True or False
	def displayArtist(self):
		return self.display_artist

	def setDisplayArtist(self,dispArtist):
		self.display_artist = dispArtist

        def updateSearchIndex(self):
                index = _radiostate.get_current_id()
                setSearchIndex(index)
                
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


