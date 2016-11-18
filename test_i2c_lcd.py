#!/usr/bin/env python
#
# LCD driver program using the lcd_i2c_class.py
# $Id: test_i2c_lcd.py,v 1.7 2016/06/25 10:37:43 bob Exp $
# Adapted from RpiLcdBackpack from Paul Knox-Kennedy
# at Adafruit Industries
#
# Author : Bob Rathbone
# Site	 : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#

import sys
from lcd_i2c_class import lcd_i2c
from lcd_i2c_pcf8574 import lcd_i2c_pcf8574

from time import sleep

def no_interrupt():
	return False

if __name__ == '__main__':
  	i2c_address = 0x00
	print "I2C LCD test program"
	print "1 = Adafruit I2C backpack"
	print "2 = PCF8574 I2C backpack"
	response = raw_input("Select type of backpack: ")
	if int(response) is 1:
		lcd = lcd_i2c()
		i2c_address = 0x20

	elif int(response) is 2:
		lcd = lcd_i2c_pcf8574()
		i2c_address = 0x27
	else:
		print "Invalid selection!" 
		sys.exit(1)

	print "I2C address:", hex(i2c_address)

	try:
		if int(response) is 2:
			lcd.init(address=i2c_address)
		else:
			lcd.init()
	except: 
		print "Could not initialise LCD, check selection!" 
		sys.exit(1)

	lcd.setWidth(20)
	lcd.backlight(True)
	lcd.blink(False)
	lcd.cursor(False)
	lcd.clear()
	lcd.line1("Bob Rathbone")
	lcd.line2("Hello World!")
	lcd.blink(True)
	sleep(3)
	lcd.blink(False)
	lcd.line3("Line 3 1923456789012")
	lcd.line4("!@#$%^&*(_[]\/?<>:?+")
	lcd.scroll2("Bob Rathbone ABCDEFGHIJKLMNOPQRSTUVWXYZ", no_interrupt)
	sleep(3)
	lcd.line1("Finished test!")
	lcd.line2("")
	lcd.line3("")
	lcd.line4("")
	sleep(1)
	lcd.backlight(False)
	sleep(1)
	lcd.backlight(True)
	print "Test finished"

