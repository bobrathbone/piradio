#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_class.py,v 1.22 2014/08/29 10:25:14 bob Exp $
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
import pifacecommon
import pifacecad
#import RPi.GPIO as GPIO

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
#LCD_RS = 7
#LCD_E  = 8
#LCD_D4_21 = 21    # Rev 1 Board
#LCD_D4_27 = 27    # Rev 2 Board
#LCD_D5 = 22
#LCD_D6 = 23
#LCD_D7 = 24

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


# Lcd Class 
class Piface_lcd:
	width = LCD_WIDTH
	# If display can support umlauts set to True else False
	displayUmlauts = True
        RawMode = False         # Test only
        ScrollSpeed = 0.3       # Default scroll speed

        ENTER = 5
        LEFT  = 6
        RIGHT = 7
        LEFTBUTTON  = 0
        BUTTON2     = 1
        BUTTON3     = 2
        RIGHTBUTTON = 3
        EXTRABUTTON = 4

        saveline1 = ""
        saveline2 = ""


#	lcd_d4 = LCD_D4_27	# Default for revision 2 boards 

        def __init__(self):
                self.cad = pifacecad.PiFaceCAD()
                self.lcd = self.cad.lcd
		return

	# Initialise for either revision 1 or 2 boards
	def init(self):
                
                print ("iniit")
		#self.lcd.send_command(0x33)
		#self.lcd.send_command(0x32)
		#self.lcd.send_command(0x28) # 4bit, 2 Zeilen, 5x8-font
		#self.lcd.send_command(0x0C) # disp. on, cursor off, position_car off
		#self.lcd.send_command(0x06) # Increment/no shift
		# self.lcd.send_command(0x01,LCD_CMD) # clear display
		self.lcd.blink_off()
		self.lcd.cursor_off()
		self.lcd.clear()
                time.sleep(0.3)
		self.lcd.backlight_on()
		return


	# Output byte to Led  mode = Command or Data
	def _byte_out(self,bits, mode):
		# Send byte to data pins
		# bits = data
		# mode = True  for character
		#        False for command
                if (mode):
                        self.lcd.send_data(bits)
                else:
                        self.lcd.send_command(bits)
		return

	def clear(self):
		self.lcd.clear()

        def backlight(self,on):
                if (on):
                        self.lcd.backlight_on()
                else:
                        self.lcd.backlight_off()

	# Set the display width
	def setWidth(self,width):
		self.width = width
		return

	# Send string to display
	def _string(self,message):
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = self.translateSpecialChars(s)
                self.lcd.write(s);
		return

	# Display Line 1 on LED
	def line1(self,text):
                self.saveline1 = text
                self.lcd.set_cursor(0,0)
		self._string(text)
		return

	# Display Line 2 on LED
	def line2(self,text):
                self.saveline2 = text
		self.lcd.set_cursor(0,1)
		self._string(text)
		return

	# Display Line 3 on LED
	def line3(self,text):
                self.lcd.set_cursor(0,2)
		self._string(text)
		return

	# Display Line 4 on LED
	def line4(self,text):
		self.lcd.set_cursor(0,3)
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

	# Scroll message on line 3
	def scroll3(self,mytext,interrupt):
		self._scroll(mytext,2,interrupt)
		return

	# Scroll message on line 4
	def scroll4(self,mytext,interrupt):
		self._scroll(mytext,3,interrupt)
		return

	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self.lcd.set_cursor(0,line)
		self._string(mytext[0:self.width + 1])
	
		if (ilen <= self.width):
			skip = True

		if not skip:
			for i in range(0, 5):
				time.sleep(0.2)
				if interrupt():
					skip = True
					break

		if not skip and False:
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
                s = s.replace(chr(224), 'a')       # Small a grave to a
                s = s.replace(chr(225), 'a')       # Small a acute to a
                s = s.replace(chr(226), 'a')       # Small a circumflex to a
                s = s.replace(chr(232), 'e')       # Small e grave to e
                s = s.replace(chr(233), 'e')       # Small e acute to e
                s = s.replace(chr(234), 'e')       # Small e circumflex to e
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

        def buttonPressed(self,Wert):
                retval = self.cad.switches[Wert].value
                print ("Buttons: ",hex(self.cad.switch_port.value))
                print ("Button %d = %d" % (Wert,self.cad.switches[Wert].value))
                return retval
        def get_listener(self):
                self.listener = pifacecad.SwitchEventListener(chip=self.cad)
                return self.listener

        def update_display(self):
                self.line1(self.saveline1)
                self.line2(self.saveline2)
# End of Lcd class
