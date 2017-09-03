#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_class.py,v 1.32 2017/07/24 07:35:41 bob Exp $
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# From original LCD routines : Matt Hawkins
# Site   : http://www.raspberrypi-spy.co.uk
# Timing improvements fromobert Coward/Paul Carpenter
# Site   : http://www.raspberrypi-spy.co.uk
#          http://www.pcserviceslectronics.co.uk
#
# Expanded to use 4 x 20  display
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import os
import time
import RPi.GPIO as GPIO
from translate_class import Translate
from config_class import Configuration

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

# Define LCD device constants
#LCD_WIDTH = 16    # Default characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line
# Some LCDs use different addresses (16 x 4 line LCDs)
LCD_LINE_3a = 0x90 # LCD RAM address for the 3rd line (16 char display)
LCD_LINE_4a = 0xD0 # LCD RAM address for the 4th line (16 char display)

# If using a 4 x 16 display also amend the lcd.setWidth(<width>) statement in rradio4.py

# Timing constants
E_PULSE = 0.00001	# Pulse width of enable
E_DELAY = 0.00001	# Delay between writes
E_POSTCLEAR = 0.01	# Delay after clearing display

translate = Translate()
config = Configuration()

# Lcd Class 
class Lcd:
	# Define GPIO to LCD mapping
	lcd_select = 7
	lcd_enable  = 8
	LCD_D4_21 = 21    # Rev 1 Board
	LCD_D4_27 = 27    # Rev 2 Board
	lcd_data4 = LCD_D4_27
	lcd_data5 = 22
	lcd_data6 = 23
	lcd_data7 = 24

	lcd_line3 = LCD_LINE_3
	lcd_line4 = LCD_LINE_4

	width = 0
	# If display can support umlauts set to True else False
        RawMode = False         # Test only
        ScrollSpeed = 0.3       # Default scroll speed

        def __init__(self):
		return

	# Initialise for either revision 1 or 2 boards
	def init(self,revision=2):
        # LCD outputs

		if revision == 1:
			self.lcd_data4 = LCD_D4_21

		# Get LCD configuration connects including self.lcd_data4
		self.lcd_select = config.getLcdGpio("lcd_select")
		self.lcd_enable  = config.getLcdGpio("lcd_enable")

		if revision != 1:
			self.lcd_data4 = config.getLcdGpio("lcd_data4")

		self.lcd_data5 = config.getLcdGpio("lcd_data5")
		self.lcd_data6 = config.getLcdGpio("lcd_data6")
		self.lcd_data7 = config.getLcdGpio("lcd_data7")

		GPIO.setwarnings(False)	     # Disable warnings
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setup(self.lcd_enable, GPIO.OUT)  # E
		GPIO.setup(self.lcd_select, GPIO.OUT) # RS
		GPIO.setup(self.lcd_data4, GPIO.OUT) # DB4
		GPIO.setup(self.lcd_data5, GPIO.OUT) # DB5
		GPIO.setup(self.lcd_data6, GPIO.OUT) # DB6
		GPIO.setup(self.lcd_data7, GPIO.OUT) # DB7
		self.lcd_init()
		return

	# Initialise the display
	def lcd_init(self):
		self._byte_out(0x33,LCD_CMD) # 110011 Initialise
		self._byte_out(0x32,LCD_CMD) # 110010 Initialise
		self._byte_out(0x06,LCD_CMD) # 000110 Cursor move direction
		self._byte_out(0x17,LCD_CMD) # character mode, power on
		self._byte_out(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
		self._byte_out(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
		self._byte_out(0x01,LCD_CMD) # 000001 Clear display
		time.sleep(0.3)		     # Allow to settle before using
		return
	 
	# Output byte to Led  mode = Command or Data
	def _byte_out(self,bits, mode):
		# Send byte to data pins
		# bits = data
		# mode = True  for character
		#        False for command
		GPIO.output(self.lcd_select, mode) # RS
		# High bits
		GPIO.output(self.lcd_data4, False)
		GPIO.output(self.lcd_data5, False)
		GPIO.output(self.lcd_data6, False)
		GPIO.output(self.lcd_data7, False)
		if bits&0x10==0x10:
			GPIO.output(self.lcd_data4, True)
		if bits&0x20==0x20:
			GPIO.output(self.lcd_data5, True)
		if bits&0x40==0x40:
			GPIO.output(self.lcd_data6, True)
		if bits&0x80==0x80:
			GPIO.output(self.lcd_data7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(self.lcd_enable, True)
		time.sleep(E_PULSE)
		GPIO.output(self.lcd_enable, False)
		time.sleep(E_DELAY)

		# Low bits
		GPIO.output(self.lcd_data4, False)
		GPIO.output(self.lcd_data5, False)
		GPIO.output(self.lcd_data6, False)
		GPIO.output(self.lcd_data7, False)
		if bits&0x01==0x01:
			GPIO.output(self.lcd_data4, True)
		if bits&0x02==0x02:
			GPIO.output(self.lcd_data5, True)
		if bits&0x04==0x04:
			GPIO.output(self.lcd_data6, True)
		if bits&0x08==0x08:
			GPIO.output(self.lcd_data7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(self.lcd_enable, True)
		time.sleep(E_PULSE)
		GPIO.output(self.lcd_enable, False)
		time.sleep(E_DELAY)
		return

	# Set the display width
	def setWidth(self,width):
		self.width = width
		# Adjust line offsets if 16 char display
		if width is 16:
			self.lcd_line3 = LCD_LINE_3a
			self.lcd_line4 = LCD_LINE_4a
		return

	# Get LCD width 0 = use default for program
	def getWidth(self):
		if self.width == 0:
			self.width = config.getWidth()
		return self.width

	# Send string to display
	def _string(self,message):
		# prevent 0 width 
		if self.width == 0:
			self.width = 16
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = translate.toLCD(s)
		for i in range(self.width):
			self._byte_out(ord(s[i]),LCD_CHR)
		return

	# Display Line 1 on LCD
	def line1(self,text):
		self._byte_out(LCD_LINE_1, LCD_CMD)
		self._string(text)
		return

	# Display Line 2 on LCD
	def line2(self,text):
		self._byte_out(LCD_LINE_2, LCD_CMD)
		self._string(text)
		return

	# Display Line 3 on LCD
	def line3(self,text):
		self._byte_out(self.lcd_line3, LCD_CMD)
		self._string(text)
		return

	# Display Line 4 on LCD
	def line4(self,text):
		self._byte_out(self.lcd_line4, LCD_CMD)
		self._string(text)
		return

	# Scroll message on line 1
	def scroll1(self,mytext,interrupt):
		self._scroll(mytext,LCD_LINE_1,interrupt)
		return

	# Scroll message on line 2
	def scroll2(self,mytext,interrupt):
		self._scroll(mytext,LCD_LINE_2,interrupt)
		return

	# Scroll message on line 3
	def scroll3(self,mytext,interrupt):
		self._scroll(mytext,self.lcd_line3,interrupt)
		return

	# Scroll message on line 4
	def scroll4(self,mytext,interrupt):
		self._scroll(mytext,self.lcd_line4,interrupt)
		return

	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self._byte_out(line, LCD_CMD)
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
				self._byte_out(line, LCD_CMD)
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

	# Clear display
	def clearDisplay(self):
		self._byte_out(0x01,LCD_CMD) # 000001 Clear display
		time.sleep(E_POSTCLEAR)
                return


# End of Lcd class
