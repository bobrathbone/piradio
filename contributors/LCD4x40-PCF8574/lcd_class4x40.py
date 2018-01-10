#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_class4x40.py,v 1.1 2016/04/30 11:11:19 bob Exp $
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
#
# Autor: Pythy
#
# original Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# From original LCD routines : Matt Hawkins
# Site   : http://www.raspberrypi-spy.co.uk
#
# Expanded to use 4 x 40  display with 2 HD 44780 Controller and use a PCF8574 Port Expander (no Backlight Version)
#
# Pinout: P0, P1, P2, P3 = D4, D5, D6, D7    P4=RS, P5=R/W, P6=E1, P7=E2
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#

import os
import smbus
from time import *

# Define LCD device constants
LCD_WIDTH = 40    # Default characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xA8 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x80 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xA8 # LCD RAM address for the 4th line

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005


# Lcd Class
class Lcd:
	# Commands
	CMD_Clear_Display = 0x01
	CMD_Return_Home = 0x02
	CMD_Entry_Mode = 0x04
	CMD_Display_Control = 0x08
	CMD_Cursor_Display_Shift = 0x10
	CMD_Function_Set = 0x20
	CMD_DDRAM_Set = 0x80
	CMD_Lcd_Cursor_Off = 0x0c

	# Options
	OPT_Increment = 0x02 					# CMD_Entry_Mode
	OPT_Display_Shift = 0x01 				# CMD_Entry_Mode
	OPT_Enable_Display = 0x04 				# CMD_Display_Control
	OPT_Enable_Cursor = 0x02 				# CMD_Display_Control
	OPT_Enable_Blink = 0x01 				# CMD_Display_Control
	OPT_Display_Shift = 0x08 				# CMD_Cursor_Display_Shift
	OPT_Shift_Right = 0x04 					# CMD_Cursor_Display_Shift 0 = Left
	OPT_2_Lines = 0x08 						# CMD_Function_Set 0 = 1 line
	OPT_5x10_Dots = 0x04 					# CMD_Function_Set 0 = 5x7 dots


	width = LCD_WIDTH
	# If display can support umlauts set to True else False
	displayUmlauts = True
        RawMode = False         # Test only
        ScrollSpeed = 0.3       # Default scroll speed


	def __init__(self, addr, port, en1, en2, rw, rs, d4, d5, d6, d7):
		self.addr = addr
		self.bus = smbus.SMBus(port)

		self.en1 = en1
		self.en2 = en2
		self.rs = rs
		self.rw = rw
		self.d4 = d4
		self.d5 = d5
		self.d6 = d6
		self.d7 = d7

		# Activate LCD Cotroller 1
		initialize_i2c_data = 0x00
		initialize_i2c_data = self._pinInterpret(self.d4, initialize_i2c_data, 0b1)
		initialize_i2c_data = self._pinInterpret(self.d5, initialize_i2c_data, 0b1)
		self._enable1(initialize_i2c_data)
		sleep(0.2)
		self._enable1(initialize_i2c_data)
		sleep(0.1)
		self._enable1(initialize_i2c_data)
		sleep(0.1)


		# Activate LCD Cotroller 2
		initialize_i2c_data = 0x00
		initialize_i2c_data = self._pinInterpret(self.d4, initialize_i2c_data, 0b1)
		initialize_i2c_data = self._pinInterpret(self.d5, initialize_i2c_data, 0b1)
		self._enable2(initialize_i2c_data)
		sleep(0.2)
		self._enable2(initialize_i2c_data)
		sleep(0.1)
		self._enable2(initialize_i2c_data)
		sleep(0.1)

		# Initialize 4-bit mode Controller 1
		initialize_i2c_data = self._pinInterpret(self.d4, initialize_i2c_data, 0b0)
		self._enable1(initialize_i2c_data)
		sleep(0.01)

		self.command1(self.CMD_Function_Set | self.OPT_2_Lines)
		self.command1(self.CMD_Display_Control | self.OPT_Enable_Display)
		self.command1(self.CMD_Clear_Display)
		self.command1(self.CMD_Entry_Mode | self.OPT_Increment | self.OPT_Display_Shift)
		self.command1(self.CMD_Lcd_Cursor_Off)

		# Initialize 4-bit mode Controller 2
		initialize_i2c_data = self._pinInterpret(self.d4, initialize_i2c_data, 0b0)
		self._enable2(initialize_i2c_data)
		sleep(0.01)

		self.command2(self.CMD_Function_Set | self.OPT_2_Lines)
		self.command2(self.CMD_Display_Control | self.OPT_Enable_Display)
		self.command2(self.CMD_Clear_Display)
		self.command2(self.CMD_Entry_Mode | self.OPT_Increment | self.OPT_Display_Shift)
		self.command2(self.CMD_Lcd_Cursor_Off)
		return

	def init(self):
		self.command1(self.CMD_Clear_Display)
		sleep(0.1)
		self.command2(self.CMD_Clear_Display)
		sleep(0.1)

	# Output byte to Led  mode = Command or Data
	def _byte_out(self,bits, mode, controller):
		i2c_data = 0x00

		#Add data for high nibble
		hi_nibble = bits >> 4
		i2c_data = self._pinInterpret(self.d4, i2c_data, (hi_nibble & 0x01))
		i2c_data = self._pinInterpret(self.d5, i2c_data, ((hi_nibble >> 1) & 0x01))
		i2c_data = self._pinInterpret(self.d6, i2c_data, ((hi_nibble >> 2) & 0x01))
		i2c_data = self._pinInterpret(self.d7, i2c_data, ((hi_nibble >> 3) & 0x01))

		# Set the register selector to 1 if this is data
		if mode != False:
			i2c_data = self._pinInterpret(self.rs, i2c_data, 0x1)

		# Toggle Enable
		
		if controller == False:
			self._enable1(i2c_data)
		else:
			self._enable2(i2c_data)

		i2c_data = 0x00

		#Add data for high nibble
		low_nibble = bits & 0x0F
		i2c_data = self._pinInterpret(self.d4, i2c_data, (low_nibble & 0x01))
		i2c_data = self._pinInterpret(self.d5, i2c_data, ((low_nibble >> 1) & 0x01))
		i2c_data = self._pinInterpret(self.d6, i2c_data, ((low_nibble >> 2) & 0x01))
		i2c_data = self._pinInterpret(self.d7, i2c_data, ((low_nibble >> 3) & 0x01))

		# Set the register selector to 1 if this is data
		if mode != False:
			i2c_data = self._pinInterpret(self.rs, i2c_data, 0x1)

		if controller == False:
			self._enable1(i2c_data)
		else:
			self._enable2(i2c_data)

		sleep(0.01)
		return

	def _pinInterpret(self, pin, data, value="0b0"):
		if value:
			# Construct mask using pin
			mask = 0x01 << (pin)
			data = data | mask
		else:
			# Construct mask using pin
			mask = 0x01 << (pin) ^ 0xFF
			data = data & mask
		return data

	def _enable1(self, data):
		# Determine if black light is on and insure it does not turn off or on
		self.bus.write_byte(self.addr, data)
		self.bus.write_byte(self.addr, self._pinInterpret(self.en1, data, 0b1))
		self.bus.write_byte(self.addr, data)
		return

	def _enable2(self, data):
		# Determine if black light is on and insure it does not turn off or on
		self.bus.write_byte(self.addr, data)
		self.bus.write_byte(self.addr, self._pinInterpret(self.en2, data, 0b1))
		self.bus.write_byte(self.addr, data)
		return

	def command1(self, data):
		self._byte_out(data, False, False)
		return

	def command2(self, data):
		self._byte_out(data, False, True)
		return

	# Set the display width Controller 1
	def setWidth1(self,width):
		self.width = width
		return

	# Set the display width Controller 2
	def setWidth2(self,width):
		self.width = width
		return

	# Send string to display Contoller 1
	def _string1(self,message):
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = self.translateSpecialChars(s)
		for i in range(self.width):
			self._byte_out(ord(s[i]),LCD_CHR, False)
		return

	# Send string to display Contoller 2
	def _string2(self,message):
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = self.translateSpecialChars(s)
		for i in range(self.width):
			self._byte_out(ord(s[i]),LCD_CHR, True)
		return

	# Display Line 1 on LED
	def line1(self,text):
		self._byte_out(LCD_LINE_1, LCD_CMD, False)
		self._string1(text)
		return

	# Display Line 2 on LED
	def line2(self,text):
		self._byte_out(LCD_LINE_2, LCD_CMD, False)
		self._string1(text)
		return

	# Display Line 3 on LED
	def line3(self,text):
		self._byte_out(LCD_LINE_3, LCD_CMD, True)
		self._string2(text)
		return

	# Display Line 4 on LED
	def line4(self,text):
		self._byte_out(LCD_LINE_4, LCD_CMD, True)
		self._string2(text)
		return

	# Scroll message on line 1
	def scroll1(self,mytext,interrupt):
		self._scroll1(mytext,LCD_LINE_1,interrupt)
		return

	# Scroll message on line 2
	def scroll2(self,mytext,interrupt):
		self._scroll1(mytext,LCD_LINE_2,interrupt)
		return

	# Scroll message on line 3
	def scroll3(self,mytext,interrupt):
		self._scroll2(mytext,LCD_LINE_3,interrupt)
		return

	# Scroll message on line 4
	def scroll4(self,mytext,interrupt):
		self._scroll2(mytext,LCD_LINE_4,interrupt)
		return

	# Scroll line - interrupt() breaks out routine if True (Controller 1)
	def _scroll1(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self._byte_out(line, LCD_CMD, False)
		self._string1(mytext[0:self.width + 1])

		if (ilen <= self.width):
			skip = True

		if not skip:
			for i in range(0, 5):
				sleep(0.2)
				if interrupt():
					skip = True
					break

		if not skip:
			for i in range(0, ilen - self.width + 1 ):
				self._byte_out(line, LCD_CMD, False)
				self._string1(mytext[i:i+self.width])
				if interrupt():
					skip = True
					break
				sleep(self.ScrollSpeed)

		if not skip:
			for i in range(0, 5):
				sleep(0.2)
				if interrupt():
					break
		return

	# Scroll line - interrupt() breaks out routine if True (Controller 2)
	def _scroll2(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self._byte_out(line, LCD_CMD, True)
		self._string2(mytext[0:self.width + 1])

		if (ilen <= self.width):
			skip = True

		if not skip:
			for i in range(0, 5):
				sleep(0.2)
				if interrupt():
					skip = True
					break

		if not skip:
			for i in range(0, ilen - self.width + 1 ):
				self._byte_out(line, LCD_CMD, True)
				self._string2(mytext[i:i+self.width])
				if interrupt():
					skip = True
					break
				sleep(self.ScrollSpeed)

		if not skip:
			for i in range(0, 5):
				sleep(0.2)
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

	# Display umlats if tro elese oe ae etc
        def displayUmlauts(self,value):
                self.displayUmlauts = value
                return

	# Translate special characters (umlautes etc) to LCD values
	# See standard character patterns for LCD display
	def translateSpecialChars(self,sp):
		s = sp

                # Currency
                s = s.replace(chr(156), '#')       # Pound by hash
                s = s.replace(chr(169), '(c)')     # Copyright

                # Spanish french
                s = s.replace(chr(241), 'n')       # Small tilde n
                s = s.replace(chr(191), '?')       # Small u acute to u
                s = s.replace(chr(224), 'a')       # Small reverse a acute to a
                s = s.replace(chr(225), 'a')       # Small a acute to a
                s = s.replace(chr(232), 'e')       # Small e grave to e
                s = s.replace(chr(233), 'e')       # Small e acute to e
                s = s.replace(chr(237), 'i')       # Small i acute to i
                s = s.replace(chr(238), 'i')       # Small i circumflex to i
                s = s.replace(chr(243), 'o')       # Small o acute to o
                s = s.replace(chr(244), 'o')       # Small o circumflex to o
                s = s.replace(chr(250), 'u')       # Small u acute to u
                s = s.replace(chr(193), 'A')       # Capital A acute to A
                s = s.replace(chr(201), 'E')       # Capital E acute to E
                s = s.replace(chr(205), 'I')       # Capital I acute to I
                s = s.replace(chr(209), 'N')       # Capital N acute to N
                s = s.replace(chr(211), 'O')       # Capital O acute to O
                s = s.replace(chr(218), 'U')       # Capital U acute to U
                s = s.replace(chr(220), 'U')       # Capital U umlaut to U
                s = s.replace(chr(231), 'c')       # Small c Cedilla
                s = s.replace(chr(199), 'C')       # Capital C Cedilla

                # German
                s = s.replace(chr(196), "Ae")           # A umlaut
                s = s.replace(chr(214), "Oe")           # O umlaut
                s = s.replace(chr(220), "Ue")           # U umlaut

                if self.displayUmlauts:
                        s = s.replace(chr(223), chr(226))       # Sharp s
                        s = s.replace(chr(246), chr(239))       # o umlaut
                        s = s.replace(chr(228), chr(225))       # a umlaut
                        s = s.replace(chr(252), chr(245))       # u umlaut
                else:
                        s = s.replace(chr(228), "ae")           # a umlaut
                        s = s.replace(chr(223), "ss")           # Sharp s
                        s = s.replace(chr(246), "oe")           # o umlaut
                        s = s.replace(chr(252), "ue")           # u umlaut
		return s


# End of Lcd class
