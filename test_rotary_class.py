#!/usr/bin/env python
#
# Raspberry Pi Rotary Test Encoder Class
# $Id: test_rotary_class.py,v 1.4 2014/07/22 13:10:01 bob Exp $
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
import atexit
import traceback

from rotary_class import RotaryEncoder

stderr = sys.stderr.write;

# Switch definitions
MENU_SWITCH = 25
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 17
DOWN_SWITCH = 18
MUTE_SWITCH = 4 

# Try to trap any exit errors 
def exit_fn():
        if not traceback.format_exc().startswith('None'):
                s=traceback.format_exc()
	sys.exit(0)

# Register
atexit.register(exit_fn)

# This is the callback routine to handle volume events
def volume_event(event):
	display_event("Volume", event)
	return

# This is the callback routine to handle tuner events
def tuner_event(event):
	display_event("Tuner", event)
	return

def display_event(name,event):
	if event == RotaryEncoder.CLOCKWISE:
		print name + " clockwise", RotaryEncoder.CLOCKWISE
	elif event == RotaryEncoder.ANTICLOCKWISE:
		print name + " anticlockwise", RotaryEncoder.BUTTONDOWN
	elif event == RotaryEncoder.BUTTONDOWN:
		print name + " button down", RotaryEncoder.BUTTONDOWN
	elif event == RotaryEncoder.BUTTONUP:
		print name + " button up", RotaryEncoder.BUTTONUP
	return

# Allow user to select board revision
revision = 2
stderr("Are you using an old revision 1 board y/n: ")
answer = raw_input("")
if answer == 'y':
	revision = 1

volumeknob = RotaryEncoder(LEFT_SWITCH,RIGHT_SWITCH,MUTE_SWITCH,volume_event,revision)
tunerknob = RotaryEncoder(UP_SWITCH,DOWN_SWITCH,MENU_SWITCH,tuner_event,revision)

print "Use Ctl-C to exit"

while True:
	try:
		time.sleep(0.2)
	except KeyboardInterrupt:
		print "\nExit"
		sys.exit(0)




