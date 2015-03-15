#!/usr/bin/env python
#       
# $Id: test_remote_control.py,v 1.1 2015/03/08 11:47:41 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# IR remote control test
#

import pifacecad.ir
import time
import sys
import os

def print_ir_code(event):
	print  (event.ir_code)
	key = event.ir_code
	if key == 'KEY_VOLUMEUP': 
		exec_cmd('mpc volume +5')		
	if key == 'KEY_VOLUMEDOWN': 
		exec_cmd('mpc volume -5')		
	if key == 'KEY_CHANNELUP': 
		exec_cmd('mpc next')		
	if key == 'KEY_CHANNELDOWN': 
		exec_cmd('mpc prev')		
	return

# Execute system command
def exec_cmd(cmd):
        p = os.popen(cmd)
        result = p.readline().rstrip('\n')
        return result


listener = pifacecad.ir.IREventListener(prog="piradio")
listener.register('KEY_VOLUMEUP',print_ir_code)
listener.register('KEY_VOLUMEDOWN',print_ir_code)
listener.register('KEY_CHANNELUP',print_ir_code)
listener.register('KEY_CHANNELDOWN',print_ir_code)
listener.register('KEY_MENU',print_ir_code)
print "Activating"
listener.activate()

