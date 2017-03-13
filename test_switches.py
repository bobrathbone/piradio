#!/usr/bin/env python
#
# Test push buttons for the Raspberry PI internet radio
#
# $Id: test_switches.py,v 1.7 2017/01/11 11:15:41 bob Exp $
#
# Author Bob Rathbone
# Web site http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys
import time
import RPi.GPIO as GPIO

stderr = sys.stderr.write;

GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
GPIO.setwarnings(False)

# Switch definitions
menu_switch = 25
left_switch = 14
right_switch = 15
up_switch = 17
down_switch = 18
mute_switch = 4

# If using a DAC with 26 pin wiring wire down switch to GPIO10(pin 19)
dac_down_switch = 10

# Switch settings for 40 pin version (support for IQAudio)
menu_switch_40 = 17
mute_switch_40 = 4
up_switch_40 = 15
down_switch_40 = 14
left_switch_40 = 23
right_switch_40 = 24

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

if revision == 1:
	# For rev 1 boards with no inbuilt pull-up/down resistors the
	# Wire the GPIO inputs to ground via a 10K resistor 
	GPIO.setup(menu_switch, GPIO.IN)
	GPIO.setup(mute_switch, GPIO.IN)
	GPIO.setup(up_switch, GPIO.IN)
	GPIO.setup(down_switch, GPIO.IN)
	GPIO.setup(left_switch, GPIO.IN)
	GPIO.setup(right_switch, GPIO.IN)
else:
	# For rev 2 boards with inbuilt pull-up/down resistors the
	# following lines are used instead of the above, so
	# there is no need to physically wire the 10k resistors
	GPIO.setup(menu_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(up_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(down_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(left_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(right_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(mute_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
	try:
		menu_switch_in = GPIO.input(menu_switch)
		up_switch_in = GPIO.input(up_switch)
		down_switch_in = GPIO.input(down_switch)
		left_switch_in = GPIO.input(left_switch)
		right_switch_in = GPIO.input(right_switch)
		mute_switch_in = GPIO.input(mute_switch)

		if menu_switch_in:
			print "menu_switch"
		elif up_switch_in:
			print "up_switch"
		elif down_switch_in:
			print "down_switch"
		elif left_switch_in:
			print "left_switch"
		elif right_switch_in:
			print "right_switch"
		elif mute_switch_in:
			print "mute_switch"

		time.sleep(0.5)

	except KeyboardInterrupt:
		print "\nExit"
		GPIO.setwarnings(False)
		GPIO.cleanup()
		sys.exit(0)

# End of program
