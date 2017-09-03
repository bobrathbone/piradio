#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# LCD test program using the lcd_class.py 
# Use this program to test LCD wiring
#
# $Id: test_lcd.py,v 1.14 2017/04/25 10:20:21 bob Exp $
# 
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys
import os
import atexit
import traceback
import RPi.GPIO as GPIO
from lcd_class import Lcd
from translate_class import Translate

stderr = sys.stderr.write;

lcd = Lcd()
translate = Translate()

# Try to trap any exit errors and cleanup GPIO
def exit_fn():
	if not traceback.format_exc().startswith('None'):
		s=traceback.format_exc()

# Register
atexit.register(exit_fn)

def interrupt():
        return False

boardrevision = 2
stderr("Are you using an old revision 1 board y/n: ")
answer = raw_input("")
if answer == 'y':
	boardrevision = 1

print "Use Ctl-C to exit"

lcd.init(boardrevision)
width = lcd.getWidth()
if width is 0:
	print "Set the lcd_width parameter in /etc/radiod.conf"
	sys.exit(1)

lcd.setWidth(width)

if len(sys.argv) > 1:
	text = translate.escape(sys.argv[1])
else:
	text = "Bob Rathbone"

lcd.line3("Line 3")
lcd.line4("Line 4")

while True:
	try:
		if len(text) > width:
			lcd.scroll1(text,interrupt)
		else:
			lcd.line1(text)

		lcd.scroll2("Line 2: abcdefghijklmnopqrstuvwxyz 0123456789",interrupt) 

	except KeyboardInterrupt:
		print "\nExit"
		GPIO.setwarnings(False)
		GPIO.cleanup()
		sys.exit(0)

# End of test program
