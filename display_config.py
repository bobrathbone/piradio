#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Configuration dislay
# $Id: display_config.py,v 1.3 2016/06/19 12:23:53 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#

import os
import sys
import datetime
import commands
from time import strftime
from radio_class import Radio

# System files
RadioLibDir = "/var/lib/radiod"
CurrentStationFile = RadioLibDir + "/current_station"
CurrentTrackFile = RadioLibDir + "/current_track"
VolumeFile = RadioLibDir + "/volume"
TimerFile = RadioLibDir + "/timer"
AlarmFile = RadioLibDir + "/alarm"
StreamFile = RadioLibDir + "/streaming"
LogLevelFile=RadioLibDir + "/loglevel"
RssFile = "/var/lib/radiod/rss"

alarmType = ["off", "on", "repeat", "weekdays"]

radio = Radio()

# Exec system command
def execCommand(cmd):
	return commands.getoutput(cmd)

# Display flags
def displayConfig(radio):
	todaysdate = strftime("%H:%M %d/%m/%Y")
	print "Radio Configuration " + todaysdate
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
