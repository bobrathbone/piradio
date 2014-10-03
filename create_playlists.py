#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Raspberry Pi Internet Radio playlist utility
# $Id: create_playlists.py,v 1.21 2014/07/12 10:35:53 bob Exp $
#
# Create playlist files from the following url formats
#       iPhone stream files (.asx)
# 	Playlist files (.pls)
# 	Extended M3U files (.m3u)
#	Direct media streams (no extension)
#
# See Raspberry PI Radio constructors manual for instructions
#
# Author   : Bob Rathbone
# Web site : http://www.bobrathbone.com
#
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import urllib2
from xml.dom.minidom import parseString

# Output errors to STDERR
stderr = sys.stderr.write;

# File locations
PlsDirectory = '/var/lib/mpd/playlists/'
RadioDir = '/home/pi/radio/'
RadioLibDir = '/var/lib/radiod/'
StationList = RadioLibDir + 'stationlist'
DistFile = '/home/pi/radio/station.urls'
TempDir = '/tmp/radio_stream_files/'
PlaylistsDir = '/home/pi/radio/playlists/'
PodcastsFile = '/var/lib/radiod/podcasts'

duplicateCount = 0

# Execute system command
def execCommand(cmd):
	p = os.popen(cmd)
	return  p.readline().rstrip('\n')

# Create the initial list of files
def createList():
	if not os.path.isfile(StationList):
		print 'Creating ' + StationList + '\n'
		execCommand ("mkdir -p " + RadioLibDir )
		print ("cp " + DistFile + ' ' + StationList )
		execCommand ("cp " + DistFile + ' ' + StationList)
		print 
	return

# Create the output from the title and URL
def createPlsOutput(title,url,filenumber):
	lines = []	
	lines.append('File%s=%s' % (filenumber,url))
	lines.append('Title%s=%s' % (filenumber,title))
	lines.append('Length%s=-1' % filenumber)
	return lines

# Create the PLS or M3U file
def createPlsFile(filename,output,nlines):
	global duplicateCount
	uniqueCount = 1
	if len(filename) < 1:
		filename = 'unknown'
	outfile = TempDir + filename + '.pls' 

	# Create unique files
	exists = True
	while exists:
		if os.path.exists(outfile):
			print "Warning: " + outfile + ' already exists'
			outfile = TempDir + filename + '[' + str(uniqueCount) + '].pls'
			uniqueCount += 1
			duplicateCount += 1
		else:
			exists = False

	try:
		print 'Creating ' + outfile + '\n'
		outfile = open(outfile,'w')
		outfile.writelines("[playlist]\n")
		outfile.writelines("NumberOfEntries=%s\n"% nlines)
		outfile.writelines("Version=2\n")
		for item in output:
			outstr = item.encode('utf8', 'replace')
			outfile.write(outstr + "\n")

		outfile.close()
	except:
		print "Failed to create",outfile
	return

# Beautify HTML convert tags to lower case
def parseHTML(data):
	lcdata = ''
	for line in data:
		lcline = ''
		line = line.rstrip()
		line = line.lstrip()
		line.replace('href =', 'href=')
		length = len(line)

		if length < 1:
			continue
		tag1right = line.find('>')

		if tag1right > 1:
			start_tag = line[0:tag1right+1]
			lcline = lcline + start_tag.lower()

		tag2left = line.find('<', tag1right+1)

		if tag2left > 1:
			end_tag = line[tag2left:length]
			parameter = line[tag1right+1:tag2left]
			lcline = lcline + parameter + end_tag.lower()
		lcdata = lcdata + lcline
	return lcdata

# Get XML/HTML parameter
def getParameter(line):
	tag1right = line.find('>')
	tag2left = line.find('<', tag1right+1)
	parameter = line[tag1right+1:tag2left]
	return parameter


# Create a PLS file from an ASX(XML) file
def parseAsx(title,url,data,filenumber):
	global errorCount
	global warningCount
	lcdata = parseHTML(data)

	try:
		dom = parseString(lcdata)
	except Exception,e:
		print "Error:",e
		print "Error: Could not parse XML data from,", url + '\n'
		errorCount += 1
		return

	try:
		# If title undefined in the station list get it from the file
		if len(title) < 1:
			titleTag = dom.getElementsByTagName('title')[0].toxml()
			title = getParameter(titleTag)

	except:
		print "Warning: Title not found in", url 
		pass

	finally:
		try:
			urlTag = dom.getElementsByTagName('ref')[0].toxml()
			url = urlTag.replace('<ref href=\"','').replace('\"/>','')
			urls = url.split('?')
			url = urls[0]
			print 'Title:',title
			plsfile = title.replace(' ','_')
			output = createPlsOutput(title,url,filenumber)
		except IndexError,e:
			print "Error:",e
			print "Error parsing", url
			errorCount += 1
			return "# DOM Error" 

	return output

# Create filename from URL
def createFileName(title,url):
	if len(title) > 0:
		name = title
		name = name.replace('.',' ')
		name = name.replace(' ','_')
	else:
		try:
			urlparts = url.rsplit('/',1)
			site = urlparts[0]
			siteparts = site.split('/')
			name = siteparts[2]
			siteparts = name.split(':')
			name = siteparts[0]
		except:
			name = url
		name = name.replace('www.','')
		name = name.replace('.com','')
		name = name.replace('.','_')

	name = name.replace('__','_')
	return name

# Create default title 
def createTitle(url):
	urlparts = url.rsplit('/',1)
	site = urlparts[0]
	siteparts = site.split('/')
	name = siteparts[2]
	siteparts = name.split(':')
	title = siteparts[0]
	return title

# Direct radio stream (MP3 AAC etc)
def parseDirect(title,url,filenumber):
	url = url.replace('(stream)', '')
	if len(title) < 1:
		title = createTitle(url)
	print "Title:",title
	output = createPlsOutput(title,url,filenumber)
	return output

# Create PLS file in the temporary directory
def parsePls(title,url,lines,filenumber):
	plstitle = ''
	plsurl = ''

	for line in lines:
		if line.startswith('Title1='):
			titleline =  line.split('=')
			plstitle = titleline[1]
		
		if line.startswith('File1='):
			fileline =  line.split('=')
			plsurl = fileline[1]

	# If title undefined in the station list get it from the file
	if len(title) < 1:
		if  len(plstitle) > 1:
			title = plstitle
		else: 
			title = createTitle(url)
			plsfile = createFileName(title,url)

	print 'Title:',title
	plsfile = title.replace(' ','_')
	output = createPlsOutput(title,plsurl,filenumber)
	return output

# Convert M3U file to PLS output
def parseM3u(title,lines,filenumber):
	info = 'Unknown' 
	output = []

	for line in lines:
		line = line.replace('\r','')
		line = line.replace('\n','')
		if line.startswith('http:'):
			url = line
		elif line.startswith('#EXTINF:'):
			info = line
			
	if len(title) < 1:
		title = info
	
	if len(title) < 1:
		filename = createFileName(title,url)
	else:
		filename = title.replace(' ','_')

	print 'Title:',title
	output.append('Title%s=%s'% (filenumber,title))
	output.append('File%s=%s'% (filenumber,url))
	output.append('Length%s=-1'% filenumber)
	return output

# Usage message 
def usage():
	stderr("\nUsage: %s [--delete_old] [--no_delete] [--help]\n" % sys.argv[0])
	stderr("\tWhere: --delete_old   Delete old playlists\n")
	stderr("\t       --no_delete    Don't delete old playlists\n")
	stderr("\t       --help	 Display help message\n\n")
	return

# Station definition help message
def format():
	stderr ("Start a playlist with the name between brackets. For example:\n")
	stderr ("(BBC Radio Stations)\n")
	stderr ("This will create a playlist called BBC_Radio_Stations.pls)\n")
	stderr ("\nThe above is followed by station definitions which take the following format:\n")
	stderr ("\t[title] http://<url>\n")
	stderr ("\tExample:\n")
	stderr ("\t[BBC Radio 3] http://bbc.co.uk/radio/listen/live/r3.asx\n\n")
	stderr ("End a playlist by inserting a blank line at the end of the list of stations\n")
	stderr ("or start a new playlist definition.\n\n")
	return

# Start of MAIN script

if os.getuid() != 0:
	print "This program can only be run as root user or using sudo"
	sys.exit(1)

deleteOld =  False
noDelete  =  False

if len(sys.argv) > 2:
	stderr("\nError: you may not define more than one parameter at a time\n")
	usage()
	sys.exit(1)

if len(sys.argv) > 1:
	param = sys.argv[1]
	if param == '--delete_old':
		deleteOld  = True

	elif param == '--no_delete':
		noDelete  = True

	elif param == '--help':
		usage()
		format()
		sys.exit(0)
	else:
		stderr("Invalid parameter %s\n" % param)
		usage()
		sys.exit(1)

# Create station URL list
createList()

# Temporary directory - if it exists then delete all pls files from it
execCommand ("mkdir -p " + TempDir )
execCommand ("rm -f " + TempDir + '*' )

# Open the list of URLs 
print "Creating PLS files from", StationList + '\n'

lineCount = 0		# Line being processed (Including comments)
errorCount = 0		# Errors
duplicateCount = 0	# Duplicate file names
warningCount = 0	# Warnings
processedCount = 0	# Processed station count

# Copy user stream files to temporary directory 
print "Copying user PLS and M3U files from " + PlaylistsDir  + " to " + TempDir + '\n'

if os.listdir(PlaylistsDir):
	execCommand ("cp -f " +  PlaylistsDir + '* ' + TempDir )

# Playlist file name
filename = ''
pls_output = []
filenumber = 1
writeFile = False
url = ''

# Main processing loop
for line in open(StationList,'r'):
	lineCount += 1
	lines = []
	newplaylist = ''

	# Set url types to False
	isASX = False
	isM3U = False
	isPLS = False

	# Skip commented out or blank lines
	line = line.rstrip()	# Remove line feed
	if line[:1] == '#':
		continue

	# Handle playlist definition in () brackets
	elif line[:1] == '(':
		newplaylist = line.strip('(')	   # Remove left bracket
		newplaylist = newplaylist.strip(')') # Remove right  bracket
		playlistname = newplaylist
		newplaylist = newplaylist.replace(' ', '_')

		if len(filename) > 0:
			writeFile = True
		else:
			print "Playlist:", playlistname
			filename = newplaylist
			filenumber = 1
			continue

	if len(line) < 1 or writeFile:
		if len(filename) < 1 and len(url) > 0:
			filename = createFileName(title,url)
		if len(filename) > 0 and len(pls_output) > 0:
			createPlsFile(filename,pls_output,filenumber-1)
			filenumber = 1
			pls_output = []
			filename = ''
			url = ''

		if len(newplaylist) > 0:
			filename = newplaylist	
			continue

		if writeFile and len(line) > 0:
			writeFile = False
		else:
			continue


	# Check start of title defined
	elif line[:1] != '[':
		stderr("Error: Missing left bracket [ in line %s in %s\n" % (lineCount,StationList))
		format()
		errorCount += 1
		continue

	processedCount += 1
	line = line.lstrip('[')

	# Get title and URL parts
	line = line.strip()
	lineparts = line.split(']')

	# Should be 2 parts (title and url)
	if len(lineparts) != 2:
		stderr("Error: Missing right bracket [ in line %s in %s\n" % (lineCount,StationList))
		format()
		errorCount += 1
		continue

	# Get title and URL from station definition
	title = lineparts[0].lstrip()
	url = lineparts[1].lstrip()

	# Get the published URL and determine its type
	print 'Processing line ' + str(lineCount) + ': ' + url

	# Extended M3U (MPEG 3 URL) format
	if url.endswith('.m3u'):
		isM3U = True

	# Advanced Stream Redirector (ASX)
	elif url.endswith('.asx'):
		isASX = True

	# Playlist format
	elif url.endswith('.pls'):
		isPLS = True

	# Advanced Audio Coding stream (Don't retrieve any URL)
	else:
		# Remove redundant (stream) parameter 
		url = url.replace('(stream)', '')
		pls_output += parseDirect(title,url,filenumber)
		if len(filename) < 1:
			filename = createFileName(title,url)
			writeFile = True
		filenumber += 1
		continue

	# Get the published URL to the stream file
	try:
		file = urllib2.urlopen(url)
		data = file.read()
		file.close()
	except:
		print "Error: Failed to retrieve ", url
		errorCount += 1
		continue

	# Creat list from data
	lines = data.split('\n')
	firstline = lines[0].rstrip()

	# process lines accoording to URL type
	if isPLS:
		pls_output += parsePls(title,url,lines,filenumber)
	elif isM3U:
		pls_output += parseM3u(title,lines,filenumber)
	elif isASX:
		if firstline.startswith('<ASX'):
			pls_output += parseAsx(title,url,lines,filenumber)
		else:
			print url,"didn't return XML data"
			continue

	if len(filename) < 1:
		filename = createFileName(title,url)
		writeFile = True

	filenumber += 1


# End of for line 

# Write last file
if len(filename) < 1:
	filename = createFileName(title,url)
if len(filename) > 0 and len(pls_output) > 0:
	createPlsFile(filename,pls_output,filenumber-1)
	
print ("Processed %s station URLs from %s" % (processedCount,StationList))

# Copy files from temporary directory to playlist directory
oldfiles = len(os.listdir(PlsDirectory))
if oldfiles > 0:
	if not deleteOld and not noDelete:
		stderr("There are %s old playlist files in the %s directory.\n" % (oldfiles,PlsDirectory))
		stderr("Do you wish to remove the old files y/n: ")
		answer = raw_input("")
		if answer == 'y':
			deleteOld = True

	if deleteOld:
		stderr ("\nRemoving old playlists from directory %s\n" % PlsDirectory)
		execCommand ("rm -f " + PlsDirectory + "*.pls" )
		execCommand ("rm -f " + PlsDirectory + "*.m3u" )
	else:
		print "Old playlist files not removed"

copiedCount = len(os.listdir(TempDir))
print "Copying %s new playlist files to directory %s" % (copiedCount,PlsDirectory)
execCommand ("cp -f " + TempDir + '* ' + PlsDirectory )

if os.path.isfile(PodcastsFile):
	print "\nCreating Podcast playlists from " + PodcastsFile
	execCommand(RadioDir + "create_podcasts.py")

# Create summary report
print "\nNew radio playlist files will be found in " + PlsDirectory

if errorCount > 0:
	print str(errorCount) + " error(s)"

if duplicateCount > 0:
	print str(duplicateCount) + " duplicate file name(s) found and renamed."

warningCount += duplicateCount
if warningCount > 0:
	print str(warningCount) + " warning(s)"

# End of script

