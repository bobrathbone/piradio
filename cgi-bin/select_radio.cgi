#!/usr/bin/python
import shutil;
import sys;
import os;
import logging
import cgi
import time
from subprocess import call 

CurrentStationFile = "/var/lib/radiod/current_station"

def write_html_header():
    print "Content-Type: text/html", "\n";
    print "<html>";
    print "<head>";
    print "<title>Select internet radio</title>";
    print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">";
    print "<META HTTP-EQUIV='refresh' CONTENT='1;URL=../snoopy.html'>"
    print "<link rel='stylesheet' type='text/css' href='/basic-noise.css' title='Basic Noise' media='all' />"
    print "</head>";
    print "<body>";
    return;

def write_html_footer():
    print "</body>";
    print "<head>";
    print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">";
    print "</head>";
    print "</html>";
    return;

# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# Reload if new source selected
def load_radio():
	exec_mpc_cmd("clear")	
	dirList=os.listdir("/var/lib/mpd/playlists")
	for fname in dirList:
		print "NAME:",fname
		fname,ext = fname.split('.')
		cmd = "load \"" + fname + "\""
		exec_mpc_cmd(cmd)	
	exec_mpc_cmd("random off")
        cmd = "play " + str(get_stored_id())
	exec_mpc_cmd(cmd)

def exec_mpc_cmd(cmd):
	return exec_cmd("/usr/bin/mpc " + cmd)

# Get the last ID stored in /var/lib/radiod
def get_stored_id():
        current_id = 1
        if os.path.isfile(CurrentStationFile):
                current_id = int(exec_cmd("cat " + CurrentStationFile) )
        return current_id


write_html_header();

print "<h1>Loading radio stations</h1>"

load_radio()
write_html_footer()
 
# End of script

