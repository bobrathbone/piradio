#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: translate_class.py,v 1.5 2014/03/25 19:42:00 bob Exp $
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
from log_class import Log

log = Log()

class Translate:
	def __init__(self):
		log.init('radio')
		return    

	# Translate all 
        def all(self,text):
                s = self._convert2escape(text)
		s = self._escape(s)
		s = self._unicode(s)
		s = self._html(s)
		return s   

	# Convert unicode to escape codes
	def _convert2escape(self,text):
		s = repr(text)
		if s.__len__() > 2: 
			s= s[1:-1]      # Strip ' characters
			s = s.lstrip("'")
		return s

        # Convert escaped characters (umlauts) to normal characters
        def escape(self,text):
                s = self._convert2escape(text)
		s = self._escape(s)
		return s


        # Convert escaped characters (umlauts) to normal characters
        def _escape(self,text):
		s = text
		s = s.replace('//', '/')

		# Currency other special character
		s = s.replace('\\xa3', chr(156))  # UK pound sign
		s = s.replace('\\xa9', chr(169))  # Copyright

		# German unicode escape sequences
		s = s.replace('\\xc3\\x83', chr(223))   # Sharp s es-zett
		s = s.replace('\\xc3\\x9f', chr(223))   # Sharp s ?
		s = s.replace('\\xc3\\xa4', chr(228))   # a umlaut
		s = s.replace('\\xc3\\xb6', chr(246))   # o umlaut
		s = s.replace('\\xc3\\xbc', chr(252))   # u umlaut
 		s = s.replace('\\xc3\\x84', chr(196))	# A umlaut
		s = s.replace('\\xc3\\x96', chr(214)) 	# O umlaut
 		s = s.replace('\\xc3\\x9c', chr(220))	# U umlaut

		# German short hex representation
		s = s.replace('\\xdf', chr(223))   	# Sharp s es-zett
		s = s.replace('\\xe4', chr(228))   	# a umlaut
		s = s.replace('\\xf6', chr(246))   	# o umlaut
		s = s.replace('\\xfc', chr(252))   	# u umlaut
 		s = s.replace('\\xc4', chr(196))	# A umlaut
		s = s.replace('\\xd6', chr(214)) 	# O umlaut
 		s = s.replace('\\xdc', chr(220))	# U umlaut

		# Spanish and French
		s = s.replace('\\xa0', ' ')         # Line feed  to space
		s = s.replace('\\xe0', chr(224))    # Small a reverse acute
		s = s.replace('\\xe1', chr(225))    # Small a acute
		s = s.replace('\\xe7', chr(231))    # Small c Cedilla 
		s = s.replace('\\xe8', chr(232))    # Small e grave
		s = s.replace('\\xe9', chr(233))    # Small e acute
		s = s.replace('\\xed', chr(237))    # Small i acute
		s = s.replace('\\xee', chr(238))    # Small i circumflex
		s = s.replace('\\xf1', chr(241))    # Small n tilde
		s = s.replace('\\xf3', chr(243))    # Small o acute
		s = s.replace('\\xf4', chr(244))    # Small o circumflex
		s = s.replace('\\xf9', chr(249))    # Small u circumflex
		s = s.replace('\\xfa', chr(250))    # Small u acute

		s = s.replace('\\xc1', chr(193))    # Capital A acute

		s = s.replace('\\xc7', chr(199))    # Capital C Cedilla 
		s = s.replace('\\xc9', chr(201))    # Capital E acute
		s = s.replace('\\xcd', chr(205))    # Capital I acute
		s = s.replace('\\xd3', chr(211))    # Capital O acute
		s = s.replace('\\xda', chr(218))    # Capital U acute

		s = s.replace('\\xbf', chr(191))    # Spanish Punctuation
                return s

	# HTML translations (callable)
        def html(self,text):
		s = self._html(s)
		return s

	# HTML translations
        def _html(self,text):
		s = text
		s = s.replace('&lt;', '<') 
		s = s.replace('&gt;', '>') 
		s = s.replace('&quot;', '"') 
		s = s.replace('&nbsp;', ' ') 
		s = s.replace('&amp;', '&') 
                return s

	# Unicodes etc (callable)
        def unicode(self,text):
                s = self._convert2escape(text)
		s = self._unicode(s)
		return s

	# Unicodes etc
        def _unicode(self,text):
		s = text
		s = s.replace('\\u201e', '"')    # ORF feed
		s = s.replace('\\u3000', " ") 
		s = s.replace('\\u201c', '"') 
		s = s.replace('\\u201d', '"') 
		s = s.replace("\\'", "'") 
		s = s.replace("\\n", " ") 
                return s

# End of class
