#!/usr/bin/env python
#
# Raspberry Pi Rotary Test Encoder Class
# $Id: test_rotary_class.py,v 1.9 2017/02/13 18:55:53 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#

import sys
import time
import atexit
import traceback

from rotary_class import RotaryEncoder

stderr = sys.stderr.write;

# Switch definitions
menu_switch = 25
left_switch = 14
right_switch = 15
up_switch = 17
down_switch = 18
mute_switch = 4 

# If using a DAC with 26 pin wiring the down switch is on GPIO10
dac_down_switch = 10

# Switch settings for 40 pin version (support for IQAudio)
menu_switch_40 = 17
mute_switch_40 = 4
up_switch_40 = 15
down_switch_40 = 14
left_switch_40 = 23
right_switch_40 = 24

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
		print name + " anticlockwise", RotaryEncoder.ANTICLOCKWISE
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

# If using a Audio DAC use GPIO 10 (Pin 19) 
down_switch = down_switch
stderr("Which wiring version are you using\n")
stderr("40 pin = 1, 26 pin = 2: ")
answer = raw_input("")
if answer == '1':
	menu_switch = menu_switch_40
	left_switch = left_switch_40
	right_switch = right_switch_40
	up_switch = up_switch_40
	down_switch = down_switch_40
	mute_switch =  mute_switch_40
	stderr("40 pin wiring version selected\n")
else:
	stderr("26 pin wiring version selected\n")
	stderr("Are you using GPIO10 (pin 19) for the down switch y/n: ")
	answer = raw_input("")
	if answer == 'y':
		down_switch = dac_down_switch
		stderr("Down switch is set to GPIO" + str(dac_down_switch) + "\n")

# Set up rotary encoders
volumeknob = RotaryEncoder(left_switch,right_switch,mute_switch,volume_event,revision)
tunerknob = RotaryEncoder(down_switch,up_switch,menu_switch,tuner_event,revision)

print "Use Ctl-C to exit"

while True:
	try:
		time.sleep(0.1)
	except KeyboardInterrupt:
		print "\nExit"
		sys.exit(0)

# End of test rotary encoders


