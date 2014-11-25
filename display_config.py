#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Configuration dislay
# $Id: display_config.py,v 1.2 2014/05/26 07:47:05 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#

import os
import sys
import datetime
import commands
from time import strftime
import config
from radio_class import Radio


alarmType = ["off", "on", "repeat", "weekdays"]

radio = Radio()

# Exec system command
def execCommand(cmd):
	return commands.getoutput(cmd)

# Display flags
def displayConfig(radio):
	todaysdate = strftime("%H:%M %d/%m/%Y")
	print "Radio Configuration " + todaysdate
	print "MPD port " + execCommand( "cat " + MpdPortFile)
	print "Volume " + str(radio.getStoredVolume())
	print "Timer  " + str(radio.getStoredTimer())
	AlarmString = radio.getStoredAlarm()
	print "Alarm  " +  AlarmString
	(sType,sHours,sMins) = AlarmString.split(':')
	iAlarmType = int(sType)
	print "Alarm  " + alarmType[iAlarmType] + " [" + str(iAlarmType) + "]" 
	print "Streaming " + execCommand( "cat " + StreamFile) + " (" + str(radio.getStoredStreaming()) + ")"
	print "Current station " + execCommand( "cat " + CurrentStationFile)
	print "Current track " + execCommand( "cat " + CurrentTrackFile)
	print "Log level " + execCommand( "cat " + LogLevelFile)
	print "RSS " + execCommand( "cat " + RssFile)
	print "\nMPC status"
	print execCommand("mpc status")
	return

# Main routine
displayConfig(radio)

# End of script
