#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: translate_class.py,v 1.24 2016/04/14 06:37:56 bob Exp $
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

	# Escaped codes (from unicode)
	codes = {
		'//' : '/', 	   # Double /
		'  ' : ' ',        # Double spaces
		'\\xa0' : ' ',     # Line feed  to space
		'\\' : "'",	   # Double backslash to apostrophe
		'\\n' : ' ',       # Line feed  to space

		# Special characters
		'\\xc2\\xa1' : '!',        # Inverted exclamation
		'\\xc2\\xa2' : 'c',        # Cent sign
		'\\xc2\\xa3' : '#',        # Pound sign
		'\\xc2\\xa4' : '$',        # Currency sign
		'\\xc2\\xa5' : 'Y',        # Yen sign
		'\\xc2\\xa6' : '|',        # Broken bar
		'\\xc2\\xa7' : '?',        # Section sign
		'\\xc2\\xa8' : ':',        # Diaerisis
		'\\xc2\\xa9' : '(C)',      # Copyright
		'\\xc2\\xaa' : '?',        # Feminal ordinal
		'\\xc2\\xab' : '<<',       # Double left
		'\\xc2\\xac' : '-',        # Not sign
		'\\xc2\\xad' : '',         # Soft hyphen
		'\\xc2\\xae' : '(R)',      # Registered sign
		'\\xc2\\xaf' : '-',        # Macron
		'\\xc2\\xb0' : 'o',        # Degrees sign
		'\\xc2\\xb1' : '+-',       # Plus minus
		'\\xc2\\xb2' : '2',        # Superscript 2
		'\\xc2\\xb3' : '3',        # Superscript 3
		'\\xc2\\xb4' : '',         # Acute accent
		'\\xc2\\xb5' : 'u',        # Micro sign
		'\\xc2\\xb6' : '',         # Pilcrow
		'\\xc2\\xb7' : '.',        # Middle dot
		'\\xc2\\xb8' : '',         # Cedilla
		'\\xc2\\xb9' : '1',        # Superscript 1
		'\\xc2\\xba' : '',         # Masculine indicator
		'\\xc2\\xbb' : '>>',       # Double right
		'\\xc2\\xbc' : '1/4',      # 1/4 fraction
		'\\xc2\\xbd' : '1/2',      # 1/2 Fraction
		'\\xc2\\xbe' : '3/4',      # 3/4 Fraction
		'\\xc2\\xbf' : '?',        # Inverted ?

		# German unicode escape sequences
		'\\xc3\\x83' : chr(223),   # Sharp s es-zett
		'\\xc3\\x9f' : chr(223),   # Sharp s ?
		'\\xc3\\xa4' : chr(228),   # a umlaut
		'\\xc3\\xb6' : chr(246),   # o umlaut
		'\\xc3\\xbc' : chr(252),   # u umlaut
		'\\xc3\\x84' : chr(196),   # A umlaut
		'\\xc3\\x96' : chr(214),   # O umlaut
		'\\xc3\\x9c' : chr(220),   # U umlaut

		# Norwegian unicode escape sequences
		'\\xc3\\x98' : 'O',   # Oslash
		'\\xc3\\xb8' : 'o',   # Oslash
		'\\xc3\\x85' : 'A',   # Aring
		'\\xc3\\x93' : 'O',   # O grave
		'\\xc3\\xa5' : 'a',   # aring
		'\\xc3\\x86' : 'AE',  # AElig
		'\\xc3\\x98' : 'O',   # O crossed
		'\\xc3\\x99' : 'U',   # U grave
		'\\xc3\\xa6' : 'ae',  # aelig
		'\\xc3\\xb0' : 'o',   # o umlaut
		'\\xc3\\xb3' : 'o',   # o tilde
		'\\xc3\\xb8' : 'o',   # oslash
		'\\xc2\\x88' : 'A',   # aelig
		'\\xc2\\xb4' : 'A',   # aelig

		# French (Latin) unicode escape sequences
		'\\xc3\\x80' : 'A',        # A grave
		'\\xc3\\x81' : 'A',        # A acute
		'\\xc3\\x82' : 'A',        # A circumflex
		'\\xc3\\x83' : 'A',        # A tilde
		'\\xc3\\x88' : 'E',        # E grave
		'\\xc3\\x89' : 'E',        # E acute
		'\\xc3\\x8a' : 'E',        # E circumflex
		'\\xc3\\xa0' : chr(224),   # a grave
		'\\xc3\\xa1' : chr(225),   # a acute
		'\\xc3\\xa2' : chr(226),   # a circumflex
		'\\xc3\\xa8' : chr(232),   # e grave
		'\\xc3\\xa9' : chr(233),   # e acute
		'\\xc3\\xaa' : chr(234),   # e circumflex
		'\\xc3\\xb6' : "'",        # Hyphon
		'\\xc3\\xb7' : "/",        # Division sign

		# Hungarian lower case
		'\\xc3\\xb3' : chr(243),   #  
		'\\xc3\\xad' : chr(237),   # 
		'\\xc3\\xb5' : chr(245),   # 
		'\\xc5\\x91' : chr(245),   # 
		'\\xc5\\xb1' : chr(252),   # 
		'\\xc3\\xba' : chr(250),   # Ã

		# Polish unicode escape sequences
		'\\xc4\\x84' : 'A',        # A,
		'\\xc4\\x85' : 'a',        # a,
		'\\xc4\\x86' : 'C',        # C'
		'\\xc4\\x87' : 'c',        # c'
		'\\xc4\\x98' : 'E',        # E,
		'\\xc4\\x99' : 'e',        # e,
		'\\xc5\\x81' : 'L',        # L/
		'\\xc5\\x82' : 'l',        # l/
		'\\xc5\\x83' : 'N',        # N'
		'\\xc5\\x84' : 'n',        # n'
		'\\xc5\\x9a' : 'S',        # S'
		'\\xc5\\x9b' : 's',        # s'
		'\\xc5\\xb9' : 'Z',        # Z'
		'\\xc5\\xba' : 'z',        # z'
		'\\xc5\\xbb' : 'Z',        # Z.
		'\\xc5\\xbc' : 'z',        # z.

		# Greek upper case
		'\\xce\\x91' : 'A',        # Alpha
		'\\xce\\x92' : 'B',        # Beta
		'\\xce\\x93' : 'G',        # Gamma
		'\\xce\\x94' : 'D',        # Delta
		'\\xce\\x95' : 'E',        # Epsilon
		'\\xce\\x96' : 'Z',        # Zeta
		'\\xce\\x97' : 'H',        # Eta
		'\\xce\\x98' : 'TH',       # Theta
		'\\xce\\x99' : 'I',        # Iota
		'\\xce\\x9a' : 'K',        # Kappa
		'\\xce\\x9b' : 'L',        # Lamda
		'\\xce\\x9c' : 'M',        # Mu
		'\\xce\\x9e' : 'N',        # Nu
		'\\xce\\x9f' : 'O',        # Omicron
		'\\xce\\xa0' : 'Pi',       # Pi
		'\\xce '     : 'Pi',       # Pi ?
		'\\xce\\xa1' : 'R',        # Rho
		'\\xce\\xa3' : 'S',        # Sigma
		'\\xce\\xa4' : 'T',        # Tau
		'\\xce\\xa5' : 'Y',        # Upsilon
		'\\xce\\xa6' : 'F',        # Fi
		'\\xce\\xa7' : 'X',        # Chi
		'\\xce\\xa8' : 'PS',       # Psi
		'\\xce\\xa9' : 'O',        # Omega

		# Greek lower case
		'\\xce\\xb1' : 'a',        # Alpha
		'\\xce\\xb2' : 'b',        # Beta
		'\\xce\\xb3' : 'c',        # Gamma
		'\\xce\\xb4' : 'd',        # Delta
		'\\xce\\xb5' : 'e',        # Epsilon
		'\\xce\\xb6' : 'z',        # Zeta
		'\\xce\\xb7' : 'h',        # Eta
		'\\xce\\xb8' : 'th',       # Theta
		'\\xce\\xb9' : 'i',        # Iota
		'\\xce\\xba' : 'k',        # Kappa
		'\\xce\\xbb' : 'l',        # Lamda
		'\\xce\\xbc' : 'm',        # Mu
		'\\xce\\xbd' : 'v',        # Nu
		'\\xce\\xbe' : 'ks',       # Xi
		'\\xce\\xbf' : 'o',        # Omicron
		'\\xce\\xc0' : 'p',        # Pi
		'\\xce\\xc1' : 'r',        # Rho
		'\\xce\\xc3' : 's',        # Sigma
		'\\xce\\xc4' : 't',        # Tau
		'\\xce\\xc5' : 'y',        # Upsilon
		'\\xce\\xc6' : 'f',        # Fi
		'\\xce\\xc7' : 'x',        # Chi
		'\\xce\\xc8' : 'ps',       # Psi
		'\\xce\\xc9' : 'o',        # Omega

		# Currency other special character
		'\\xa3' : chr(156),  # UK pound sign
		'\\xa9' : chr(169),  # Copyright

		# German short hex representation
		'\\xdf' : chr(223),        # Sharp s es-zett
		'\\xe4' : chr(228),        # a umlaut
		'\\xf6' : chr(246),        # o umlaut
		'\\xfc' : chr(252),        # u umlaut
		'\\xc4' : chr(196),        # A umlaut
		'\\xd6' : chr(214),        # O umlaut
		'\\xdc' : chr(220),        # U umlaut

		# Spanish and French
		'\\xe0' : chr(224),    # Small a reverse acute
		'\\xe1' : chr(225),    # Small a acute
		'\\xe2' : chr(226),    # Small audo bashcircumflex
		'\\xe7' : chr(231),    # Small c Cedilla
		'\\xe8' : chr(232),    # Small e grave
		'\\xe9' : chr(233),    # Small e acute
		'\\xea' : chr(234),    # Small e circumflex
		'\\xeb' : chr(235),    # Small e diarisis
		'\\xed' : chr(237),    # Small i acute
		'\\xee' : chr(238),    # Small i circumflex
		'\\xf1' : chr(241),    # Small n tilde
		'\\xf3' : chr(243),    # Small o acute
		'\\xf4' : chr(244),    # Small o circumflex
		'\\xf9' : chr(249),    # Small u circumflex
		'\\xfa' : chr(250),    # Small u acute
		'\\xfb' : chr(251),    # u circumflex

		'\\xc0' : chr(192),    # Small A grave
		'\\xc1' : chr(193),    # Capital A acute

		'\\xc7' : chr(199),    # Capital C Cedilla
		'\\xc9' : chr(201),    # Capital E acute
		'\\xcd' : chr(205),    # Capital I acute
		'\\xd3' : chr(211),    # Capital O acute
		'\\xda' : chr(218),    # Capital U acute

		'\\xbf' : chr(191),    # Spanish Punctuation

		'xb0'  : 'o',	       # Degrees symbol
	}

	HtmlCodes = {
		# Currency
		chr(156) : '#',       # Pound by hash
		chr(169) : '(c)',     # Copyright

		# Norwegian
		chr(216) : 'O',       # Oslash

		# Spanish french
		chr(241) : 'n',       # Small tilde n
		chr(191) : '?',       # Small u acute to u
		chr(224) : 'a',       # Small a grave to a
		chr(225) : 'a',       # Small a acute to a
		chr(226) : 'a',       # Small a circumflex to a
		chr(232) : 'e',       # Small e grave to e
		chr(233) : 'e',       # Small e acute to e
		chr(234) : 'e',       # Small e circumflex to e
		chr(235) : 'e',       # Small e diarisis to e
		chr(237) : 'i',       # Small i acute to i
		chr(238) : 'i',       # Small i circumflex to i
		chr(243) : 'o',       # Small o acute to o
		chr(244) : 'o',       # Small o circumflex to o
		chr(250) : 'u',       # Small u acute to u
		chr(251) : 'u',       # Small u circumflex to u
		chr(192) : 'A',       # Capital A grave to A
		chr(193) : 'A',       # Capital A acute to A
		chr(201) : 'E',       # Capital E acute to E
		chr(205) : 'I',       # Capital I acute to I
		chr(209) : 'N',       # Capital N acute to N
		chr(211) : 'O',       # Capital O acute to O
		chr(218) : 'U',       # Capital U acute to U
		chr(220) : 'U',       # Capital U umlaut to U
		chr(231) : 'c',       # Small c Cedilla
		chr(199) : 'C',       # Capital C Cedilla

		# German
		chr(196) : "Ae",      # A umlaut
		chr(214) : "Oe",      # O umlaut
		chr(220) : "Ue",      # U umlaut
		}

	unicodes = {
		'\\u201e' : '"',       # ORF feed
		'\\u3000' : " ", 
		'\\u201c' : '"', 
		'\\u201d' : '"', 
		'\\u0153' : "oe",      # French oe
		'\\u2009' : ' ',       # Short space to space
		'\\u2013' : '-',       # Long dash to minus sign
		'\\u2019' : "'",       # French apostrophe
		}

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
		for code in self.codes:
			s = s.replace(code, self.codes[code])
		s = s.replace("'oC",'oC')   # Degrees C fudge
		s = s.replace("'oF",'oF')   # Degrees C fudge
		return s

	# HTML translations (callable)
	def html(self,text):
		s = self._html(s)
		_convert_html(s)
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

	# Convert &#nn sequences
	def _convert_html(s):
		c = re.findall('&#[0-9][0-9][0-9]', s)
		c += re.findall('&#[0-9][0-9]', s)
		for html in c:
			ch = int(html.replace('&#', ''))
			if ch > 31 and ch < 127:
				s = s.replace(html,chr(ch))
			else:
				s = s.replace(html,'')
		return s

	# Unicodes etc (callable)
	def unicode(self,text):
		s = self._convert2escape(text)
		s = self._unicode(s)
		return s

	# Unicodes etc
	def _unicode(self,text):
		s = text
		for unicode in self.unicodes:
			s = s.replace(unicode, self.unicodes[unicode])
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
		for HtmlCode in self.HtmlCodes:
			s = s.replace(HtmlCode, self.HtmlCodes[HtmlCode])

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
