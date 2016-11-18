#!/usr/bin/env python
#
# LCD test program for the lcd_i2c_class.py class
# $Id: lcd_i2c_pcf8574.py,v 1.2 2016/04/30 09:17:01 bob Exp $
# PCF8574 I2C LCD Backpack LCD class
# Adapted from unknown code author ufux on GitHub
# See https://gist.github.com/ufux/6094977
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
# communication from expander to display: high nibble first, then low nibble
# communication via i2c to the PCF 8547: bits are processed from highest to lowest (send P7 bit first) 

import smbus
import os
import sys
from time import *
from time import gmtime, strftime

# General i2c device class so that other devices can be added easily
class i2c_device:
	def __init__(self, addr, port):
		self.addr = addr
		self.bus = smbus.SMBus(port)

	def write(self, byte):
		self.bus.write_byte(self.addr, byte)

	def read(self):
		return self.bus.read_byte(self.addr)

	def read_nbytes_data(self, data, n): # For sequential reads > 1 byte
		return self.bus.read_i2c_block_data(self.addr, data, n)


class ioexpander:
	def __init__(self):
		pass

class lcd_i2c_pcf8574:
	# Define LCD device constants
	LCD_WIDTH = 16    # Default characters per line
	width = LCD_WIDTH
	ScrollSpeed = 0.3       # Default scroll speed

	#initializes objects and lcd

	# LCD Commands
	LCD_CLEARDISPLAY   = 0x01
	LCD_RETURNHOME	   = 0x02
	LCD_ENTRYMODESET   = 0x04
	LCD_DISPLAYCONTROL = 0x08
	LCD_CURSORSHIFT    = 0x10
	LCD_FUNCTIONSET	   = 0x20
	LCD_SETCGRAMADDR   = 0x40
	LCD_SETDDRAMADDR   = 0x80

	# Flags for display on/off control
	LCD_DISPLAYON   = 0x04
	LCD_DISPLAYOFF	= 0x00
	LCD_CURSORON	= 0x02
	LCD_CURSOROFF   = 0x00
	LCD_BLINKON	= 0x01
	LCD_BLINKOFF	= 0x00

	# Flags for display entry mode
	LCD_ENTRYRIGHT	  = 0x00
	LCD_ENTRYLEFT	  = 0x02
	LCD_ENTRYSHIFTINCREMENT = 0x01
	LCD_ENTRYSHIFTDECREMENT = 0x00

	# Flags for display/cursor shift
	LCD_DISPLAYMOVE = 0x08
	LCD_CURSORMOVE  = 0x00
	LCD_MOVERIGHT   = 0x04
	LCD_MOVELEFT	= 0x00
	
	# flags for function set
	LCD_8BITMODE = 0x10
	LCD_4BITMODE = 0x00

	LCD_LINE_1 = 0x01 # LCD RAM address for the 1st line
	LCD_LINE_2 = 0x02 # LCD RAM address for the 2nd line
	LCD_LINE_3 = 0x03 # LCD RAM address for the 3rd line
	LCD_LINE_4 = 0x04 # LCD RAM address for the 4th line

        LCD_2LINE = 0x08
        LCD_1LINE = 0x00

	LCD_5x10DOTS = 0x04
	LCD_5x8DOTS = 0x00

	# flags for backlight control
	LCD_BACKLIGHT = 0x08
	LCD_NOBACKLIGHT = 0x00

	EN = 0b00000100  # Enable bit
	RW = 0b00000010  # Read/Write bit
	RS = 0b00000001  # Register select bit

	'''
	new pinout:
	----------
	0x80	P7 -  - D7	 
	0x40	P6 -  - D6
	0x20	P5 -  - D5
	0x10	P4 -  - D4	
		-----------
	0x08	P3 -  - BL   Backlight ???
	0x04	P2 -  - EN   Starts Data read/write 
	0x02	P1 -  - RW   low: write, high: read   
	0x01	P0 -  - RS   Register Select: 0: Instruction Register (IR) (AC when read), 1: data register (DR)
	'''

	# custom character settings
	customCharMapping = {
                    "[Oslash]": {"address": 0, 
                                "character":
                                [
                                0b00001,
                                0b01110,
                                0b10011,
                                0b10101,
                                0b11001,
                                0b01110,
                                0b10000,
                                0b00000]},
                    "[oslash]": {"address": 1,
                                "character":
                                [
                                0b00000,
                                0b00001,
                                0b01110,
                                0b10101,
                                0b10101,
                                0b01110,
                                0b10000,
                                0b00000]},
                    "[AElig]": {"address": 4,
                                "character":
                                [
                                0b01111,
                                0b10100,
                                0b10100,
                                0b11111,
                                0b10100,
                                0b10100,
                                0b10111,
                                0b00000]},
                    "[aelig]": {"address": 5,
                                "character":
                                [
                                0b00000,
                                0b00000,
                                0b11010,
                                0b00101,
                                0b01111,
                                0b10100,
                                0b01111,
                                0b00000]},
                    "[Aring]": {"address": 2,
                                "character":
                                [
                                0b01110,
                                0b00000,
                                0b01110,
                                0b10001,
                                0b11111,
                                0b10001,
                                0b10001,
                                0b00000]},
                    "[aring]": {"address": 3,
                                "character":
                                [
                                0b00110,
                                0b00000,
                                0b01110,
                                0b00001,
                                0b01111,
                                0b10001,
                                0b01111,
				0b00000]}
        }    
	
	# function to set custom characters to 16x2 LCD screen
	def setCustomChar(self):
		lcdSleep = 0.0005
		for key in self.customCharMapping.keys():
			address = self.customCharMapping[key]["address"] << 3
			character = self.customCharMapping[key]["character"]

			self.lcd_device.bus.write_byte(0x27, 0b1100 | 0b01000000 | (address & 0x30))
			sleep(lcdSleep)
			self.lcd_device.bus.write_byte(0x27, 0b1000 | 0b01000000 | (address & 0x30))
			sleep(lcdSleep)
			self.lcd_device.bus.write_byte(0x27, 0b1100 |(address & 0x0F) << 4)
			sleep(lcdSleep)
			self.lcd_device.bus.write_byte(0x27, 0b1000 |(address & 0x0F) << 4)
			sleep(lcdSleep)
        
			for i in range(0,len(character)):
				code = character[i]
				self.lcd_device.bus.write_byte(0x27, 0b1101 |(code & 0xF0))
				sleep(lcdSleep)
				self.lcd_device.bus.write_byte(0x27, 0b1001 |(code & 0xF0))
				sleep(lcdSleep)
				self.lcd_device.bus.write_byte(0x27, 0b1101 |(code & 0x0F) << 4)
				sleep(lcdSleep)
				self.lcd_device.bus.write_byte(0x27, 0b1001 |(code & 0x0F) << 4)
				sleep(lcdSleep)
        

	def __init__(self,boardrevision=1):
		'''
		device writes!
		crosscheck also http://www.monkeyboard.org/tutorials/81-display/70-usb-serial-to-hd44780-lcd
		here a sequence is listed
		'''
		addr=0x27
		port=1
		withBacklight=True
		withOneTimeInit=True
		self.displayshift  = (self.LCD_CURSORMOVE |
					   self.LCD_MOVERIGHT)
		self.displaymode   = (self.LCD_ENTRYLEFT |
					   self.LCD_ENTRYSHIFTDECREMENT)
		self.displaycontrol = (self.LCD_DISPLAYON |
					   self.LCD_CURSOROFF |
					   self.LCD_BLINKOFF)

		if withBacklight:
			self.blFlag=self.LCD_BACKLIGHT
		else:
			self.blFlag=self.LCD_NOBACKLIGHT
		
		
		self.lcd_device = i2c_device(addr, port)
		
		# we can initialize the display only once after it had been powered on
		if not self._isInitialised():
			self.init_lcd()

		self.lcd_write(self.LCD_DISPLAYCONTROL | self.displaycontrol)   # 0x08 + 0x4 = 0x0C
		self.lcd_write(self.LCD_ENTRYMODESET   | self.displaymode)  	# 0x06
		self.lcd_write(self.LCD_CLEARDISPLAY)				# 0x01
		self.lcd_write(self.LCD_CURSORSHIFT    | self.displayshift)	# 0x14 
		self.lcd_write(self.LCD_RETURNHOME)
		self.setCustomChar()
		return

	# Indicate 
	def _isInitialised(self):
		initialised = False
		if not os.path.isfile("/tmp/pcf8574") or os.path.getsize("/tmp/pcf8574") == 0:
			self.execCommand ("echo Initialised > /tmp/pcf8574")
		else:
			initialised = True
		return initialised

	# This routine initialises the LCD and must only called after swithon
	def init_lcd(self):
		print "Initialise LCD"
		self.lcd_device.write(0x20) 
		self.lcd_strobe()
		sleep(0.0100) # TODO: Not clear if we have to wait that long
		self.lcd_write(self.LCD_FUNCTIONSET | self.LCD_4BITMODE  | self.LCD_2LINE | self.LCD_5x8DOTS) # 0x28
		return

	def init(self, boardrevision):
		return
			
	def backlight(self, backlight):
		return
			
			
	# clocks EN to latch command
	def lcd_strobe(self):
		self.lcd_device.write((self.lcd_device.read() | self.EN | self.blFlag)) # | 0b0000 0100 # set "EN" high
		self.lcd_device.write(( (self.lcd_device.read() | self.blFlag) & 0xFB)) # & 0b1111 1011 # set "EN" low

	# write data to lcd in 4 bit mode, 2 nibbles
	# high nibble is sent first
	def lcd_write(self, cmd):
		
		#write high nibble first
		self.lcd_device.write( (cmd & 0xF0) | self.blFlag )
		hi= self.lcd_device.read()
		self.lcd_strobe()
		
		# write low nibble second ...
		self.lcd_device.write( (cmd << 4) | self.blFlag )
		lo= self.lcd_device.read()
		self.lcd_strobe()
		self.lcd_device.write(self.blFlag)
	
	
	# write a character to lcd (or character rom) 0x09: backlight | RS=DR
	# works as expected
	def lcd_write_char(self, charvalue):
		controlFlag = self.blFlag | self.RS
		
		# write high nibble
		self.lcd_device.write((controlFlag | (charvalue & 0xF0)))
		self.lcd_strobe()
		
		# write low nibble
		self.lcd_device.write((controlFlag | (charvalue << 4)))
		self.lcd_strobe()
		self.lcd_device.write(self.blFlag)


	# put char function
	def lcd_putc(self, char):
		self.lcd_write_char(ord(char))

	def _setDDRAMAdress(self, line, col):
		# we write to the Data Display RAM (DDRAM)		
		# TODO: Factor line offsets for other display organizations; this is for 20x4 only 
		if line == 1:
			self.lcd_write(self.LCD_SETDDRAMADDR | (0x00 + col) )
		if line == 2:
			self.lcd_write(self.LCD_SETDDRAMADDR | (0x40 + col) )
		if line == 3:
			self.lcd_write(self.LCD_SETDDRAMADDR | (0x14 + col) )
		if line == 4:
			self.lcd_write(self.LCD_SETDDRAMADDR | (0x54 + col) )
		

	# put string function
	def lcd_puts(self, string, line):
		self._setDDRAMAdress(line, 0)
		for char in string:
			self.lcd_putc(char)

	# clear lcd and set to home
	def clear(self):
		# self.lcd_write(0x10)
		self.lcd_write(self.LCD_CLEARDISPLAY)
		# self.lcd_write(0x20)
		self.lcd_write(self.LCD_RETURNHOME)

	# add custom characters (0 - 7)
	def lcd_load_custon_chars(self, fontdata):
		self.lcd_device.bus.write(0x40);
		for char in fontdata:
			for line in char:
				self.lcd_write_char(line)

# Changes - Bob Rathbone
	# Set the display width
	def setWidth(self,width):
		self.width = width
		return

	# Display Line 1 on LCD
	def line1(self,text):
		self._writeLine(self.LCD_LINE_1,text)
		return

	# Display Line 2 on LCD
	def line2(self,text):
		self._writeLine(self.LCD_LINE_2,text)
		return

	# Display Line 3 on LCD
	def line3(self,text):
		self._writeLine(self.LCD_LINE_3,text)
		return

	# Display Line 4 on LCD
	def line4(self,text):
		self._writeLine(self.LCD_LINE_4,text)
		return

	# Write a single line to the LCD
	def _writeLine(self,line,text):
		if len(text) < self.width:
			text = text.ljust(self.width, ' ')
		self.lcd_puts(text[:self.width],line)
		return

	# Scroll message on line 1
	def scroll1(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_1,interrupt)
		return

	# Scroll message on line 2
	def scroll2(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_2,interrupt)
		return

	# Scroll message on line 3
	def scroll3(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_3,interrupt)
		return

	# Scroll message on line 4
	def scroll4(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_4,interrupt)
		return


	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self._writeLine(line,mytext[0:self.width + 1])

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
				self._writeLine(line,mytext[i:i+self.width])
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

	def setScrollSpeed(self,speed):
		return

	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

# Test the class
def main():	

	# No interrupt for scrolling
	def no_interrupt():
		return False

	while True:
            try:
		lcd = lcd_i2c_pcf8574()  
		lcd.init(1)
		lcd.setWidth(20)
		lcd.line1("Bob Rathbone ABCDEFGHIJK")
		lcd.line2("Line 2 abcdefghijklmno")
		lcd.line3("Line 3 abcdefghijklmno")
		lcd.scroll4("Line 4 abcdefghijklmnopqrstuvwxyz",no_interrupt)

		sleep(2)
		lcd.lcd_puts(strftime("%Y-%m-%d %H:%M:%S", gmtime()),4)
		lcd.clear()
		lcd.line1("    Simple Clock    ")
		while True:
			lcd.line3(strftime("%Y-%m-%d %H:%M:%S ", localtime()))
			sleep(1)

            except KeyboardInterrupt:
		lcd.line1("Test ended")
		lcd.line2("")
		lcd.line3("")
		lcd.line4("")
                print "\nExit"
                sys.exit(0)

if __name__ == '__main__':
	main()


