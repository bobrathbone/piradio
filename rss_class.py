#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# $Id: rss_class.py,v 1.18 2014/04/08 13:26:51 bob Exp $
# Raspberry Pi RSS feed class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#


import os
import time
import urllib2
from xml.dom.minidom import parseString
from log_class import Log
from translate_class import Translate

log = Log()
translate = Translate()

url = "/var/lib/radiod/rss"

class Rss:
        rss = []	# Array for the RSS feed
        length = 0	# Number of RSS news items
	feed_available = False

	def __init__(self):
		log.init('radio')
                if os.path.isfile(url):
			self.feed_available = True
		return    

	# Gets the next RSS entry from the rss array
	def getFeed(self):
		self.feed_available = False
		line = "No RSS feed"
		if self.length < 1:
			self.rss = self.get_new_feed(url)    
			self.length = self.rss.__len__()

		feed = "No RSS feed"
		if self.length > 0:
			self.feed_available = True
			line = self.rss.pop()
			self.length -= 1
			feed = translate.all(line)
			log.message(feed,log.DEBUG)
		return feed

	# Is an RSS news feed available
	def isAvailable(self):
		return self.feed_available

	# Get a new feed and put it into the rss array
	def get_new_feed(self,url):
		rss = []
                if os.path.isfile(url):
			rss_feed = self.exec_cmd("cat " + url)
			log.message("Getting RSS feed: " + rss_feed,log.DEBUG)
			file = urllib2.urlopen(rss_feed)
			data = file.read()
			file.close()
			dom = parseString(data)
			dom.normalize()
			
			for news in dom.getElementsByTagName('*'):
				display = False
				line = news.toxml()
				line = line.lstrip(' ')
				if (line.find("VIDEO:") != -1):
					continue
				if (line.find("AUDIO:") != -1):
					continue
				if (line.find("<title>") == 0):
					display= True
				if (line.find("<description>") == 0):
					display= True
				if display:
					line = line.rstrip(' ')
					line = line.replace("<title>", "")
					line = line.replace("</title>", "")
					line = line.replace("<description>", "")
					line = line.replace("</description>", "")
					line = line.replace("![CDATA[", "")
					line = line.replace("]]>", "")
					rss.append(line)
					self.feed_available = True
		rss.reverse()
		return rss

	# Execute system command
	def exec_cmd(self,cmd):
		p = os.popen(cmd)
		result = p.readline().rstrip('\n')
		return result

# End of class
