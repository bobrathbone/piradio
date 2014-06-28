#!/usr/bin/env python
#
# Raspberry Pi Rotary Test Encoder Class
# $Id: test_rotary_class.py,v 1.2 2014/03/25 19:42:00 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys
import time
from rotary_class import RotaryEncoder

# Switch definitions
MENU_SWITCH = 25
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 17
DOWN_SWITCH = 18
MUTE_SWITCH = 4 


# This is the event callback routine to handle events
def callback(event):
	if event == RotaryEncoder.CLOCKWISE:
		print "Clockwise", RotaryEncoder.CLOCKWISE
	elif event == RotaryEncoder.ANTICLOCKWISE:
		print "Anticlockwise", RotaryEncoder.BUTTONDOWN
	elif event == RotaryEncoder.BUTTONDOWN:
		print "Button down", RotaryEncoder.BUTTONDOWN
	elif event == RotaryEncoder.BUTTONUP:
		print "Button up", RotaryEncoder.BUTTONUP
	return

#rswitch = RotaryEncoder(PIN_A,PIN_B,BUTTON,callback)
volumeknob = RotaryEncoder(LEFT_SWITCH,RIGHT_SWITCH,MUTE_SWITCH,callback)
tunerknob = RotaryEncoder(UP_SWITCH,DOWN_SWITCH,MENU_SWITCH,callback)


while True:
	time.sleep(0.5)



