#!/usr/bin/env python
#
# LCD driver program using the lcd_i2c_class.py
# $Id: test_i2c_lcd.py,v 1.2 2014/11/02 09:48:06 bob Exp $
# Adapted from RpiLcdBackpack from Paul Knox-Kennedy
# at Adafruit Industries
#
# Author : Bob Rathbone
# Site	 : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#						 The authors shall not be liable for any loss or damage however caused.
#

from lcd_i2c_class import lcd_i2c
from time import sleep

def no_interrupt():
	return False

if __name__ == '__main__':
	lcd = lcd_i2c()
	lcd.init()
	lcd.backlight(True)
	lcd.blink(False)
	lcd.cursor(False)
	lcd.clear()
	lcd.line1("Bob Rathbone")
	lcd.line2("Hello World!")
	lcd.blink(True)
	sleep(3)
	lcd.blink(False)
	lcd.scroll2("Bob Rathbone ABCDEFGHIJKLMNOPQRSTUVWXYZ", no_interrupt)
	lcd.line1("Finished!")
	lcd.line2("test!")
	lcd.backlight(False)

