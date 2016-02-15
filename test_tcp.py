#!/usr/bin/env python
#
# Raspberry Pi TCPIP test server class
# $Id: test_tcp.py,v 1.1 2015/10/09 12:03:45 bob Exp $
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

import sys
import time
import SocketServer
from tcp_server_class import TCPServer
from tcp_server_class import RequestHandler

server = None

def callback():
	global server
	print "Data =", server.getData()
	return False

server = TCPServer((TCPServer.host,TCPServer.port),RequestHandler)
print "Listening", server.fileno()
server.listen(server,callback)

try:
	while True:
		time.sleep(0.1)
except KeyboardInterrupt:
	print "Exit server"
	server.shutdown()
	server.server_close()
	sys.exit(0)

# End of program
