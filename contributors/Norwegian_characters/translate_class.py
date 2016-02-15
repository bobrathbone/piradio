#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: translate_class.py,v 1.1 2015/08/15 18:53:06 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#
# Useful Links on character encodings
#  	http://www.zytrax.com/tech/web/entities.html
#	http://www.utf8-chartable.de/
#


import os
import time
import unicodedata
from log_class import Log


log = Log()

class Translate:
	displayUmlauts = True

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


	# Convert escaped characters (umlauts etc.) to normal characters
	def _escape(self,text):
		s = text
		s = s.replace('//', '/')
		s = s.replace('  ', ' ')	# Double spaces
		s = s.replace('\\xa0', ' ')     # Line feed  to space
		s = s.replace("\\'", "'") 	
		s = s.replace("\\n", " ") 	# Line feed  to space

		# German unicode escape sequences
		s = s.replace('\\xc3\\x83', chr(223))   # Sharp s es-zett
		s = s.replace('\\xc3\\x9f', chr(223))   # Sharp s ?
		s = s.replace('\\xc3\\xa4', chr(228))   # a umlaut
		s = s.replace('\\xc3\\xb6', chr(246))   # o umlaut
		s = s.replace('\\xc3\\xbc', chr(252))   # u umlaut
 		s = s.replace('\\xc3\\x84', chr(196))	# A umlaut
		s = s.replace('\\xc3\\x96', chr(214)) 	# O umlaut
 		s = s.replace('\\xc3\\x9c', chr(220))	# U umlaut

		# Norwegian unicode escape sequences
		s = s.replace('\\xc3\\x98', chr(0))   # Oslash
		s = s.replace('\\xc3\\xb8', chr(1))   # Oslash
		s = s.replace('\\xc3\\x85', chr(2))   # Aring
		s = s.replace('\\xc3\\xa5', chr(3))   # aring
		s = s.replace('\\xc3\\x86', chr(4))   # AElig
		s = s.replace('\\xc3\\xa6', chr(5))   # aelig
		

		# French unicode escape sequences
 		s = s.replace('\\xc3\\x80', 'A')	# A grave 
 		s = s.replace('\\xc3\\x81', 'A')	# A acute 
 		s = s.replace('\\xc3\\x82', 'A')	# A circumflex 
 		s = s.replace('\\xc3\\x83', 'A')	# A tilde 
 		s = s.replace('\\xc3\\x88', 'E')	# E grave 
 		s = s.replace('\\xc3\\x89', 'E')	# E acute 
 		s = s.replace('\\xc3\\x8a', 'E')	# E circumflex 
 		s = s.replace('\\xc3\\xa0', chr(224))	# a grave
 		s = s.replace('\\xc3\\xa1', chr(225))	# a acute
 		s = s.replace('\\xc3\\xa2', chr(226))	# a circumflex
 		s = s.replace('\\xc3\\xa8', chr(232))	# e grave
 		s = s.replace('\\xc3\\xa9', chr(233))	# e acute
 		s = s.replace('\\xc3\\xaa', chr(234))	# e circumflex
 		s = s.replace('\\xc3\\xb6', 'u')	# u diaris

		# Hungarian lower case
		s = s.replace('\\xc3\\xb3', chr(243))   # ó
		s = s.replace('\\xc3\\xad', chr(237))   # í
		s = s.replace('\\xc3\\xb5', chr(245))   # ő
		s = s.replace('\\xc5\\x91', chr(245))   # ő
		s = s.replace('\\xc5\\xb1', chr(252))   # ű
		s = s.replace('\\xc3\\xba', chr(250))   # ú

		# Greek upper case
 		s = s.replace('\\xce\\x91', 'A')	# Alpha
 		s = s.replace('\\xce\\x92', 'B')	# Beta
 		s = s.replace('\\xce\\x93', 'G')	# Gamma
 		s = s.replace('\\xce\\x94', 'D')	# Delta
 		s = s.replace('\\xce\\x95', 'E')	# Epsilon
 		s = s.replace('\\xce\\x96', 'Z')	# Zeta
 		s = s.replace('\\xce\\x97', 'H')	# Eta
 		s = s.replace('\\xce\\x98', 'TH')	# Theta
 		s = s.replace('\\xce\\x99', 'I')	# Iota
 		s = s.replace('\\xce\\x9a', 'K')	# Kappa
 		s = s.replace('\\xce\\x9b', 'L')	# Lamda 
 		s = s.replace('\\xce\\x9c', 'M')	# Mu
 		s = s.replace('\\xce\\x9e', 'N')	# Nu
 		s = s.replace('\\xce\\x9f', 'O')	# Omicron
 		s = s.replace('\\xce\\xa0', 'P')	# Pi 
 		s = s.replace('\\xce ', 'P')		# Pi ?
 		s = s.replace('\\xce\\xa1', 'R')	# Rho
 		s = s.replace('\\xce\\xa3', 'S')	# Sigma
 		s = s.replace('\\xce\\xa4', 'T')	# Tau
 		s = s.replace('\\xce\\xa5', 'Y')	# Upsilon
 		s = s.replace('\\xce\\xa6', 'F')	# Fi
 		s = s.replace('\\xce\\xa7', 'X')	# Chi
 		s = s.replace('\\xce\\xa8', 'PS')	# Psi
 		s = s.replace('\\xce\\xa9', 'O')	# Omega

		# Greek lower case
 		s = s.replace('\\xce\\xb1', 'a')	# Alpha
 		s = s.replace('\\xce\\xb2', 'b')	# Beta
 		s = s.replace('\\xce\\xb3', 'c')	# Gamma
 		s = s.replace('\\xce\\xb4', 'd')	# Delta
 		s = s.replace('\\xce\\xb5', 'e')	# Epsilon
 		s = s.replace('\\xce\\xb6', 'z')	# Zeta
 		s = s.replace('\\xce\\xb7', 'h')	# Eta
 		s = s.replace('\\xce\\xb8', 'th')	# Theta
 		s = s.replace('\\xce\\xb9', 'i')	# Iota
 		s = s.replace('\\xce\\xba', 'k')	# Kappa
 		s = s.replace('\\xce\\xbb', 'l')	# Lamda 
 		s = s.replace('\\xce\\xbc', 'm')	# Mu
 		s = s.replace('\\xce\\xbd', 'v')	# Nu
 		s = s.replace('\\xce\\xbe', 'ks')	# Xi
 		s = s.replace('\\xce\\xbf', 'o')	# Omicron
 		s = s.replace('\\xce\\xc0', 'p')	# Pi 
 		s = s.replace('\\xce\\xc1', 'r')	# Rho
 		s = s.replace('\\xce\\xc3', 's')	# Sigma
 		s = s.replace('\\xce\\xc4', 't')	# Tau
 		s = s.replace('\\xce\\xc5', 'y')	# Upsilon
 		s = s.replace('\\xce\\xc6', 'f')	# Fi
 		s = s.replace('\\xce\\xc7', 'x')	# Chi
 		s = s.replace('\\xce\\xc8', 'ps')	# Psi
 		s = s.replace('\\xce\\xc9', 'o')	# Omega

		# Currency other special character
		s = s.replace('\\xa3', chr(156))  # UK pound sign
		s = s.replace('\\xa9', chr(169))  # Copyright

		# German short hex representation
		s = s.replace('\\xdf', chr(223))   	# Sharp s es-zett
		s = s.replace('\\xe4', chr(228))   	# a umlaut
		s = s.replace('\\xf6', chr(246))   	# o umlaut
		s = s.replace('\\xfc', chr(252))   	# u umlaut
 		s = s.replace('\\xc4', chr(196))	# A umlaut
		s = s.replace('\\xd6', chr(214)) 	# O umlaut
 		s = s.replace('\\xdc', chr(220))	# U umlaut

		# Spanish and French
		s = s.replace('\\xe0', chr(224))    # Small a reverse acute
		s = s.replace('\\xe1', chr(225))    # Small a acute
		s = s.replace('\\xe2', chr(226))    # Small audo bashcircumflex
		s = s.replace('\\xe7', chr(231))    # Small c Cedilla 
		s = s.replace('\\xe8', chr(232))    # Small e grave
		s = s.replace('\\xe9', chr(233))    # Small e acute
		s = s.replace('\\xea', chr(234))    # Small e circumflex
		s = s.replace('\\xeb', chr(235))    # Small e diarisis
		s = s.replace('\\xed', chr(237))    # Small i acute
		s = s.replace('\\xee', chr(238))    # Small i circumflex
		s = s.replace('\\xf1', chr(241))    # Small n tilde
		s = s.replace('\\xf3', chr(243))    # Small o acute
		s = s.replace('\\xf4', chr(244))    # Small o circumflex
		s = s.replace('\\xf9', chr(249))    # Small u circumflex
		s = s.replace('\\xfa', chr(250))    # Small u acute
 		s = s.replace('\\xfb', chr(251))    # u circumflex

		s = s.replace('\\xc0', chr(192))    # Small A grave
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
		s = s.replace('&copy;', '(c)') 
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
		s = s.replace('\\u0153', "oe")      # French oe
		s = s.replace('\\u2009', " ")       # Short space to space
		s = s.replace('\\u2013', "-")       # Long dash to minus sign
		s = s.replace('\\u2019', "'")       # French apostrophe
		return s

	# Decode greek
	def decode_greek(self,text):
		s = text.decode('macgreek')
		return s

        # Display umlats as oe ae etc
        def displayUmlauts(self,value):
                self.displayUmlauts = value
                return

	# Translate special characters (umlautes etc) to LCD values
	# See standard character patterns for LCD display
	def toLCD(self,sp):
		s = sp

		# Currency
		s = s.replace(chr(156), '#')       # Pound by hash
		s = s.replace(chr(169), '(c)')     # Copyright

		# Norwegian
		s = s.replace(chr(216), '0')       # Oslash

		# Spanish french
		s = s.replace(chr(241), 'n')       # Small tilde n
		s = s.replace(chr(191), '?')       # Small u acute to u
		s = s.replace(chr(224), 'a')       # Small a grave to a
		s = s.replace(chr(225), 'a')       # Small a acute to a
		s = s.replace(chr(226), 'a')       # Small a circumflex to a
		s = s.replace(chr(232), 'e')       # Small e grave to e
		s = s.replace(chr(233), 'e')       # Small e acute to e
		s = s.replace(chr(234), 'e')       # Small e circumflex to e
		s = s.replace(chr(235), 'e')       # Small e diarisis to e
		s = s.replace(chr(237), 'i')       # Small i acute to i
		s = s.replace(chr(238), 'i')       # Small i circumflex to i
		s = s.replace(chr(243), 'o')       # Small o acute to o
		s = s.replace(chr(244), 'o')       # Small o circumflex to o
		s = s.replace(chr(250), 'u')       # Small u acute to u
		s = s.replace(chr(251), 'u')       # Small u circumflex to u
		s = s.replace(chr(192), 'A')       # Capital A grave to A
		s = s.replace(chr(193), 'A')       # Capital A acute to A
		s = s.replace(chr(201), 'E')       # Capital E acute to E
		s = s.replace(chr(205), 'I')       # Capital I acute to I
		s = s.replace(chr(209), 'N')       # Capital N acute to N
		s = s.replace(chr(211), 'O')       # Capital O acute to O
		s = s.replace(chr(218), 'U')       # Capital U acute to U
		s = s.replace(chr(220), 'U')       # Capital U umlaut to U
		s = s.replace(chr(231), 'c')       # Small c Cedilla
		s = s.replace(chr(199), 'C')       # Capital C Cedilla

		# German
		s = s.replace(chr(196), "Ae")	   # A umlaut
		s = s.replace(chr(214), "Oe")	   # O umlaut
		s = s.replace(chr(220), "Ue")	   # U umlaut

		if self.displayUmlauts:
			s = s.replace(chr(223), chr(226))       # Sharp s
			s = s.replace(chr(246), chr(239))       # o umlaut (Problem in Hungarian?)
			s = s.replace(chr(228), chr(225))       # a umlaut
			s = s.replace(chr(252), chr(245))       # u umlaut (Problem in Hungarian?)
		else:
			s = s.replace(chr(228), "ae")	   # a umlaut
			s = s.replace(chr(223), "ss")	   # Sharp s
			s = s.replace(chr(246), "oe")	   # o umlaut
			s = s.replace(chr(252), "ue")	   # u umlaut
		return s



# End of class
