#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_daemon.py,v 1.3 2014/06/08 10:08:07 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class is the daemon class for radio_class.py
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys, os, time, atexit
from signal import SIGTERM 

class Daemon:
	"""
	A generic daemon class.
	
	Usage: subclass the Daemon class and override the run() method
	"""
	def __init__(self, pidfile, stdin='/dev/null', stdout='/var/log/radiod.stdout', stderr='/var/log/radiod.stderr'):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
	
	def daemonize(self):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced 
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
                print("daemonize")
                
                try: 
                        pid = os.fork() 
                        if pid > 0:
                                print ("fork 1 ok")
                                print ("pid = ", os.getpid())
                                # exit first parent
                                sys.exit(0) 
                except OSError as e: 
                        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
                        sys.exit(1)
	
                print ("forekd")
		# decouple from parent environment
		os.chdir("/") 
                print ("pid = ", pid)
                print ("pid = ", os.getpid())
                print ("ppid = ", os.getppid())
		os.setsid() 
		os.umask(0) 
	
                print ("decoupled")
                # do second fork
                try: 
                        pid = os.fork() 
                        if pid > 0:
                                print ("fork2 ok")
                                print ("pid = ", os.getpid())
                                # exit from second parent
                                sys.exit(0) 
                except OSError as e: 
                        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
                        sys.exit(1) 
	
		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin, 'r')
		so = file(self.stdout, 'a+')
		se = file(self.stderr, 'a+', 0)
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())
                print ("pid2 = ", pid)
                print ("pid = ", os.getpid())

		# write pidfile
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)
	
	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		"""
		Start the daemon
		"""
		# Check for a pidfile to see if the daemon already runs
		try:
                        print ("pidfile " + self.pidfile)
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
                        print ("pid = " + str(pid))
                        pf.close()
		except IOError:
			pid = None
                        print ("no pid")
	
		if pid:
			message = "pidfile %s already exist. Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)
		
		# Start the daemon
		self.daemonize()
		self.run()

	def stop(self):
		"""
		Stop the daemon
		"""
# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if not pid:
			message = "pidfile %s does not exist. Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process	
		try:
			count = 30
			while count > 0:
				os.kill(pid, SIGTERM)
				time.sleep(0.2)
				count -= 1

		except OSError as err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print (str(err))
				sys.exit(1)

	def restart(self):
		"""
		Restart the daemon
		"""
		self.stop()
		self.start()

	def status(self):
		"""
		Status
		"""

	def run(self):
		"""
		You should override this method when you subclass Daemon. It will be called after the process has been
		daemonized by start() or restart().
		"""

