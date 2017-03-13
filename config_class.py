#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: config_class.py,v 1.40 2017/02/12 13:01:02 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /etc/radiod.conf file for configuration parameters
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import ConfigParser
from log_class import Log

# System files
ConfigFile = "/etc/radiod.conf"

log = Log()
config = ConfigParser.ConfigParser()


class Configuration:
	# Input source
	RADIO = 0
	PLAYER = 1
	LIST = 0
	STREAM = 1

	# Rotary class selection
	STANDARD = 0	# Select rotary_class.py
	ALTERNATIVE = 1	# Select rotary_class_alternate.py

	# Configuration parameters
	mpdport = 6600  # MPD port number
	dateFormat = "%H:%M %d/%m/%Y"   # Date format
	volume_range = 100 		# Volume range 10 to 100
	volume_increment = 1 		# Volume increment 1 to 10
	display_playlist_number = False # Two line displays only, display station(n)
	source = RADIO  		# Source RADIO or Player
	auto_load = False 		# Auto load media if no Internet on startup
	stationNamesSource = LIST # Station names from playlist names or STREAM
	rotary_class = STANDARD		# Rotary class STANDARD or ALTERNATIVE 
	lcd_width = 0		# Line width of LCD 0 = use program default

	# Remote control parameters 
	remote_led = 0  # Remote Control activity LED 0 = No LED	
	remote_control_host = 'localhost' 	# Remote control to radio communication port
	remote_listen_host = 'localhost' 	# Remote control to radio communication port
	remote_control_port = 5100 	  	# Remote control to radio communication port

	ADAFRUIT = 1	    # I2C backpack type AdaFruit
	PCF8574  = 2	    # I2C backpack type PCF8574
	i2c_backpack = ADAFRUIT 
	i2c_address = 0x00	# Use defaults or use setting in radiod.conf 
	backpack_names = [ 'UNKWOWN','ADAFRUIT','PCF8574']
	speech = False 	    # Speech on for visually impaired or blind persons
	isVerbose = False     # Extra speech verbosity
	speech_volume = 80  # Percentage speech volume 
	use_playlist_extensions = False # MPD 0.15 requires playlist.<ext>


	# Colours for Adafruit LCD
	color = { 'OFF': 0x0, 'RED' : 0x1, 'GREEN' : 0x2, 'YELLOW' : 0x3,
		  'BLUE' : 0x4, 'VIOLET' : 0x5, 'TEAL' : 0x6, 'WHITE' : 0x7 }

	colorName = { 0: 'Off', 1 : 'Red', 2 : 'Green', 3 : 'Yellow',
		    4 : 'Blue', 5 : 'Violet', 6 : 'Teal', 7 : 'White' }

	colors = { 'bg_color' : 0x0,
		   'mute_color' : 0x0,
		   'shutdown_color' : 0x0,
		   'error_color' : 0x0,
		   'search_color' : 0x0,
		   'source_color' : 0x0,
		   'info_color' : 0x0,
		   'menu_color' : 0x0,
		   'sleep_color': 0x0 }

	# List of loaded options for display
	configOptions = {}

	# Other definitions
	UP = 0
	DOWN = 1

	#  GPIOs for switches and rotary encoder configuration
	switches = { "menu_switch": 25,
		     "mute_switch": 4,
		     "left_switch": 14,
		     "right_switch": 15,
		     "up_switch": 17,
		     "down_switch": 18,
		     "aux_switch": 0,
		   }

	# Values for the rotary switch on vintage radio (Not rotary encoders)
	# Zero values disable usage 
	menu_switches = {"menu_switch_value_1": 0,	# Normally 24
			 "menu_switch_value_2": 0,	# Normally 8
			 "menu_switch_value_4": 0,	# Normally 7
			}
	
	# RGB LED definitions for vintage radio
	# Zero values disable usage 
	rgb_leds = { "rgb_green": 0,	# Normally 27
		     "rgb_blue": 0,	# Normally 22
		     "rgb_red": 0,	# Normally 23
		   }

	#  GPIOs for LCD connections
	lcdconnects = { 
		     "lcd_enable": 8,
		     "lcd_select": 7,
		     "lcd_data4": 27,
		     "lcd_data5": 22,
		     "lcd_data6": 23,
		     "lcd_data7": 24,
		   }

	# Initialisation routine
	def __init__(self):
		log.init('radio')
		if not os.path.isfile(ConfigFile) or os.path.getsize(ConfigFile) == 0:
			log.message("Missing configuration file " + ConfigFile, log.ERROR)
		else:
			self.getConfig()

		return

	# Get configuration options from /etc/radiod.conf
	def getConfig(self):
		section = 'RADIOD'

		# Get options
		config.read(ConfigFile)
		try:
			options =  config.options(section)
			for option in options:
				option = option.lower()
				parameter = config.get(section,option)
				
				self.configOptions[option] = parameter

				if option == 'loglevel':
					next

				elif option == 'volume_range':
					range = 100
					try:
						range = int(parameter)
						if range < 10:
							range = 10
						if range > 100:
							range = 100
						self.volume_range = range
						self.volume_increment = int(100/range)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'remote_led':
					try:
						self.remote_led = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'remote_control_host':
					self.remote_control_host = parameter

				elif option == 'remote_control_port':
					try:
						self.remote_control_port = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'remote_listen_host':
					self.remote_listen_host = parameter

				elif option == 'mpdport':
					try:
						self.mpdport = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'dateformat':
					self.dateFormat = parameter

				elif option == 'display_playlist_number':
					if parameter == 'yes':
						self.display_playlist_number = True

				elif option == 'startup':
					if parameter == 'MEDIA':
						self.source =  self.PLAYER
					elif parameter == 'AUTO': 
						self.auto_load = True

				elif option == 'station_names':
					if parameter == 'stream':
						self.stationNamesSource =  self.STREAM
					else:
						self.stationNamesSource =  self.LIST

				elif option == 'i2c_backpack':
					if parameter == 'PCF8574':
						self.i2c_backpack =  self.PCF8574
					else:
						self.i2c_backpack =  self.ADAFRUIT

				elif option == 'i2c_address':
					try:
						value = int(parameter,16)
						if parameter  > 0x00:
							self.i2c_address =  value
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif 'color' in option:
					try:
						self.colors[option] = self.color[parameter]
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'speech':
					if parameter == 'yes':
						self.speech = True
					else:
						self.speech = False

				elif option == 'verbose':
					if parameter == 'yes':
						self.isVerbose = True
					else:
						self.isVerbose = False

				elif option == 'speech_volume':
					try:
						self.speech_volume = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'use_playlist_extensions':
					if parameter == 'yes':
						self.use_playlist_extensions = True
					else:
						self.use_playlist_extensions = False

				elif '_switch' in option and not 'menu_switch_value'in option:
					try:
						self.switches[option] = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif 'lcd_width' in option:
					try:
						self.lcd_width = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif 'lcd_' in option:
					try:
						lcdconnect = int(parameter)
						self.lcdconnects[option] = lcdconnect
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif 'rgb' in option:
					try:
						led = int(parameter)
						self.rgb_leds[option] = led
					except:
						msg = "Invalid RGB LED connect parameter " +  option
						log.message(msg,log.ERROR)

				elif 'menu_switch_value_' in option:
					try:
						menuswitch = int(parameter)
						self.menu_switches[option] = menuswitch
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				elif option == 'rotary_class':
					if parameter == 'standard':
						self.rotary_class = self.STANDARD
					else:
						self.rotary_class = self.ALTERNATIVE

				elif 'lcd_width' in option:
					try:
						self.lcd_width = int(parameter)
					except:
						self.invalidParameter(ConfigFile,option,parameter)

				else:
					msg = "Invalid option " + option + ' in section ' \
						+ section + ' in ' + ConfigFile
					log.message(msg,log.ERROR)

		except ConfigParser.NoSectionError:
			msg = ConfigParser.NoSectionError(section),'in',ConfigFile
			log.message(msg,log.ERROR)
		return


	# Invalid parametrs message
	def invalidParameter(self, ConfigFile, option, parameter):
		msg = "Invalid parameter " + parameter + ' in option ' \
			+ option + ' in ' + ConfigFile
		log.message(msg,log.ERROR)
	
	# Get routines

	# Get I2C backpack type
	def getBackPackType(self):
		return self.i2c_backpack

	# Get I2C backpack address
	def getI2Caddress(self):
		return self.i2c_address

	# Get I2C backpack name
	def getBackPackName(self):
		return self.backpack_names[self.i2c_backpack]

	# Get the volume range
	def getVolumeRange(self):
		return self.volume_range

	# Get the volume increment
	def getVolumeIncrement(self):
		return self.volume_increment

	# Get the remote control activity LED number
	def getRemoteLed(self):
		return self.remote_led

	# Get the remote Host default localhost
	def getRemoteUdpHost(self):
		return self.remote_control_host

	# Get the UDP server listener IP Host default localhost
	# or 0.0.0.0 for all interfaces
	def getRemoteListenHost(self):
		return self.remote_listen_host

	# Get the remote Port  default 5100
	def getRemoteUdpPort(self):
		return self.remote_control_port

	# Get the mpdport
	def getMpdPort(self):
		return self.mpdport

	# Get the date format
	def getDateFormat(self):
		return self.dateFormat

	# Get display playlist number (Two line displays only)
	def getDisplayPlaylistNumber(self):
		return self.display_playlist_number

	# Get the startup source 0=RADIO or 1=MEDIA
	def getSource(self):
		return self.source

	# Get Auto load option 
	def autoload(self):
		return self.auto_load

	# Get the startup source name RADIO MEDIA
	def getSourceName(self):
		source_name = "MEDIA"
		if self.getSource() < 1:
			source_name = "RADIO"
		return source_name

	# Get the background color (Integer)
	def getBackColor(self,sColor):
		color = 0x0
	# Get the remote Port  default 5100
	def getRemoteUdpPort(self):
		return self.remote_control_port

	# Get the mpdport
	def getMpdPort(self):
		return self.mpdport

	# Get the date format
	def getDateFormat(self):
		return self.dateFormat

	# Get display playlist number (Two line displays only)
	def getDisplayPlaylistNumber(self):
		return self.display_playlist_number

	# Get the startup source 0=RADIO or 1=MEDIA
	def getSource(self):
		return self.source

	# Get the startup source name RADIO MEDIA
	def getSourceName(self):
		source_name = "MEDIA"
		if self.getSource() < 1:
			source_name = "RADIO"
		return source_name

	# Get the background color (Integer)
	def getBackColor(self,sColor):
		color = 0x0
		try: 
			color = self.colors[sColor]
		except:
			log.message("Invalid option " + sColor, log.ERROR)
		return color

	# Cycle background colors
	def cycleColor(self,direction):
		color = self.getBackColor('bg_color')

		if direction == self.UP:
			color += 1
		else:
			color -= 1

		if color < 0:
			color = 0x7
		elif color > 0x7:
			color = 0x0

		self.colors['bg_color'] = color
		return color


	# Get the background colour string name
	def getBackColorName(self,iColor):
		sColor = 'None' 
		try: 
			sColor = self.colorName[iColor]
		except:
			log.message("Invalid option " + int(iColor), log.ERROR)
		return sColor

	# Get speech
	def getSpeech(self):
		return self.speech	

	# Get verbose
	def verbose(self):
		return self.isVerbose	

	# Get speech volume % of normal volume level
	def getSpeechVolume(self):
		return self.speech_volume

	# Get playlist extensions used 
	def getPlaylistExtensions(self):
		return self.use_playlist_extensions	

	# Return the sations name source (Stream or playlist)
	def getStationNamesSource(self):
		return self.stationNamesSource	

	# Display parameters
	def display(self):
		for option in sorted(self.configOptions):
			param = self.configOptions[option]
			if option != 'None':
				log.message(option + " = " + param, log.DEBUG)
		return

	# Return the ID of the rotary class to be used STANDARD or ALTERNATIVE
	def getRotaryClass(self):
		return self.rotary_class

	# Returns the switch GPIO configuration by label
	def getSwitchGpio(self,label):
		switch = -1
		try:
			switch = self.switches[label]
		except:
			msg = "Invalid switch label " + label
			log.message(msg, log.ERROR)
		return switch

	# Returns the LCD GPIO configuration by label
	def getLcdGpio(self,label):
		lcdconnect = -1
		try:
			lcdconnect = self.lcdconnects[label]
		except:
			msg = "Invalid LCD connection label " + label
			log.message(msg, log.ERROR)
		return lcdconnect

	# Get the RGB Led configuration by label (Retro radio only)
	def getRgbLed(self,label):
		led = -1
		try:
			led = self.rgb_leds[label]
		except:
			msg = "Invalid RGB configuration label " + label
			log.message(msg, log.ERROR)
		return led

	# Get the RGB Led configuration by label (Retro radio only)
	def getMenuSwitch(self,label):
		menuswitch = -1
		try:
			menuswitch = self.menu_switches[label]
		except:
			msg = "Invalid menu switch configuration label " + label
			log.message(msg, log.ERROR)
		return menuswitch

	# Get LCD width
	def getWidth(self):
		return self.lcd_width

# End Configuration of class

# Test Configuration class
if __name__ == '__main__':

	config = Configuration()
	print "Configuration file", ConfigFile
	print "Volume range:", config.getVolumeRange()
	print "Volume increment:", config.getVolumeIncrement()
	print "Mpd port:", config.getMpdPort()
	print "Remote LED:", config.getRemoteLed()
	print "Remote LED port:", config.getRemoteUdpPort()
	print "Date format:", config.getDateFormat()
	print "Display playlist number:", config.getDisplayPlaylistNumber()
	print "Source:", config.getSource(), config.getSourceName()
	print "Auto-load", config.autoload()
	print "Background colour number:", config.getBackColor('bg_color')
	print "Background colour:", config.getBackColorName(config.getBackColor('bg_color'))
	print "Speech:", config.getSpeech()
	print "Speech volume:", str(config.getSpeechVolume()) + '%'
	print "Verbose:", config.verbose()
	if config.getStationNamesSource() is 1:
		sSource = "STREAM"
	else: 
		sSource = "LIST"
	print "Station names source:",sSource
	print "Use playlist extensions:", config.getPlaylistExtensions()

	for switch in config.switches:
		print switch, config.getSwitchGpio(switch)
	
	for lcdconnect in sorted(config.lcdconnects):
		print lcdconnect, config.getLcdGpio(lcdconnect)
	
	for led in config.rgb_leds:
		print led, config.getRgbLed(led)
	
	for menuswitch in config.menu_switches:
		print menuswitch, config.getMenuSwitch(menuswitch)
	
	rclass = ['Standard', 'Alternative']
	rotary_class = config.getRotaryClass()
	print "Rotary class:", rotary_class, rclass[rotary_class]
	print "Backpack type:", config.getBackPackType(), config.getBackPackName()
	print "I2C address:", hex(config.getI2Caddress())
	print "LCD width:", config.getWidth()

# End of file

