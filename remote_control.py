#!/usr/bin/env python
#       
# Raspberry Pi remote control daemon (Non-Piface variants)
# $Id: remote_control.py,v 1.17 2016/02/09 13:23:31 bob Exp $
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
#	    The authors shall not be liable for any loss or damage however caused.
#
# The important configuration files are
# 	/etc/lirc/lircrc Program to event registration file
#	/etc/lircd.conf	 User generated remote control configuration file
#

import RPi.GPIO as GPIO
import ConfigParser
import pifacecad.ir
import sys
import os
import time
import signal
import socket
import errno

# Radio project imports
from config_class import Configuration
from rc_daemon import Daemon
from log_class import Log

log = Log()
IR_LED=11	# GPIO 11 pin 23
remote_led = IR_LED
muted = False
udphost = 'localhost'	# IR Listener UDP host default localhost
udpport = 5100		# IR Listener UDP port number default 5100

config = Configuration()

pidfile = '/var/run/radiod.pid'

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global log
	pid = os.getpid()
	log.message("Remote control stopped, PID " + str(pid), log.INFO)
	sys.exit(0)

# Daemon class
class RemoteDaemon(Daemon):

	def run(self):
		global remote_led
		global udpport
		global udphost
		log.init('radio')
		progcall = str(sys.argv)
		log.message(progcall, log.DEBUG)
		log.message('Remote control running pid ' + str(os.getpid()), log.INFO)
		signal.signal(signal.SIGHUP,signalHandler)
		exec_cmd('sudo service lirc start')		

		remote_led = config.getRemoteLed()
		if remote_led > 0:
			GPIO.setwarnings(False)      # Disable warnings
			GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
			GPIO.setup(remote_led, GPIO.OUT)  # Output LED
			flash_led(remote_led)
		else:
			log.message("Remote control LED disabled", log.DEBUG)
		udpport = config.getRemoteUdpPort()
		udphost = config.getRemoteUdpHost()
		log.message("UDP connect host " + udphost + " port " + str(udpport), log.DEBUG)
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

	# Test udp send
	def send(self,msg):
		udpSend(msg)
		return
		
	# Test the LED
	def flash(self):
		log.init('radio')
		remote_led = config.getRemoteLed()
		if remote_led > 0:
			GPIO.setwarnings(False)      # Disable warnings
			GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
			GPIO.setup(remote_led, GPIO.OUT)  # Output LED
			flash_led(remote_led)
		return

# End of class overrides

# Handle events
def handleIRevent(event):
	global muted
	global remote_led
	message = "Remote control sent " + event.ir_code
	log.message(message, log.DEBUG)
	if remote_led > 0:
		GPIO.output(remote_led, True)
	button = event.ir_code
	print button
	udpSend(button)

	if remote_led > 0:
		GPIO.output(remote_led, False)
	return

# Execute system command
def exec_cmd(cmd):
	log.message(cmd, log.DEBUG)
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# The main Remote control listen routine
def listener():
	log.message("Remote: setup IR listener", log.DEBUG)
	listener = pifacecad.ir.IREventListener(prog="piradio")
	listener.register('KEY_VOLUMEUP',handleIRevent)
	listener.register('KEY_VOLUMEDOWN',handleIRevent)
	listener.register('KEY_CHANNELUP',handleIRevent)
	listener.register('KEY_CHANNELDOWN',handleIRevent)
	listener.register('KEY_MENU',handleIRevent)
	listener.register('KEY_MUTE',handleIRevent)
	listener.register('KEY_LEFT',handleIRevent)
	listener.register('KEY_RIGHT',handleIRevent)
	listener.register('KEY_UP',handleIRevent)
	listener.register('KEY_DOWN',handleIRevent)
	listener.register('KEY_OK',handleIRevent)
	listener.register('KEY_LANGUAGE',handleIRevent)
	listener.register('KEY_INFO',handleIRevent)
	log.message("Activating IR Remote Control listener", log.DEBUG)
	listener.activate()


# Send button data to radio program
def udpSend(button):
	global udpport
	global udphost
	data = ''
	log.message("Remote control daemon udpSend " + button, log.DEBUG)
	
	try:
		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		clientsocket.settimeout(3)
		clientsocket.sendto(button, (udphost, udpport))
		data = clientsocket.recv(100).strip()

	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			log.message("IR remote udpSend no data" + e, log.ERROR)
		else:
			# Errors such as timeout
			log.message("IR remote udpSend " + str(e), log.ERROR)

	if len(data) > 0:
		log.message("IR daemon server sent: " + data, log.DEBUG)
	return data

# Flash the IR activity LED
def flash_led(led):
	count = 6
	delay = 0.3
	log.message("Flash LED on GPIO " + str(led), log.DEBUG)

	while count > 0:
		GPIO.output(led, True)
		time.sleep(delay)
		GPIO.output(led, False)
		time.sleep(delay)
		count -= 1
	return

# Execute system command
def execCommand(cmd):
	p = os.popen(cmd)
	return  p.readline().rstrip('\n')

# Print usage
def usage():
	print "usage: %s start|stop|status|version|flash|send|config" % sys.argv[0]
	sys.exit(2)

### Main routine ###
if __name__ == "__main__":

	daemon = RemoteDaemon('/var/run/remote.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'flash' == sys.argv[1]:
			daemon.flash()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version 0.1"
		elif 'send' == sys.argv[1]:
			daemon.send('IR_REMOTE')
		elif 'config' == sys.argv[1]:
			config = Configuration()
			print "LED = GPIO", config.getRemoteLed()
			print "HOST =", config.getRemoteUdpHost()
			print "PORT =", config.getRemoteUdpPort()
			print "LISTEN =", config.getRemoteListenHost()
		else:
			print "Unknown command: " + sys.argv[1]
			usage()
		sys.exit(0)
	else:
		usage()

# End of script

