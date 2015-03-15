#!/usr/bin/env python
#       
# Raspberry Pi PiFace remote control daemon
# $Id: piface_remote.py,v 1.6 2015/03/14 13:21:18 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses the piface CAD libraries 
# See  http://www.piface.org.uk/products/piface_control_and_display/
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# The important configuration files are
# 	/etc/lirc/lircrc Program to event registration file
#	/etc/lircd.conf	 User generated remote control configuration file
#


import RPi.GPIO as GPIO
import pifacecad.ir
import sys
import os
import time
import signal
from signal import SIGUSR1

# Radio project imports
from rc_daemon import Daemon
from log_class import Log

log = Log()
IR_LED=11	# GPIO 11 pin 23

muted = False

pidfile = '/var/run/radiod.pid'

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global log
	pid = os.getpid()
	log.message("Remote control stopped, PID " + str(pid), log.INFO)
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):
	def run(self):
		log.init('radio')
		signal.signal(signal.SIGHUP,signalHandler)
		progcall = str(sys.argv)
		log.message('Remote control running pid ' + str(os.getpid()), log.INFO)
		exec_cmd('sudo service lirc start')		
		GPIO.setwarnings(False)      # Disable warnings
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setup(IR_LED, GPIO.OUT)  # Output LED

		listener()

	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "Remote control status: not running"
			log.message(message, log.INFO)
			print message
		else:
			message = "Remote control running pid " + str(pid)
			log.message(message, log.INFO)
			print message
		return

# End of class overrides


# Handle events
def print_ir_code(event):
	global muted
	message = "Remote:", event.ir_code
	log.message(message, log.DEBUG)
	GPIO.output(IR_LED, True)
	key = event.ir_code

	if key == 'KEY_VOLUMEUP': 
		exec_cmd('mpc play')		
		exec_cmd('mpc volume +5')		

	elif key == 'KEY_VOLUMEDOWN': 
		exec_cmd('mpc play')		
		exec_cmd('mpc volume -5')		

	elif key == 'KEY_CHANNELUP': 
		exec_cmd('mpc next')		

	elif key == 'KEY_CHANNELDOWN': 
		exec_cmd('mpc prev')		

	elif key == 'KEY_MUTE': 
		if not muted:
			exec_cmd('mpc pause')		
			muted = True
		else:
			exec_cmd('mpc play')		
			exec_cmd('mpc volume +1')		
			muted = False

	elif key == 'KEY_MENU': 
		if os.path.exists(pidfile):
			pf = file(pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
			os.kill(pid, SIGUSR1)
	GPIO.output(IR_LED, False)
	return

# Execute system command
def exec_cmd(cmd):
	log.message(cmd, log.DEBUG)
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# The main Remote control listen routine
def listener():
	log.message("Remote: setup listener", log.DEBUG)
	listener = pifacecad.ir.IREventListener(prog="piradio")
	listener.register('KEY_VOLUMEUP',print_ir_code)
	listener.register('KEY_VOLUMEDOWN',print_ir_code)
	listener.register('KEY_CHANNELUP',print_ir_code)
	listener.register('KEY_CHANNELDOWN',print_ir_code)
	listener.register('KEY_MENU',print_ir_code)
	listener.register('KEY_MUTE',print_ir_code)
	print "Activating"
	listener.activate()

### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/remote.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version 0.1"
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script

