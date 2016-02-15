#!/usr/bin/env python
#       
# Raspberry Pi TCPIP server class
# $Id: tcp_server_class.py,v 1.4 2015/11/08 09:29:28 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses the Python socket server
# See https://docs.python.org/2/library/socketserver.html 
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#

import socket
import sys
import time
import threading
import SocketServer
from log_class import Log

log = Log()

PORT = 5100
HOST = '0.0.0.0'
callback = None
client_data = ""

# Class to handle the data requests
class RequestHandler(SocketServer.BaseRequestHandler):
	# Client connection event
	def setup(self):
		log.message("Client connect", log.DEBUG)
	
	# Handle the data request
	def handle(self):
		global  callback
		global  client_data
		data = self.request.recv(1024)
		client_data = data.replace('\n','')
		log.message("TCP Server received: " + client_data, Log.DEBUG)
		self.request.sendall('OK\n')
		callback() 	# Call the get data routine
		return

	# Handle client disconnect
	def finish(self):
		log.message("Client disconnect", Log.DEBUG)


class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass # We will override class methods
	port = PORT
	host = HOST

	# Listen for incomming connections
	def listen(self,server, mycallback):
		global log
		log.init('radio')
		global  callback
		callback = mycallback  # Set up the callback
		# Start a thread with the server
		server_thread = threading.Thread(target=server.serve_forever)
		# Exit the server thread when the main thread terminates
		server_thread.daemon = True
		server_thread.name = 'remote'
		server_thread.start()
		msg = "tcp listen:" + server_thread.name + " " + str(self.host) + " port " + str(self.port)
		log.message(msg, Log.INFO)
		return

	def getServerAddress(self):
		return (self.host,self.port)

	def getData(self):
		global client_data
		data = client_data
		client_data = ''
		return data

# Test TCP server class
if __name__ == "__main__":
	
	server = None

	# Call back routine to get data event
	def callback():
		global server
		print "Data =", server.getData()
		return 

	server = TCPServer((HOST, PORT), RequestHandler)
	server.allow_reuse_address = True
	print "Listening", server.fileno()

	server.listen(server,callback)
	try:
		while True:
			time.sleep(0.1)
	except KeyboardInterrupt:
		server.shutdown()
		server.server_close()
		log.message("Exiting remote listener", Log.INFO)
		sys.exit(0)

# End of class
