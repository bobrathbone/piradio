#!/usr/bin/env python
#
# LCD test program for the lcd_i2c_class.py class
# $Id: lcd_i2c_pcf8574.py,v 1.2 2016/06/25 10:37:43 bob Exp $
# PCF8574 I2C LCD Backpack LCD class
# Use this program to test I2C Backpack LCD wiring
# Adapted from RpiLcdBackpack from Paul Knox-Kennedy by Lubos Ruckl and Bob Rathbone
# at Adafruit Industries
#
# Author : Bob Rathbone
# Site     : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#                         The authors shall not be liable for any loss or damage however caused.
#

import smbus, time
from subprocess import * 
from time import sleep, strftime
from datetime import datetime

class lcd_i2c_pcf8574:
    ADDRESS = 0x27 #for "Serial Interface IIC I2C TWI Adapter Module" (eBay)
    i2c_address = ADDRESS
    #Bus = None
    # commands
    __CLEARDISPLAY=0x01
    __RETURNHOME=0x02
    __ENTRYMODESET=0x04
    __DISPLAYCONTROL=0x08
    __CURSORSHIFT=0x10
    __FUNCTIONSET=0x20
    __SETCGRAMADDR=0x40
    __SETDDRAMADDR=0x80

    # flags for display entry mode
    __ENTRYRIGHT=0x00
    __ENTRYLEFT=0x02
    __ENTRYSHIFTINCREMENT=0x01
    __ENTRYSHIFTDECREMENT=0x00

    # flags for display on/off control
    __DISPLAYON=0x04
    __DISPLAYOFF=0x00
    __CURSORON=0x02
    __CURSOROFF=0x00
    __BLINKON=0x01
    __BLINKOFF=0x00

    # flags for display/cursor shift
    __DISPLAYMOVE=0x08
    __CURSORMOVE=0x00
    __MOVERIGHT=0x04
    __MOVELEFT=0x00

    # flags for function set
    __8BITMODE=0x10
    __4BITMODE=0x00
    __2LINE=0x08
    __1LINE=0x00
    __5x10DOTS=0x04
    __5x8DOTS=0x00

    # flags for backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00

    # control bits
    En = 0b00000100 # Enable bit
    Rw = 0b00000010 # Read/Write bit
    Rs = 0b00000001 # Register select bit

    # Define LCD device constants
    LCD_WIDTH = 16    # Default characters per line

    LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
    LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
    LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
    LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

    width = LCD_WIDTH
    ScrollSpeed = 0.3       # Default scroll speed


    def write_cmd(self, cmd):
        #self.__bus.write_byte(self.ADDRESS, cmd)	# Now configurable 
        self.__bus.write_byte(self.i2c_address, cmd)
        sleep(0.0001)


    # clocks EN to latch command
    def lcd_strobe(self, data):
        self.write_cmd(data | self.En | self._backlight)
        sleep(.0005)
        self.write_cmd(((data & ~self.En) | self._backlight))
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.write_cmd(data | self._backlight)
        self.lcd_strobe(data)

    # write a command to lcd
    def writeCommand(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        #self.lcd_write_four_bits(data)
        #self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # __init__
    def __init__(self):
        self._backlight = self.LCD_BACKLIGHT

    # Initialisation routine
    def init(self, board_rev=2, address=0x27):
        bus = 1
        if board_rev == 1:
            bus = 0

	if address > 0x00:
		self.i2c_address = address
        
        self.__bus=smbus.SMBus(bus)

        self.writeCommand(0x03)
        self.writeCommand(0x03)
        self.writeCommand(0x03)
        self.writeCommand(0x02)

        self.__displayfunction = self.__FUNCTIONSET | self.__2LINE | self.__5x8DOTS | self.__4BITMODE
        self.__displaycontrol = self.__DISPLAYCONTROL | self.__DISPLAYON | self.__CURSORON | self.__BLINKON
        self.writeCommand(self.__displayfunction)
        self.writeCommand(self.__DISPLAYCONTROL | self.__DISPLAYON)
        self.writeCommand(self.__CLEARDISPLAY)
        self.writeCommand(self.__ENTRYMODESET | self.__ENTRYLEFT)
        sleep(0.2)        
       
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
    def _writeLine(self, line, text):
        self.writeCommand(line)
        if len(text) < self.width:
            text = text.ljust(self.width, ' ')
        self.message(text[:self.width])
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
                time.sleep(0.2)
                if interrupt():
                    skip = True
                    break

        if not skip:
            for i in range(0, ilen - self.width + 1 ):
                self._writeLine(line,mytext[i:i+self.width])
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



    # Switch back light on and off
    def backlight(self,on):
        if on:
            self._backlight = self.LCD_BACKLIGHT
        else:
            self._backlight = self.LCD_NOBACKLIGHT
        self.writeCommand(self.__displayfunction)


    # Clear display
    def clear(self):
        self.writeCommand(self.__CLEARDISPLAY)
        time.sleep(0.002)


    # Blink cursor
    def blink(self, on):
        if on:
            self.__displaycontrol |= self.__BLINKON
        else:
            self.__displaycontrol &= ~self.__BLINKON
        self.writeCommand(self.__displaycontrol)

    def noCursor(self):
        self.writeCommand(self.__displaycontrol)

    def cursor(self, on):
        if on:
            self.__displaycontrol |= self.__CURSORON
        else:
            self.__displaycontrol &= ~self.__CURSORON
        self.writeCommand(self.__displaycontrol)

    def message(self, text):
        for char in text:
            if char == '\n':
                self.writeCommand(0xC0)
            else:
                self.writeCommand(ord(char), self.Rs)

    # Set the display width
    def setWidth(self,width):
        self.width = width
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

# End of lcd_i2c_class
