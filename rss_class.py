#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# $Id: rss_class.py,v 1.21 2014/09/10 12:49:54 bob Exp $
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
import config
from log_class import Log
from translate_class import Translate

log = Log()
translate = Translate()


# Tags to strip out
tags = ['<h1>', '</h1>',
	'<h2>', '</h2>',
	'<h3>', '</h3>',
	'<h4>', '</h4>',
	'<p>', '</p>', '<p/>',
	'<br>', '</br>','<br/>',
	'<strong>', '</strong>',
	'<title>', '</title>',
	'<description>', '</description>',
	]

class Rss:
        rss = []	# Array for the RSS feed
        length = 0	# Number of RSS news items
	feed_available = False

	def __init__(self):
                global url
		log.init('radio')
                if not config.config.has_section("RSS"):
			self.feed_available = False
                elif not config.config.has_option("RSS","file"):
			self.feed_available = False
                else:
                        url = config.config.get("RSS","file")
                        print ("RSS URL: " + url,log.DEBUG)
                        if os.path.isfile(url):
                                self.feed_available = True
                        else:
                                self.feed_available = False
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
			feed = feed.lstrip('"')
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
			log.message("Getting RSS feed: " + rss_feed,log.INFO)
			file = urllib2.urlopen(rss_feed)
			data = file.read()
			file.close()
			dom = parseString(data)
			dom.normalize()
			
			for news in dom.getElementsByTagName('*'):
				display = False
				line = news.toxml()
				line = line.replace("&lt;", "<")	# Replace special string
				line = line.replace("&gt;", ">")
				
				msg =  "LINE:" + line
				line = line.lstrip(' ')
				if (line.find("VIDEO:") != -1):
					continue
				if (line.find("AUDIO:") != -1):
					continue
				if (line.find("<rss") != -1):
					continue
				if (line.find("<item") != -1):
					continue
				if (line.find("<image") == 0):
					continue

				if (line.find("<title>") >= 0):
					display= True
				if (line.find("<description>") >= 0):
					display= True

				if display:
					title = ''
					description = ''
					line = line.rstrip(' ')
					line = line.replace("![CDATA[", "")
					line = line.replace("]]>", "")

					if (line.find("<description>") == 0):
						description = line.split("</description>", 2)[0]
						description = self._strip_string(description, "<img", "</img>")
						description = self._strip_string(description, "<a href", "</a>")
						description = self._strip_string(description, "<br ", "</br>")

					if (line.find("<title>") >= 0):
						title = line.split("</title>", 2)[0]

					if len(title) > 0:
						for tag in tags:	# Strip out HTML tags
							title = title.replace(tag, "")
						rss.append(title)

					if len(description) > 0:
						for tag in tags:	# Strip out HTML tags
							description = description.replace(tag, "")
						rss.append(description)

					self.feed_available = True
		rss.reverse()
		return rss

	# Execute system command
	def exec_cmd(self,cmd):
		p = os.popen(cmd)
		result = p.readline().rstrip('\n')
		return result

	# Strip string (between tags)
	def _strip_string(self, text, s_start, s_end):
		new_text = text
		
		try:
			while new_text.find(s_start) > 0:
				idx_start = new_text.find(s_start)
				replace_str = new_text[idx_start:]
				idx_end = replace_str.find(s_end)
				if idx_end < 0:
					idx_end = replace_str.find("/>")
					len2 = 2	
				else:
					len2 = len(s_end)
				replace_str = replace_str[0:idx_end + len2]
				new_text =  new_text.replace(replace_str,'')
		except:
			new_text = text
		return new_text

# End of class
