#!/usr/bin/python
import shutil;
import sys;
import os;
import logging
import cgi
import time
from subprocess import call 

CurrentTrackFile = "/var/lib/radiod/current_track"

def write_html_header():
    print "Content-Type: text/html", "\n";
    print "<html>";
    print "<head>";
    print "<title>Operate Garage Door</title>";
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
def load_music():
	exec_cmd("/bin/mount -o ro /dev/sda1 /media")
	exec_mpc_cmd("clear")	
	exec_mpc_cmd("update")	
	dirList=os.listdir("/var/lib/mpd/music")
	for fname in dirList:
		cmd = "add \"" + fname.strip("\n") + "\""
		exec_mpc_cmd(cmd)	
		time.sleep(0.25)
	exec_mpc_cmd("random on")	
	cmd = "play " + str(get_stored_id())
        exec_mpc_cmd(cmd)


def exec_mpc_cmd(cmd):
	return exec_cmd("/usr/bin/mpc " + cmd)

# Get the last ID stored in /var/lib/radiod
def get_stored_id():
        current_id = 1
        if os.path.isfile(CurrentTrackFile):
                current_id = int(exec_cmd("cat " + CurrentTrackFile) )
        return current_id



write_html_header();

print "<h1>Loading music library</h1>"

load_music()
write_html_footer()
 
# End of script

