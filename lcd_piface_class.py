#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_piface_class.py,v 1.25 2015/01/03 14:45:41 patrick Exp $
# Raspberry Pi Internet Radio
# using a Piface backlit LCD plate
#
# Author : Bob Rathbone
# Site   : http://bobrathbone.com
# Modified by Patrick Zacharias for use with PiFace
#
# From original LCD routines : piface.co.uk
# Site   : http://piface.github.io/pifacecad
#
# To use this program you need pifacecommon and pifacecad installed
# for their respective Python versions
#
# At the moment this program can only be executed with Python2.7
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import time
from translate_class import Translate

import subprocess
import pifacecommon
import pifacecad
from pifacecad.lcd import LCD_WIDTH

PLAY_SYMBOL = pifacecad.LCDBitmap(
    [0x10, 0x18, 0x1c, 0x1e, 0x1c, 0x18, 0x10, 0x0])
PAUSE_SYMBOL = pifacecad.LCDBitmap(
    [0x0, 0x1b, 0x1b, 0x1b, 0x1b, 0x1b, 0x0, 0x0])
INFO_SYMBOL = pifacecad.LCDBitmap(
    [0x6, 0x6, 0x0, 0x1e, 0xe, 0xe, 0xe, 0x1f])
MUSIC_SYMBOL = pifacecad.LCDBitmap(
    [0x2, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0])

PLAY_SYMBOL_INDEX = 0
PAUSE_SYMBOL_INDEX = 1
INFO_SYMBOL_INDEX = 2
MUSIC_SYMBOL_INDEX = 3
#Symbols were taken from the pifacecad examples and aren't in use yet

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0	     - NOT USED
# 8 : Data Bit 1	     - NOT USED
# 9 : Data Bit 2	     - NOT USED
# 10: Data Bit 3	     - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND


# Define LCD device constants
LCD_WIDTH = 16    # Default characters per line
LCD_CHR = True
LCD_CMD = False

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005


translate = Translate()

# Lcd Class 
class Lcd:
	width = LCD_WIDTH
	RawMode = False
	ScrollSpeed = 0.3	# Default scroll speed


	# Port expander input pin definitions
#	MENU  = 0
#	RIGHT = 1
#	DOWN  = 2
#	UP    = 3
#	LEFT  = 4

	LEFT = 0
	DOWN = 1
	UP   = 2
	RIGHT= 3
	MENU = 4

	def __init__(self):
#		self.cad = pifacecad.pifacecad()
		return

	def init(self):
	# LED outputs
		self.cad = pifacecad.PiFaceCAD()
		# set up cad
		self.cad.lcd.blink_off()
		self.cad.lcd.cursor_off()
		self.cad.lcd.backlight_on()

		self.cad.lcd.store_custom_bitmap(PLAY_SYMBOL_INDEX, PLAY_SYMBOL)
		self.cad.lcd.store_custom_bitmap(PAUSE_SYMBOL_INDEX, PAUSE_SYMBOL)
		self.cad.lcd.store_custom_bitmap(INFO_SYMBOL_INDEX, INFO_SYMBOL)
		return


	# Set the display width
	def setWidth(self,width):
		self.width = width
		return

	# Send string to display
	def _string(self,message):
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = translate.toLCD(s)
		self.cad.lcd.write(s)
		return

	# Display Line 1 on LED
	def line1(self,text):
		self.cad.lcd.set_cursor(0, 0)
		self._string(text)
		return

	# Display Line 2 on LED
	def line2(self,text):
		self.cad.lcd.set_cursor(0, 1)
		self._string(text)
		return

	# Scroll message on line 1
	def scroll1(self,mytext,interrupt):
		self._scroll(mytext,0,interrupt)
		return

	# Scroll message on line 2
	def scroll2(self,mytext,interrupt):
		self._scroll(mytext,1,interrupt)
		return


	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

                self.cad.lcd.set_cursor(0, line)
		self._string(mytext[0:self.width + 1])
	
		if (ilen <= self.width):
			skip = True

		if not skip:
			for i in range(0, 5):
				time.sleep(0.2)
				if interrupt():
					skip = True
					break

		if not skip:
			for i in range(0, ilen - self.width + 1 ):
			#	self._byte_out(line, LCD_CMD)
				self.cad.lcd.set_cursor(0, line)
				self._string(mytext[i:i+self.width])
				if interrupt():
					skip = True
					break
				time.sleep(self.ScrollSpeed)

		if not skip:
			for i in range(0, 5):
				time.sleep(0.2)
				if interrupt():
					break
		return

	# Set Scroll line speed - Best values are 0.2 and 0.3
	# Limit to between 0.05 and 1.0
	def setScrollSpeed(self,speed):
		if speed < 0.05:
			speed = 0.2
		elif speed > 1.0:
			speed = 0.3
		self.ScrollSpeed = speed
		return

	# Set raw mode on (No translation)
	def setRawMode(self,value):
		self.RawMode = value
		return
	
	# Read state of single button
	def buttonPressed(self, b):
		button =  self.cad.switches[b].value
		return button
	# Clear the display
	def clear(self):
		self.cad.lcd.clear()
	
	# Sets cursor home
	def home(self):
		self.cad.lcd.home()


# End of Lcd class
