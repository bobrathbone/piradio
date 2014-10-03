#!/usr/bin/python
# -*- coding: latin-1 -*-

# LCD class for  Adafruit RGB-backlit LCD plate for Raspberry Pi.
# Adapted by Bob Rathbone from code by Adafruit Industries.  MIT license.
# $Id: ada_lcd_class.py,v 1.4 2013/07/02 13:16:54 bob Exp $

# Original code based on code from lrvick and LiquidCrystal.
# lrvic - https://github.com/lrvick/raspi-hd44780/blob/master/hd44780.py
# LiquidCrystal - https://github.com/arduino/Arduino/blob/master/libraries/LiquidCrystal/LiquidCrystal.cpp

from i2c_class import i2c
from time import sleep
from log_class import Log

log = Log()

class Adafruit_lcd(i2c):


	# ----------------------------------------------------------------------
	# Constants

	# Port expander registers
	MCP23017_IOCON_BANK0	= 0x0A  # IOCON when Bank 0 active
	MCP23017_IOCON_BANK1	= 0x15  # IOCON when Bank 1 active
	# These are register addresses when in Bank 1 only:
	MCP23017_GPIOA		  = 0x09
	MCP23017_IODIRB		 = 0x10
	MCP23017_GPIOB		  = 0x19

	# Port expander input pin definitions
	MENU  = 0
	RIGHT = 1
	DOWN  = 2
	UP    = 3
	LEFT  = 4

	# LED colors
	OFF = 0x00
	RED = 0x01
	GREEN = 0x02
	BLUE  = 0x04
	YELLOW = RED + GREEN
	TEAL   = GREEN + BLUE
	VIOLET = RED + BLUE
	WHITE  = RED + GREEN + BLUE
	ON = RED + GREEN + BLUE

	# LCD Commands
	LCD_CLEARDISPLAY  = 0x01
	LCD_RETURNHOME	  = 0x02
	LCD_ENTRYMODESET  = 0x04
	LCD_DISPLAYCONTROL = 0x08
	LCD_CURSORSHIFT   = 0x10
	LCD_FUNCTIONSET	  = 0x20
	LCD_SETCGRAMADDR  = 0x40
	LCD_SETDDRAMADDR  = 0x80

	# Flags for display on/off control
	LCD_DISPLAYON	= 0x04
	LCD_DISPLAYOFF	= 0x00
	LCD_CURSORON	= 0x02
	LCD_CURSOROFF	= 0x00
	LCD_BLINKON	= 0x01
	LCD_BLINKOFF	= 0x00

	# Flags for display entry mode
	LCD_ENTRYRIGHT = 0x00
	LCD_ENTRYLEFT = 0x02
	LCD_ENTRYSHIFTINCREMENT = 0x01
	LCD_ENTRYSHIFTDECREMENT = 0x00

	# Flags for display/cursor shift
	LCD_DISPLAYMOVE = 0x08
	LCD_CURSORMOVE  = 0x00
	LCD_MOVERIGHT   = 0x04
	LCD_MOVELEFT	= 0x00

	LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
	LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
	LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
	LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

	width = 16	# Line width

	# Variable values
	displayUmlauts = True	# If false translate to ae oe etc.
	RawMode = False		# Test only
	ScrollSpeed = 0.3 	# Scroll speed

	# ----------------------------------------------------------------------
	# Constructor


	def __init__(self, busnum=-1, addr=0x20, debug=False):

		log.init("radio") 
		self.i2c = i2c(addr, busnum, debug)

		# I2C is relatively slow.  MCP output port states are cached
		# so we don't need to constantly poll-and-change bit states.
		self.porta, self.portb, self.ddrb = 0, 0, 0b00010000

		# Set MCP23017 IOCON register to Bank 0 with sequential operation.
		# If chip is already set for Bank 0, this will just write to OLATB,
		# which won't seriously bother anything on the plate right now
		# (blue backlight LED will come on, but that's done in the next
		# step anyway).
		self.i2c.bus.write_byte_data(
		  self.i2c.address, self.MCP23017_IOCON_BANK1, 0)

		# Brute force reload ALL registers to known state.  This also
		# sets up all the input pins, pull-ups, etc. for the Pi Plate.
		self.i2c.bus.write_i2c_block_data(
		  self.i2c.address, 0, 
		  [ 0b00111111,   # IODIRA	R+G LEDs=outputs, buttons=inputs
			self.ddrb ,   # IODIRB	LCD D7=input, Blue LED=output
			0b00111111,   # IPOLA	 Invert polarity on button inputs
			0b00000000,   # IPOLB
			0b00000000,   # GPINTENA  Disable interrupt-on-change
			0b00000000,   # GPINTENB
			0b00000000,   # DEFVALA
			0b00000000,   # DEFVALB
			0b00000000,   # INTCONA
			0b00000000,   # INTCONB
			0b00000000,   # IOCON
			0b00000000,   # IOCON
			0b00111111,   # GPPUA	 Enable pull-ups on buttons
			0b00000000,   # GPPUB
			0b00000000,   # INTFA
			0b00000000,   # INTFB
			0b00000000,   # INTCAPA
			0b00000000,   # INTCAPB
			self.porta,   # GPIOA
			self.portb,   # GPIOB
			self.porta,   # OLATA	 0 on all outputs; side effect of
			self.portb ]) # OLATB	 turning on R+G+B backlight LEDs.

		# Switch to Bank 1 and disable sequential operation.
		# From this point forward, the register addresses do NOT match
		# the list immediately above.  Instead, use the constants defined
		# at the start of the class.  Also, the address register will no
		# longer increment automatically after this -- multi-byte
		# operations must be broken down into single-byte calls.
		self.i2c.bus.write_byte_data(
		  self.i2c.address, self.MCP23017_IOCON_BANK0, 0b10100000)

		self.displayshift   = (self.LCD_CURSORMOVE |
							   self.LCD_MOVERIGHT)
		self.displaymode	= (self.LCD_ENTRYLEFT |
							   self.LCD_ENTRYSHIFTDECREMENT)
		self.displaycontrol = (self.LCD_DISPLAYON |
							   self.LCD_CURSOROFF |
							   self.LCD_BLINKOFF)

		self.write(0x33) # Init
		self.write(0x32) # Init
		self.write(0x28) # 2 line 5x8 matrix
		self.write(self.LCD_CLEARDISPLAY)
		self.write(self.LCD_CURSORSHIFT	| self.displayshift)
		self.write(self.LCD_ENTRYMODESET   | self.displaymode)
		self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)
		self.write(self.LCD_RETURNHOME)


	# ----------------------------------------------------------------------
	# Write operations

	# The LCD data pins (D4-D7) connect to MCP pins 12-9 (PORTB4-1), in
	# that order.  Because this sequence is 'reversed,' a direct shift
	# won't work.  This table remaps 4-bit data values to MCP PORTB
	# outputs, incorporating both the reverse and shift.
	flip = ( 0b00000000, 0b00010000, 0b00001000, 0b00011000,
			 0b00000100, 0b00010100, 0b00001100, 0b00011100,
			 0b00000010, 0b00010010, 0b00001010, 0b00011010,
			 0b00000110, 0b00010110, 0b00001110, 0b00011110 )

	# Low-level 4-bit interface for LCD output.  This doesn't actually
	# write data, just returns a byte array of the PORTB state over time.
	# Can concatenate the output of multiple calls (up to 8) for more
	# efficient batch write.
	def out4(self, bitmask, value):
		hi = bitmask | self.flip[value >> 4]
		lo = bitmask | self.flip[value & 0x0F]
		return [hi | 0b00100000, hi, lo | 0b00100000, lo]


	# The speed of LCD accesses is inherently limited by I2C through the
	# port expander.  A 'well behaved program' is expected to poll the
	# LCD to know that a prior instruction completed.  But the timing of
	# most instructions is a known uniform 37 mS.  The enable strobe
	# can't even be twiddled that fast through I2C, so it's a safe bet
	# with these instructions to not waste time polling (which requires
	# several I2C transfers for reconfiguring the port direction).
	# The D7 pin is set as input when a potentially time-consuming
	# instruction has been issued (e.g. screen clear), as well as on
	# startup, and polling will then occur before more commands or data
	# are issued.

	pollables = ( LCD_CLEARDISPLAY, LCD_RETURNHOME )

	# Write byte, list or string value to LCD
	def write(self, value, char_mode=False):
		""" Send command/data to LCD """

		# If pin D7 is in input state, poll LCD busy flag until clear.
		if self.ddrb & 0b00010000:
			lo = (self.portb & 0b00000001) | 0b01000000
			hi = lo | 0b00100000 # E=1 (strobe)
			self.i2c.bus.write_byte_data(
			  self.i2c.address, self.MCP23017_GPIOB, lo)
			while True:
				# Strobe high (enable)
				self.i2c.bus.write_byte(self.i2c.address, hi)
				# First nybble contains busy state
				bits = self.i2c.bus.read_byte(self.i2c.address)
				# Strobe low, high, low.  Second nybble (A3) is ignored.
				self.i2c.bus.write_i2c_block_data(
				  self.i2c.address, self.MCP23017_GPIOB, [lo, hi, lo])
				if (bits & 0b00000010) == 0: break # D7=0, not busy
			self.portb = lo

			# Polling complete, change D7 pin to output
			self.ddrb &= 0b11101111
			self.i2c.bus.write_byte_data(self.i2c.address,
			  self.MCP23017_IODIRB, self.ddrb)

		bitmask = self.portb & 0b00000001   # Mask out PORTB LCD control bits
		if char_mode: bitmask |= 0b10000000 # Set data bit if not a command

		# If string or list, iterate through multiple write ops
		if isinstance(value, str):
			last = len(value) - 1 # Last character in string
			data = []			 # Start with blank list
			for i, v in enumerate(value): # For each character...
				# Append 4 bytes to list representing PORTB over time.
				# First the high 4 data bits with strobe (enable) set
				# and unset, then same with low 4 data bits (strobe 1/0).
				data.extend(self.out4(bitmask, ord(v)))
				# I2C block data write is limited to 32 bytes max.
				# If limit reached, write data so far and clear.
				# Also do this on last byte if not otherwise handled.
				if (len(data) >= 32) or (i == last):
					self.i2c.bus.write_i2c_block_data(
					  self.i2c.address, self.MCP23017_GPIOB, data)
					self.portb = data[-1] # Save state of last byte out
					data	   = []	   # Clear list for next iteration
		elif isinstance(value, list):
			# Same as above, but for list instead of string
			last = len(value) - 1
			data = []
			for i, v in enumerate(value):
				data.extend(self.out4(bitmask, v))
				if (len(data) >= 32) or (i == last):
					self.i2c.bus.write_i2c_block_data(
					  self.i2c.address, self.MCP23017_GPIOB, data)
					self.portb = data[-1]
					data	   = []
		else:
			# Single byte
			data = self.out4(bitmask, value)
			self.i2c.bus.write_i2c_block_data(
			  self.i2c.address, self.MCP23017_GPIOB, data)
			self.portb = data[-1]

		# If a poll-worthy instruction was issued, reconfigure D7
		# pin as input to indicate need for polling on next call.
		if (not char_mode) and (value in self.pollables):
			self.ddrb |= 0b00010000
			self.i2c.bus.write_byte_data(self.i2c.address,
			  self.MCP23017_IODIRB, self.ddrb)


	# ----------------------------------------------------------------------
	# Utility methods

	def begin(self, cols, lines):
		self.currline = 0
		self.numlines = lines
		self.clear()


	# Puts the MCP23017 back in Bank 0 + sequential write mode so
	# that other code using the 'classic' library can still work.
	# Any code using this newer version of the library should
	# consider adding an atexit() handler that calls this.
	def stop(self):
		self.porta = 0b11000000  # Turn off LEDs on the way out
		self.portb = 0b00000001
		sleep(0.0015)
		self.i2c.bus.write_byte_data(
		  self.i2c.address, self.MCP23017_IOCON_BANK1, 0)
		self.i2c.bus.write_i2c_block_data(
		  self.i2c.address, 0, 
		  [ 0b00111111,   # IODIRA
			self.ddrb ,   # IODIRB
			0b00000000,   # IPOLA
			0b00000000,   # IPOLB
			0b00000000,   # GPINTENA
			0b00000000,   # GPINTENB
			0b00000000,   # DEFVALA
			0b00000000,   # DEFVALB
			0b00000000,   # INTCONA
			0b00000000,   # INTCONB
			0b00000000,   # IOCON
			0b00000000,   # IOCON
			0b00111111,   # GPPUA
			0b00000000,   # GPPUB
			0b00000000,   # INTFA
			0b00000000,   # INTFB
			0b00000000,   # INTCAPA
			0b00000000,   # INTCAPB
			self.porta,   # GPIOA
			self.portb,   # GPIOB
			self.porta,   # OLATA
			self.portb ]) # OLATB


	def clear(self):
		self.write(self.LCD_CLEARDISPLAY)


	def home(self):
		self.write(self.LCD_RETURNHOME)


	row_offsets = ( 0x00, 0x40, 0x14, 0x54 )
	def setCursor(self, col, row):
		if row > self.numlines: row = self.numlines - 1
		elif row < 0:		   row = 0
		self.write(self.LCD_SETDDRAMADDR | (col + self.row_offsets[row]))


	def message(self, text):
		""" Send string to LCD. Newline wraps to second line"""
		lines = str(text).split('\n')	 # Split at newline(s)
		for i, line in enumerate(lines): # For each substring...
			if i > 0:		 # If newline(s),
				self.write(0xC0) #  set DDRAM address to 2nd line
			self.write(line, True)	 # Issue substring

	# Display Line 1 on LCD
	def line1(self,text):
		self._write(text,self.LCD_LINE_1) 	# Set DDRAM address to 2nd line
		return

	# Display Line 1 on LCD
	def line2(self,text):
		self._write(text,self.LCD_LINE_2)	# Set DDRAM address to 2nd line
		return

	# Display Line 1 on LCD
	def _write(self,text,line):
		if self.RawMode:
			mytext = text
		else:
			mytext = self.translateChars(text)

		self.write(line)		# Set DDRAM address to 2nd line
		self.write("                    ", True)
		self.write(line)		# Set DDRAM address to 2nd line
		self.write(mytext, True)		# Issue substring
		return

	# Scroll message on line 1
	def scroll1(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_1,interrupt)
		return

	# Scroll message on line 2
	def scroll2(self,mytext,interrupt):
		self._scroll(mytext,self.LCD_LINE_2,interrupt)
		return

	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,mytext,line,interrupt):
		ilen = len(mytext)
		skip = False

		self._write(mytext[0:self.width + 1],line)
	
		if (ilen <= self.width):
			skip = True

		if not skip:
			for i in range(0, 5):
				sleep(self.ScrollSpeed)
				if interrupt():
					skip = True
					break

		if not skip:
			for i in range(0, ilen - self.width + 1 ):
				self._write(mytext[i:i+self.width],line)
				if interrupt():
					skip = True
					break
				sleep(0.2)

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


	def backlight(self, color):
		c = ~color
		self.porta = (self.porta & 0b00111111) | ((c & 0b011) << 6)
		self.portb = (self.portb & 0b11111110) | ((c & 0b100) >> 2)
		# Has to be done as two writes because sequential operation is off.
		self.i2c.bus.write_byte_data(
		  self.i2c.address, self.MCP23017_GPIOA, self.porta)
		self.i2c.bus.write_byte_data(
		  self.i2c.address, self.MCP23017_GPIOB, self.portb)


	# Read state of single button
	def buttonPressed(self, b):
		button =  (self.i2c.readU8(self.MCP23017_GPIOA) >> b) & 1
		return button

	# Read and return bitmask of combined button state
	def buttons(self):
		return self.i2c.readU8(self.MCP23017_GPIOA) & 0b11111

	# Set the display width
	def setWidth(self,width):
		self.width = width
		return

	# Set display umlauts or not
	def displayUmlauts(self,value):
		self.displayUmlauts = value
		return

	# Set raw mode on (No translation)
	def setRawMode(self,value):
		self.RawMode = value
		return

        # Translate special characters (umlautes etc) to LCD values
        # See standard character patterns for LCD display
        def translateChars(self,sp):
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
			s = s.replace(chr(228), "ae")       	# a umlaut
                        s = s.replace(chr(223), "ss")           # Sharp s
                        s = s.replace(chr(246), "oe")           # o umlaut
                        s = s.replace(chr(252), "ue")           # u umlaut

                return s

# End of class
