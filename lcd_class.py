#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_class.py,v 1.26 2015/05/30 13:10:47 bob Exp $
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# From original LCD routines : Matt Hawkins
# Site   : http://www.raspberrypi-spy.co.uk
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

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4_21 = 21    # Rev 1 Board
LCD_D4_27 = 27    # Rev 2 Board
LCD_D5 = 22
LCD_D6 = 23
LCD_D7 = 24

# Define LCD device constants
LCD_WIDTH = 16    # Default characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

# Some LCDs use different addresses (16 x 4 line LCDs)
# Comment out the above two lines and uncomment the two lines below
# LCD_LINE_3 = 0x90 # LCD RAM address for the 3rd line
# LCD_LINE_4 = 0xD0 # LCD RAM address for the 4th line

# If using a 4 x 16 display also amend the lcd.setWidth(<width>) statement in rradio4.py

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005


translate = Translate()

# Lcd Class 
class Lcd:
	width = LCD_WIDTH
	# If display can support umlauts set to True else False
        RawMode = False         # Test only
        ScrollSpeed = 0.3       # Default scroll speed
	lcd_d4 = LCD_D4_27	# Default for revision 2 boards 

        def __init__(self):
		return

	# Initialise for either revision 1 or 2 boards
	def init(self,revision=2):
        # LED outputs
		if revision == 1:
			self.lcd_d4 = LCD_D4_21

		GPIO.setwarnings(False)	     # Disable warnings
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setup(LCD_E, GPIO.OUT)  # E
		GPIO.setup(LCD_RS, GPIO.OUT) # RS
		GPIO.setup(self.lcd_d4, GPIO.OUT) # DB4
		GPIO.setup(LCD_D5, GPIO.OUT) # DB5
		GPIO.setup(LCD_D6, GPIO.OUT) # DB6
		GPIO.setup(LCD_D7, GPIO.OUT) # DB7
		self.lcd_init()
		return

	# Initialise the display
	def lcd_init(self):
		self._byte_out(0x33,LCD_CMD) # 110011 Initialise
		self._byte_out(0x32,LCD_CMD) # 110010 Initialise
		self._byte_out(0x06,LCD_CMD) # 000110 Cursor move direction
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
		GPIO.output(LCD_RS, mode) # RS

		# High bits
		GPIO.output(self.lcd_d4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x10==0x10:
			GPIO.output(self.lcd_d4, True)
		if bits&0x20==0x20:
			GPIO.output(LCD_D5, True)
		if bits&0x40==0x40:
			GPIO.output(LCD_D6, True)
		if bits&0x80==0x80:
			GPIO.output(LCD_D7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(LCD_E, True)
		time.sleep(E_PULSE)
		GPIO.output(LCD_E, False)
		time.sleep(E_DELAY)

		# Low bits
		GPIO.output(self.lcd_d4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x01==0x01:
			GPIO.output(self.lcd_d4, True)
		if bits&0x02==0x02:
			GPIO.output(LCD_D5, True)
		if bits&0x04==0x04:
			GPIO.output(LCD_D6, True)
		if bits&0x08==0x08:
			GPIO.output(LCD_D7, True)

		# Toggle 'Enable' pin
		time.sleep(E_DELAY)
		GPIO.output(LCD_E, True)
		time.sleep(E_PULSE)
		GPIO.output(LCD_E, False)
		time.sleep(E_DELAY)
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
		for i in range(self.width):
			self._byte_out(ord(s[i]),LCD_CHR)
		return

	# Display Line 1 on LED
	def line1(self,text):
		self._byte_out(LCD_LINE_1, LCD_CMD)
		self._string(text)
		return

	# Display Line 2 on LED
	def line2(self,text):
		self._byte_out(LCD_LINE_2, LCD_CMD)
		self._string(text)
		return

	# Display Line 3 on LED
	def line3(self,text):
		self._byte_out(LCD_LINE_3, LCD_CMD)
		self._string(text)
		return

	# Display Line 4 on LED
	def line4(self,text):
		self._byte_out(LCD_LINE_4, LCD_CMD)
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
		self._scroll(mytext,LCD_LINE_3,interrupt)
		return

	# Scroll message on line 4
	def scroll4(self,mytext,interrupt):
		self._scroll(mytext,LCD_LINE_4,interrupt)
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
		time.sleep(E_DELAY)
                return


# End of Lcd class
