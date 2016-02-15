#!/usr/bin/env python
#
# Test push buttons for the Raspberry PI internet radio
#
# $Id: test_switches.py,v 1.6 2015/07/13 07:25:32 bob Exp $
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

# Switch definitions
MENU_SWITCH = 25
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
UP_SWITCH = 17
DOWN_SWITCH = 18
MUTE_SWITCH = 4


GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers

GPIO.setwarnings(False)

# For rev 1 boards with no inbuilt pull-up/down resistors the
# Wire the GPIO inputs to ground via a 10K resistor and uncomment these lines
#GPIO.setup(MENU_SWITCH, GPIO.IN)
#GPIO.setup(UP_SWITCH, GPIO.IN)
#GPIO.setup(DOWN_SWITCH, GPIO.IN)
#GPIO.setup(LEFT_SWITCH, GPIO.IN)
#GPIO.setup(RIGHT_SWITCH, GPIO.IN)

# For rev 2 boards with inbuilt pull-up/down resistors the
# following lines are used instead of the above, so
# there is no need to physically wire the 10k resistors
GPIO.setup(MENU_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(UP_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DOWN_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LEFT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RIGHT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(MUTE_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
	try:
		menu_switch = GPIO.input(MENU_SWITCH)
		up_switch = GPIO.input(UP_SWITCH)
		down_switch = GPIO.input(DOWN_SWITCH)
		left_switch = GPIO.input(LEFT_SWITCH)
		right_switch = GPIO.input(RIGHT_SWITCH)
		mute_switch = GPIO.input(MUTE_SWITCH)

		if menu_switch:
			print "menu_switch"
		elif up_switch:
			print "up_switch"
		elif down_switch:
			print "down_switch"
		elif left_switch:
			print "left_switch"
		elif right_switch:
			print "right_switch"
		elif mute_switch:
			print "mute_switch"

		time.sleep(0.5)

	except KeyboardInterrupt:
		print "\nExit"
		GPIO.setwarnings(False)
		GPIO.cleanup()
		sys.exit(0)

# End of program
