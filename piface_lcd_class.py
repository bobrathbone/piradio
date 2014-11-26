#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: lcd_class.py,v 1.22 2014/08/29 10:25:14 bob Exp $
# Raspberry Pi Internet Radio
# using Piface Control & Display
#
# Autor : Tobias Schlemmer
# Site  : http://schlemmersoft.de/
#
# Original Author : Bob Rathbone
# Original Site   : http://www.bobrathbone.com
#  
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
import sys
import time
import pifacecommon
import pifacecad
import threading
import codecs
import cpHD44780
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

PLAY_SYMBOL = pifacecad.LCDBitmap(
        [0x10, 0x18, 0x1c, 0x1e, 0x1c, 0x18, 0x10, 0x0])
PAUSE_SYMBOL = pifacecad.LCDBitmap(
        [0x0, 0x1b, 0x1b, 0x1b, 0x1b, 0x1b, 0x0, 0x0])
INFO_SYMBOL = pifacecad.LCDBitmap(
        [0x6, 0x6, 0x0, 0x1e, 0xe, 0xe, 0xe, 0x1f])
MUSIC_SYMBOL = pifacecad.LCDBitmap(
        [0x2, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0])
STOP_SYMBOL = pifacecad.LCDBitmap(
        [0x0, 0x1F, 0x1F, 0x3F, 0x1F, 0x1F, 0x0, 0x0])
TIME_SYMBOL = pifacecad.LCDBitmap(
        [0x0E, 0x15, 0x15, 0x15, 0x13, 0x11, 0x0E, 0x00])

def heartbeat_run(self):
        while True:
                self.heartbeat()
                time.sleep(0.1)
                


# Lcd Class 
class Piface_lcd:
        _update_thread = None
	width = LCD_WIDTH
	# If display can support umlauts set to True else False
	displayUmlauts = True
        RawMode = False         # Test only
        ScrollSpeed = 0.4       # Default scroll speed
        ScrollDelay = 1.5

        ENTER = 5
        LEFT  = 6
        RIGHT = 7
        BUTTON1     = 0
        BUTTON2     = 1
        BUTTON3     = 2
        BUTTON4     = 3
        BUTTON5     = 4

        PLAY_SYMBOL_INDEX = 0
        PAUSE_SYMBOL_INDEX = 1
        STOP_SYMBOL_INDEX = 2
        INFO_SYMBOL_INDEX = 3
        MUSIC_SYMBOL_INDEX = 4
        TIME_SYMBOL_INDEX = 5

        savelines = ["","","",""]
        scrolllist = []

        lcdlock = threading.Lock()


#	lcd_d4 = LCD_D4_27	# Default for revision 2 boards 

        def __init__(self):
                self.cad = pifacecad.PiFaceCAD()
                self.lcd = self.cad.lcd
                self.width = 16
                self.clear()

                self.lcd.backlight_on()
                self.cad.lcd.store_custom_bitmap(self.PLAY_SYMBOL_INDEX,
                                                 PLAY_SYMBOL)
                self.cad.lcd.store_custom_bitmap(self.PAUSE_SYMBOL_INDEX,
                                                 PAUSE_SYMBOL)
                self.cad.lcd.store_custom_bitmap(self.STOP_SYMBOL_INDEX,
                                                 STOP_SYMBOL)
                self.cad.lcd.store_custom_bitmap(self.INFO_SYMBOL_INDEX,
                                                 INFO_SYMBOL)
                self.cad.lcd.store_custom_bitmap(self.MUSIC_SYMBOL_INDEX,
                                                 MUSIC_SYMBOL)
                self.cad.lcd.store_custom_bitmap(self.TIME_SYMBOL_INDEX,
                                                 TIME_SYMBOL)
        def __enter__(self):
                self.lock()
                return

        def __exit__(self,type,value,traceback):
                self.unlock()
        
        def start(self):
                self._update_thread = threading.Thread(name="LCD-heartbeat",
                                                       group=None,
                                                       target = heartbeat_run,
                                                       args = [self])
                self._update_thread.daemon = True
                self._update_thread.start()

#                 for i in range(8):
#                         for j in range(2):
#                                 self.lcd.set_cursor(0,j)
#                                 for k in range(16):
#                                         self.lcd.write(chr(16*(2*i + j)+k))
#                         sys.stdin.readline()
#                 
		return

	# Initialise for either revision 1 or 2 boards
	def init(self):
                
		#self.lcd.send_command(0x33)
		#self.lcd.send_command(0x32)
		#self.lcd.send_command(0x28) # 4bit, 2 Zeilen, 5x8-font
		#self.lcd.send_command(0x0C) # disp. on, cursor off, position_car off
		#self.lcd.send_command(0x06) # Increment/no shift
		# self.lcd.send_command(0x01,LCD_CMD) # clear display
		self.lcd.blink_off()
		self.lcd.cursor_off()
		self.clear()
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
                for i in range (0,2):
                        self.savelines[i] = "".ljust(self.width," ")


        def backlight(self,on):
                if (on):
                        self.lcd.backlight_on()
                else:
                        self.lcd.backlight_off()

        def display(self,on):
                if (on):
                        self.lcd.display_on()
                else:
                        self.lcd.display_off()

	# Set the display width
	def setWidth(self,width):
		self.width = width
                for i in range (0,2):
                        self.savelines = "".ljust(self.width," ")
		return

	# Send string to display
	def _string(self,message):
                s = message
		if not self.RawMode:
			s = self.translateSpecialChars(s)
                # log.message("LCD._string: " + s, log.DEBUG)
                self.lcd.write(s);
		return

        def putSymbol(self,x,y,sym):
                self.line(x,y,"{0:c}".format(sym),1)

	# Display Line 1 on LED
	def line(self,x,y,message,length = None, clear = True):
                if not self.is_locked:
                        error_LCD_not_locked()
                if not length:
                        length = self.width
		text = message.ljust(length," ")
                leng = len(text)
                end = x+leng
                if clear:
                        self.clear_scroll(x,y,leng)
        
                current_line = (self.savelines[y][0:x]
                                + text
                                + self.savelines[y][end:self.width])
                first_difference = self.width
                for i in range(0,self.width-1):
                        if current_line[i] != self.savelines[y][i]:
                                first_difference = i
                                break
                last_difference = first_difference -1
                for i in range(self.width-1,first_difference-1,-1):
                        if current_line[i] != self.savelines[y][i]:
                                last_difference = i+1
                                break
                self.lcd.set_cursor(first_difference,y)
		self._string(current_line[first_difference:last_difference])
                self.savelines[y] = current_line
		return

        def clear_scroll(self,x,y,length):
                tmp= []
                for i in range (len(self.scrolllist)):
                        if (self.scrolllist[i][1] != y or
                            (self.scrolllist[i][0]+self.scrolllist[i][2] <= x or
                             self.scrolllist[i][0] >= x + length)):
                                tmp.append(self.scrolllist[i])
                self.scrolllist = tmp

	# Scroll message on line 1
	def scroll(self,x,y,mytext):
		self._scroll(mytext,x,y)
		return

	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,x,y,length=None):
		ilen = len(mytext)
                if x >= self.width: return
                if  not length or (x+length > self.width):
                        length = self.width - x
		skip = False

		self.line(x,y,mytext[0:length],length)
                if ilen <= length: return
                padding = " ".ljust(length," ")
                self.scrolllist.append([x,
                                        y,
                                        length,
                                        padding + mytext + padding,
                                        length,
                                        time.time()+self.ScrollDelay])



#		if (ilen <= self.width):
#			skip = True
#
#                skip = True
#
#		if not skip:
#			for i in range(0, 5):
#				time.sleep(0.2)
#
#		if not skip and False:
#			for i in range(0, ilen - self.width + 1 ):
#				self._byte_out(line, LCD_CMD)
#				self._string(mytext[i:i+self.width])
#				time.sleep(self.ScrollSpeed)
#
#		if not skip:
#			for i in range(0, 5):
#				time.sleep(0.2)
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
                return codecs.charmap_encode(sp,'replace',cpHD44780.encoding_map_A00)[0];
		s = sp

                # Currency
                s = s.replace('œ', 'oe')       # Pound by hash
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
                return retval
        def get_listener(self):
                self.listener = pifacecad.SwitchEventListener(chip=self.cad)
                return self.listener

        def lock(self):
                self.lcdlock.acquire()
                self.is_locked = True

        def unlock(self):
                self.is_locked = False
                self.lcdlock.release()

        def heartbeat(self):
                current_time = time.time()
                again = True
                while again:
                        again = False
                        with self.lcdlock:
                                self.is_locked = True
                                for i in range(len(self.scrolllist)):
                                        if current_time >= self.scrolllist[i][5]:
                                                again = True
                                                self.scrolllist[i][5]+=self.ScrollSpeed
                                                self.scrolllist[i][4]+=1
                                                if (self.scrolllist[i][4]+self.scrolllist[i][2]
                                                    > len(self.scrolllist[i][3])):
                                                        self.scrolllist[i][4] = 0
                                                self.line(
                                                        self.scrolllist[i][0],
                                                        self.scrolllist[i][1],
                                                        self.scrolllist[i][3][self.scrolllist[i][4]:
                                                                              self.scrolllist[i][4]+
                                                                              self.scrolllist[i][2]],
                                                        self.scrolllist[i][2],
                                                        False)
                                self.is_locked = False
                return

# End of Lcd class
