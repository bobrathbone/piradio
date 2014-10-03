#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Python Character Mapping Codec for the HD44780 display controller

"""#"

import codecs

### Codec APIs

class Codec_A00(codecs.Codec):

    def encode(self,input,errors='strict'):
        return codecs.charmap_encode(input,errors,encoding_map_A00)

    def decode(self,input,errors='strict'):
        return codecs.charmap_decode(input,errors,decoding_table_A00)

class IncrementalEncoder_A00(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return codecs.charmap_encode(input,self.errors,encoding_map_A00)[0]

class IncrementalDecoder_A00(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return codecs.charmap_decode(input,self.errors,decoding_table_A00)[0]

class StreamWriter_A00(Codec_A00,codecs.StreamWriter):
    pass

class StreamReader_A00(Codec_A00,codecs.StreamReader):
    pass

class Codec_A02(codecs.Codec):

    def encode(self,input,errors='strict'):
        return codecs.charmap_encode(input,errors,encoding_map_A02)

    def decode(self,input,errors='strict'):
        return codecs.charmap_decode(input,errors,decoding_table_A02)

class IncrementalEncoder_A02(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return codecs.charmap_encode(input,self.errors,encoding_map_A02)[0]

class IncrementalDecoder_A02(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return codecs.charmap_decode(input,self.errors,decoding_table_A02)[0]

class StreamWriter_A02(Codec_A02,codecs.StreamWriter):
    pass

class StreamReader_A02(Codec_A02,codecs.StreamReader):
    pass

### encodings module API

def get_registration_entry_A00():
    return codecs.CodecInfo(
        name='HD44780_A00',
        encode=Codec().encode_A00,
        decode=Codec().decode_A00,
        incrementalencoder=IncrementalEncoder_A00,
        incrementaldecoder=IncrementalDecoder_A00,
        streamreader=StreamReader_A00,
        streamwriter=StreamWriter_A00,
    )
def get_registration_entry_A02():
    return codecs.CodecInfo(
        name='HD44780_A02',
        encode=Codec().encode_A02,
        decode=Codec().decode_A02,
        incrementalencoder=IncrementalEncoder_A02,
        incrementaldecoder=IncrementalDecoder_A02,
        streamreader=StreamReader_A02,
        streamwriter=StreamWriter_A02,
    )
codecs.register(get_registration_entry_A00)
codecs.register(get_registration_entry_A02)
### Decoding Map

decoding_map_A00 = codecs.make_identity_dict(range(256))
decoding_map_A00.update({
    0x5c: 0xa5,
    0x7e: 0x2192,
    0x7f: 0x2190,
    0xe0: 0x3b1,
    0xe1: 0xe4,
    0xe2: 0x3b2,
    0xe3: 0x3b5,
    0xe4: 0x3bc,
    0xe5: 0x3c3,
    0xe6: 0x3c1,
    0xe7: 0x71,
    0xe8: 0x221a,
    0xe9: 0x207b,
    0xeb: 0x1d12a,
    0xec: 0xa2,
    0xed: 0xa3,
    0xee: 0x101,
    0xef: 0xf6,
    0xf0: 0x70,
    0xf1: 0x71,
    0xf2: 0x3b8,
    0xf3: 0x221e,
    0xf4: 0x3a9,
    0xf5: 0xfc,
    0xf6: 0x3a3,
    0xf7: 0x3c0,
    0xf8: 0x3c7,
    0xfd: 0xf7,
    0xfe: 0x20,
    0xff: 0x2588
})

decoding_map_A02 = codecs.make_identity_dict(range(256))
decoding_map_A02.update({
    0x0: 0x0,
    0x1: 0x1,
    0x2: 0x2,
    0x3: 0x3,
    0x4: 0x4,
    0x5: 0x5,
    0x6: 0x6,
    0x7: 0x7,
    0x8: 0x8,
    0x9: 0x9,
    0xa: 0xa,
    0xb: 0xb,
    0xc: 0xc,
    0xd: 0xd,
    0xe: 0xe,
    0xf: 0xf,
    0x10: 0x25b6,
    0x11: 0x25c0,
    0x12: 0x201c,
    0x13: 0x201d,
    0x14: 0x23eb,
    0x15: 0x23ec,
    0x16: 0x25cf,
    0x17: 0x21b2,
    0x18: 0x2191,
    0x19: 0x2193,
    0x1a: 0x2190,
    0x1b: 0x2192,
    0x1c: 0x2264,
    0x1d: 0x2265,
    0x1e: 0x25b2,
    0x1f: 0x25bc,
    0x20: 0x20,
    0x21: 0x21,
    0x22: 0x22,
    0x23: 0x23,
    0x24: 0x24,
    0x25: 0x25,
    0x26: 0x26,
    0x27: 0x27,
    0x28: 0x28,
    0x29: 0x29,
    0x2a: 0x2a,
    0x2b: 0x2b,
    0x2c: 0x2c,
    0x2d: 0x2d,
    0x2e: 0x2e,
    0x2f: 0x2f,
    0x30: 0x30,
    0x31: 0x31,
    0x32: 0x32,
    0x33: 0x33,
    0x34: 0x34,
    0x35: 0x35,
    0x36: 0x36,
    0x37: 0x37,
    0x38: 0x38,
    0x39: 0x39,
    0x3a: 0x3a,
    0x3b: 0x3b,
    0x3c: 0x3c,
    0x3d: 0x3d,
    0x3e: 0x3e,
    0x3f: 0x3f,
    0x40: 0x40,
    0x41: 0x41,
    0x42: 0x42,
    0x43: 0x43,
    0x44: 0x44,
    0x45: 0x45,
    0x46: 0x46,
    0x47: 0x47,
    0x48: 0x48,
    0x49: 0x49,
    0x4a: 0x4a,
    0x4b: 0x4b,
    0x4c: 0x4c,
    0x4d: 0x4d,
    0x4e: 0x4e,
    0x4f: 0x4f,
    0x50: 0x50,
    0x51: 0x51,
    0x52: 0x52,
    0x53: 0x53,
    0x54: 0x54,
    0x55: 0x55,
    0x56: 0x56,
    0x57: 0x57,
    0x58: 0x58,
    0x59: 0x59,
    0x5a: 0x5a,
    0x5b: 0x5b,
    0x5c: 0x5c,
    0x5d: 0x5d,
    0x5e: 0x5e,
    0x5f: 0x5f,
    0x60: 0x60,
    0x61: 0x61,
    0x62: 0x62,
    0x63: 0x63,
    0x64: 0x64,
    0x65: 0x65,
    0x66: 0x66,
    0x67: 0x67,
    0x68: 0x68,
    0x69: 0x69,
    0x6a: 0x6a,
    0x6b: 0x6b,
    0x6c: 0x6c,
    0x6d: 0x6d,
    0x6e: 0x6e,
    0x6f: 0x6f,
    0x70: 0x70,
    0x71: 0x71,
    0x72: 0x72,
    0x73: 0x73,
    0x74: 0x74,
    0x75: 0x75,
    0x76: 0x76,
    0x77: 0x77,
    0x78: 0x78,
    0x79: 0x79,
    0x7a: 0x7a,
    0x7b: 0x7b,
    0x7c: 0x7c,
    0x7d: 0x7d,
    0x7e: 0x7e,
    0x7f: 0x2302,
    0x80: 0x411,
    0x81: 0x414,
    0x82: 0x416,
    0x83: 0x417,
    0x84: 0x418,
    0x85: 0x419,
    0x86: 0x41b,
    0x87: 0x41f,
    0x88: 0x423,
    0x89: 0x426,
    0x8a: 0x427,
    0x8b: 0x428,
    0x8c: 0x429,
    0x8d: 0x42a,
    0x8e: 0x42c,
    0x8f: 0x42d,
    0x90: 0x3b1,
    0x91: 0x266a,
    0x92: 0x393,
    0x93: 0x3c0,
    0x94: 0x3a3,
    0x95: 0x3c3,
    0x96: 0x266b,
    0x97: 0x3c4,
    0x98: 0x1f514,
    0x99: 0x398,
    0x9a: 0x3a9,
    0x9b: 0x3b4,
    0x9c: 0x221e,
    0x9d: 0x2665,
    0x9e: 0x3b5,
    0x9f: 0x2229,
    0xa0: 0x275a,
    0xa1: 0xa1,
    0xa2: 0xa2,
    0xa3: 0xa3,
    0xa4: 0xa4,
    0xa5: 0xa5,
    0xa6: 0xa6,
    0xa7: 0xa7,
    0xa8: 0x2a0d,
    0xa9: 0xa9,
    0xaa: 0xaa,
    0xab: 0xab,
    0xac: 0x42e,
    0xad: 0x42f,
    0xae: 0xae,
    0xaf: 0x2018,
    0xb0: 0xb0,
    0xb1: 0xb1,
    0xb2: 0xb2,
    0xb3: 0xb3,
    0xb4: 0x20a7,
    0xb5: 0x3bc,
    0xb6: 0xb6,
    0xb7: 0x22c5,
    0xb8: 0x3c9,
    0xb9: 0xb9,
    0xba: 0xba,
    0xbb: 0xbb,
    0xbc: 0xbc,
    0xbd: 0xbd,
    0xbe: 0xbe,
    0xbf: 0xbf,
    0xc0: 0xc0,
    0xc1: 0xc1,
    0xc2: 0xc2,
    0xc3: 0xc3,
    0xc4: 0xc4,
    0xc5: 0xc5,
    0xc6: 0xc6,
    0xc7: 0xc7,
    0xc8: 0xc8,
    0xc9: 0xc9,
    0xca: 0xca,
    0xcb: 0xcb,
    0xcc: 0xcc,
    0xcd: 0xcd,
    0xce: 0xce,
    0xcf: 0xcf,
    0xd0: 0xd0,
    0xd1: 0xd1,
    0xd2: 0xd2,
    0xd3: 0xd3,
    0xd4: 0xd4,
    0xd5: 0xd5,
    0xd6: 0xd6,
    0xd7: 0xd7,
    0xd8: 0x3a6,
    0xd9: 0xd9,
    0xda: 0xda,
    0xdb: 0xdb,
    0xdc: 0xdc,
    0xdd: 0xdd,
    0xde: 0xde,
    0xdf: 0xdf,
    0xe0: 0xe0,
    0xe1: 0xe1,
    0xe2: 0xe2,
    0xe3: 0xe3,
    0xe4: 0xe4,
    0xe5: 0xe5,
    0xe6: 0xe6,
    0xe7: 0xe7,
    0xe8: 0xe8,
    0xe9: 0xe9,
    0xea: 0xea,
    0xeb: 0xeb,
    0xec: 0xec,
    0xed: 0xed,
    0xee: 0xee,
    0xef: 0xef,
    0xf0: 0xf0,
    0xf1: 0xf1,
    0xf2: 0xf2,
    0xf3: 0xf3,
    0xf4: 0xf4,
    0xf5: 0xf5,
    0xf6: 0xf6,
    0xf7: 0xf7,
    0xf8: 0xf8,
    0xf9: 0xf9,
    0xfa: 0xfa,
    0xfb: 0xfb,
    0xfc: 0xfc,
    0xfd: 0xfd,
    0xfe: 0xfe,
    0xff: 0xff
})

### Decoding Table

decoding_table_A02 = (
    u'\x00'     #  0x0000 -> NULL
    u'\x01'     #  0x0001 -> START OF HEADING
    u'\x02'     #  0x0002 -> START OF TEXT
    u'\x03'     #  0x0003 -> END OF TEXT
    u'\x04'     #  0x0004 -> END OF TRANSMISSION
    u'\x05'     #  0x0005 -> ENQUIRY
    u'\x06'     #  0x0006 -> ACKNOWLEDGE
    u'\x07'     #  0x0007 -> BELL
    u'\x08'     #  0x0008 -> BACKSPACE
    u'\t'       #  0x0009 -> HORIZONTAL TABULATION
    u'\n'       #  0x000a -> LINE FEED
    u'\x0b'     #  0x000b -> VERTICAL TABULATION
    u'\x0c'     #  0x000c -> FORM FEED
    u'\r'       #  0x000d -> CARRIAGE RETURN
    u'\x0e'     #  0x000e -> SHIFT OUT
    u'\x0f'     #  0x000f -> SHIFT IN

    u'▶'        #   black right-pointing triangle
    u'◀'        #   black left-pointing triangle
    u'“'        #  
    u'”'        #   
    u'⏫'       # 
    u'⏬'     # 
    u'●'     # 
    u'↲'     #  

    u'↑'     #  
    u'↓'     #  
    u'←'     #  
    u'→'     #  
    u'≤'     #  
    u'≥'     #  
    u'▲'     #  
    u'▼'     #  

    u' '        #  0x0020 -> SPACE
    u'!'        #  0x0021 -> EXCLAMATION MARK
    u'"'        #  0x0022 -> QUOTATION MARK
    u'#'        #  0x0023 -> NUMBER SIGN
    u'$'        #  0x0024 -> DOLLAR SIGN
    u'%'        #  0x0025 -> PERCENT SIGN
    u'&'        #  0x0026 -> AMPERSAND
    u"'"        #  0x0027 -> APOSTROPHE
    u'('        #  0x0028 -> LEFT PARENTHESIS
    u')'        #  0x0029 -> RIGHT PARENTHESIS
    u'*'        #  0x002a -> ASTERISK
    u'+'        #  0x002b -> PLUS SIGN
    u','        #  0x002c -> COMMA
    u'-'        #  0x002d -> HYPHEN-MINUS
    u'.'        #  0x002e -> FULL STOP
    u'/'        #  0x002f -> SOLIDUS

    u'0'        #  0x0030 -> DIGIT ZERO
    u'1'        #  0x0031 -> DIGIT ONE
    u'2'        #  0x0032 -> DIGIT TWO
    u'3'        #  0x0033 -> DIGIT THREE
    u'4'        #  0x0034 -> DIGIT FOUR
    u'5'        #  0x0035 -> DIGIT FIVE
    u'6'        #  0x0036 -> DIGIT SIX
    u'7'        #  0x0037 -> DIGIT SEVEN
    u'8'        #  0x0038 -> DIGIT EIGHT
    u'9'        #  0x0039 -> DIGIT NINE
    u':'        #  0x003a -> COLON
    u';'        #  0x003b -> SEMICOLON
    u'<'        #  0x003c -> LESS-THAN SIGN
    u'='        #  0x003d -> EQUALS SIGN
    u'>'        #  0x003e -> GREATER-THAN SIGN
    u'?'        #  0x003f -> QUESTION MARK

    u'@'        #  0x0040 -> COMMERCIAL AT
    u'A'        #  0x0041 -> LATIN CAPITAL LETTER A
    u'B'        #  0x0042 -> LATIN CAPITAL LETTER B
    u'C'        #  0x0043 -> LATIN CAPITAL LETTER C
    u'D'        #  0x0044 -> LATIN CAPITAL LETTER D
    u'E'        #  0x0045 -> LATIN CAPITAL LETTER E
    u'F'        #  0x0046 -> LATIN CAPITAL LETTER F
    u'G'        #  0x0047 -> LATIN CAPITAL LETTER G
    u'H'        #  0x0048 -> LATIN CAPITAL LETTER H
    u'I'        #  0x0049 -> LATIN CAPITAL LETTER I
    u'J'        #  0x004a -> LATIN CAPITAL LETTER J
    u'K'        #  0x004b -> LATIN CAPITAL LETTER K
    u'L'        #  0x004c -> LATIN CAPITAL LETTER L
    u'M'        #  0x004d -> LATIN CAPITAL LETTER M
    u'N'        #  0x004e -> LATIN CAPITAL LETTER N
    u'O'        #  0x004f -> LATIN CAPITAL LETTER O

    u'P'        #  0x0050 -> LATIN CAPITAL LETTER P
    u'Q'        #  0x0051 -> LATIN CAPITAL LETTER Q
    u'R'        #  0x0052 -> LATIN CAPITAL LETTER R
    u'S'        #  0x0053 -> LATIN CAPITAL LETTER S
    u'T'        #  0x0054 -> LATIN CAPITAL LETTER T
    u'U'        #  0x0055 -> LATIN CAPITAL LETTER U
    u'V'        #  0x0056 -> LATIN CAPITAL LETTER V
    u'W'        #  0x0057 -> LATIN CAPITAL LETTER W
    u'X'        #  0x0058 -> LATIN CAPITAL LETTER X
    u'Y'        #  0x0059 -> LATIN CAPITAL LETTER Y
    u'Z'        #  0x005a -> LATIN CAPITAL LETTER Z
    u'['        #  0x005b -> LEFT SQUARE BRACKET
    u'\\'       #  0x005c -> REVERSE SOLIDUS
    u']'        #  0x005d -> RIGHT SQUARE BRACKET
    u'^'        #  0x005e -> CIRCUMFLEX ACCENT
    u'_'        #  0x005f -> LOW LINE

    u'`'        #  0x0060 -> GRAVE ACCENT
    u'a'        #  0x0061 -> LATIN SMALL LETTER A
    u'b'        #  0x0062 -> LATIN SMALL LETTER B
    u'c'        #  0x0063 -> LATIN SMALL LETTER C
    u'd'        #  0x0064 -> LATIN SMALL LETTER D
    u'e'        #  0x0065 -> LATIN SMALL LETTER E
    u'f'        #  0x0066 -> LATIN SMALL LETTER F
    u'g'        #  0x0067 -> LATIN SMALL LETTER G
    u'h'        #  0x0068 -> LATIN SMALL LETTER H
    u'i'        #  0x0069 -> LATIN SMALL LETTER I
    u'j'        #  0x006a -> LATIN SMALL LETTER J
    u'k'        #  0x006b -> LATIN SMALL LETTER K
    u'l'        #  0x006c -> LATIN SMALL LETTER L
    u'm'        #  0x006d -> LATIN SMALL LETTER M
    u'n'        #  0x006e -> LATIN SMALL LETTER N
    u'o'        #  0x006f -> LATIN SMALL LETTER O

    u'p'        #  0x0070 -> LATIN SMALL LETTER P
    u'q'        #  0x0071 -> LATIN SMALL LETTER Q
    u'r'        #  0x0072 -> LATIN SMALL LETTER R
    u's'        #  0x0073 -> LATIN SMALL LETTER S
    u't'        #  0x0074 -> LATIN SMALL LETTER T
    u'u'        #  0x0075 -> LATIN SMALL LETTER U
    u'v'        #  0x0076 -> LATIN SMALL LETTER V
    u'w'        #  0x0077 -> LATIN SMALL LETTER W
    u'x'        #  0x0078 -> LATIN SMALL LETTER X
    u'y'        #  0x0079 -> LATIN SMALL LETTER Y
    u'z'        #  0x007a -> LATIN SMALL LETTER Z
    u'{'        #  0x007b -> LEFT CURLY BRACKET
    u'|'        #  0x007c -> VERTICAL LINE
    u'}'        #  0x007d -> RIGHT CURLY BRACKET
    u'~'        #  0x007e -> TILDE
    u'⌂'        # 

    u'Б'     #  0x0080 -> LATIN CAPITAL LETTER C WITH CEDILLA
    u'Д'     #  0x0081 -> LATIN SMALL LETTER U WITH DIAERESIS
    u'Ж'     #  0x0082 -> LATIN SMALL LETTER E WITH ACUTE
    u'З'     #  0x0083 -> LATIN SMALL LETTER A WITH CIRCUMFLEX
    u'И'     #  0x0084 -> LATIN SMALL LETTER A WITH DIAERESIS
    u'Й'     #  0x0085 -> LATIN SMALL LETTER A WITH GRAVE
    u'Л'     #  0x0086 -> LATIN SMALL LETTER A WITH RING ABOVE
    u'П'     #  0x0087 -> LATIN SMALL LETTER C WITH CEDILLA
    u'У'     #  0x0088 -> LATIN SMALL LETTER E WITH CIRCUMFLEX
    u'Ц'     #  0x0089 -> LATIN SMALL LETTER E WITH DIAERESIS
    u'Ч'     #  0x008a -> LATIN SMALL LETTER E WITH GRAVE
    u'Ш'     #  0x008b -> LATIN SMALL LETTER I WITH DIAERESIS
    u'Щ'     #  0x008c -> LATIN SMALL LETTER I WITH CIRCUMFLEX
    u'Ъ'     #  0x008d -> LATIN SMALL LETTER I WITH GRAVE
    u'Ь'     #  0x008e -> LATIN CAPITAL LETTER A WITH DIAERESIS
    u'Э'     #  0x008f -> LATIN CAPITAL LETTER A WITH RING ABOVE

    u'α'     #  0x0090 -> LATIN CAPITAL LETTER E WITH ACUTE
    u'♪'     #  0x0091 -> LATIN SMALL LIGATURE AE
    u'Γ'     #  0x0092 -> LATIN CAPITAL LIGATURE AE
    u'π'     #  0x0093 -> LATIN SMALL LETTER O WITH CIRCUMFLEX
    u'Σ'     #  0x0094 -> LATIN SMALL LETTER O WITH DIAERESIS
    u'σ'     #  0x0095 -> LATIN SMALL LETTER O WITH GRAVE
    u'♫'     #  0x0096 -> LATIN SMALL LETTER U WITH CIRCUMFLEX
    u'τ'     #  0x0097 -> LATIN SMALL LETTER U WITH GRAVE
    u'🔔'     #  0x0098 ->  BELL
    u'Θ'     #  0x0099 -> LATIN CAPITAL LETTER O WITH DIAERESIS
    u'Ω'     #  0x009a -> LATIN CAPITAL LETTER U WITH DIAERESIS
    u'δ'     #  0x009b -> CENT SIGN
    u'∞'     #  0x009c -> POUND SIGN
    u'♥'     #  0x009d -> YEN SIGN
    u'ε'   #  0x009e -> PESETA SIGN
    u'∩'   #  0x009f -> LATIN SMALL LETTER F WITH HOOK

    u'❚'     #  0x00a0 -> Pause sign
    u'¡'     #  0x00a1 -> LATIN SMALL LETTER I WITH ACUTE
    u'¢'     #  0x00a2 -> LATIN SMALL LETTER O WITH ACUTE
    u'£'     #  0x00a3 -> LATIN SMALL LETTER U WITH ACUTE
    u'¤'     #  0x00a4 -> LATIN SMALL LETTER N WITH TILDE
    u'¥'     #  0x00a5 -> LATIN CAPITAL LETTER N WITH TILDE
    u'¦'     #  0x00a6 -> FEMININE ORDINAL INDICATOR
    u'§'     #  0x00a7 -> MASCULINE ORDINAL INDICATOR
    u'⨍'     #  0x00a8 -> INVERTED QUESTION MARK
    u'©'   #  0x00a9 -> REVERSED NOT SIGN
    u'ª'     #  0x00aa -> NOT SIGN
    u'«'     #  0x00ab -> VULGAR FRACTION ONE HALF
    u'Ю'     #  0x00ac -> VULGAR FRACTION ONE QUARTER
    u'Я'     #  0x00ad -> INVERTED EXCLAMATION MARK
    u'®'     #  0x00ae -> LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'‘'     #  0x00af -> RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK

    u'°'   #  0x00b0 -> LIGHT SHADE
    u'±'   #  0x00b1 -> MEDIUM SHADE
    u'²'   #  0x00b2 -> DARK SHADE
    u'³'   #  0x00b3 -> BOX DRAWINGS LIGHT VERTICAL
    u'₧'   #  0x00b4 -> BOX DRAWINGS LIGHT VERTICAL AND LEFT
    u'μ'   #  0x00b5 -> BOX DRAWINGS VERTICAL SINGLE AND LEFT DOUBLE
    u'¶'   #  0x00b6 -> BOX DRAWINGS VERTICAL DOUBLE AND LEFT SINGLE
    u'⋅'   #  0x00b7 -> BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE
    u'ω'   #  0x00b8 -> BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE
    u'¹'   #  0x00b9 -> BOX DRAWINGS DOUBLE VERTICAL AND LEFT
    u'º'   #  0x00ba -> BOX DRAWINGS DOUBLE VERTICAL
    u'»'   #  0x00bb -> BOX DRAWINGS DOUBLE DOWN AND LEFT
    u'¼'   #  0x00bc -> BOX DRAWINGS DOUBLE UP AND LEFT
    u'½'   #  0x00bd -> BOX DRAWINGS UP DOUBLE AND LEFT SINGLE
    u'¾'   #  0x00be -> BOX DRAWINGS UP SINGLE AND LEFT DOUBLE
    u'¿'   #  0x00bf -> BOX DRAWINGS LIGHT DOWN AND LEFT

    u'À'   #  0x00c0 -> BOX DRAWINGS LIGHT UP AND RIGHT
    u'Á'   #  0x00c1 -> BOX DRAWINGS LIGHT UP AND HORIZONTAL
    u'Â'   #  0x00c2 -> BOX DRAWINGS LIGHT DOWN AND HORIZONTAL
    u'Ã'   #  0x00c3 -> BOX DRAWINGS LIGHT VERTICAL AND RIGHT
    u'Ä'   #  0x00c4 -> BOX DRAWINGS LIGHT HORIZONTAL
    u'Å'   #  0x00c5 -> BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL
    u'Æ'   #  0x00c6 -> BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE
    u'Ç'   #  0x00c7 -> BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE
    u'È'   #  0x00c8 -> BOX DRAWINGS DOUBLE UP AND RIGHT
    u'É'   #  0x00c9 -> BOX DRAWINGS DOUBLE DOWN AND RIGHT
    u'Ê'   #  0x00ca -> BOX DRAWINGS DOUBLE UP AND HORIZONTAL
    u'Ë'   #  0x00cb -> BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL
    u'Ì'   #  0x00cc -> BOX DRAWINGS DOUBLE VERTICAL AND RIGHT
    u'Í'   #  0x00cd -> BOX DRAWINGS DOUBLE HORIZONTAL
    u'Î'   #  0x00ce -> BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL
    u'Ï'   #  0x00cf -> BOX DRAWINGS UP SINGLE AND HORIZONTAL DOUBLE

    u'Ð'   #  0x00d0 -> BOX DRAWINGS UP DOUBLE AND HORIZONTAL SINGLE
    u'Ñ'   #  0x00d1 -> BOX DRAWINGS DOWN SINGLE AND HORIZONTAL DOUBLE
    u'Ò'   #  0x00d2 -> BOX DRAWINGS DOWN DOUBLE AND HORIZONTAL SINGLE
    u'Ó'   #  0x00d3 -> BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE
    u'Ô'   #  0x00d4 -> BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE
    u'Õ'   #  0x00d5 -> BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE
    u'Ö'   #  0x00d6 -> BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE
    u'×'   #  0x00d7 -> BOX DRAWINGS VERTICAL DOUBLE AND HORIZONTAL SINGLE
    u'Φ'   #  0x00d8 -> BOX DRAWINGS VERTICAL SINGLE AND HORIZONTAL DOUBLE
    u'Ù'   #  0x00d9 -> BOX DRAWINGS LIGHT UP AND LEFT
    u'Ú'   #  0x00da -> BOX DRAWINGS LIGHT DOWN AND RIGHT
    u'Û'   #  0x00db -> FULL BLOCK
    u'Ü'   #  0x00dc -> LOWER HALF BLOCK
    u'Ý'   #  0x00dd -> LEFT HALF BLOCK
    u'Þ'   #  0x00de -> RIGHT HALF BLOCK
    u'ß'   #  0x00df -> UPPER HALF BLOCK

    u'à'   #  0x00e0 -> GREEK SMALL LETTER ALPHA
    u'á'     #  0x00e1 -> LATIN SMALL LETTER SHARP S
    u'â'   #  0x00e2 -> GREEK CAPITAL LETTER GAMMA
    u'ã'   #  0x00e3 -> GREEK SMALL LETTER PI
    u'ä'   #  0x00e4 -> GREEK CAPITAL LETTER SIGMA
    u'å'   #  0x00e5 -> GREEK SMALL LETTER SIGMA
    u'æ'     #  0x00e6 -> MICRO SIGN
    u'ç'   #  0x00e7 -> GREEK SMALL LETTER TAU
    u'è'   #  0x00e8 -> GREEK CAPITAL LETTER PHI
    u'é'   #  0x00e9 -> GREEK CAPITAL LETTER THETA
    u'ê'   #  0x00ea -> GREEK CAPITAL LETTER OMEGA
    u'ë'   #  0x00eb -> GREEK SMALL LETTER DELTA
    u'ì'   #  0x00ec -> INFINITY
    u'í'   #  0x00ed -> GREEK SMALL LETTER PHI
    u'î'   #  0x00ee -> GREEK SMALL LETTER EPSILON
    u'ï'   #  0x00ef -> INTERSECTION

    u'ð'   #  0x00f0 -> IDENTICAL TO
    u'ñ'     #  0x00f1 -> PLUS-MINUS SIGN
    u'ò'   #  0x00f2 -> GREATER-THAN OR EQUAL TO
    u'ó'   #  0x00f3 -> LESS-THAN OR EQUAL TO
    u'ô'   #  0x00f4 -> TOP HALF INTEGRAL
    u'õ'   #  0x00f5 -> BOTTOM HALF INTEGRAL
    u'ö'     #  0x00f6 -> DIVISION SIGN
    u'÷'   #  0x00f7 -> ALMOST EQUAL TO
    u'ø'     #  0x00f8 -> DEGREE SIGN
    u'ù'   #  0x00f9 -> BULLET OPERATOR
    u'ú'     #  0x00fa -> MIDDLE DOT
    u'û'   #  0x00fb -> SQUARE ROOT
    u'ü'   #  0x00fc -> SUPERSCRIPT LATIN SMALL LETTER N
    u'ý'     #  0x00fd -> SUPERSCRIPT TWO
    u'þ'   #  0x00fe -> BLACK SQUARE
    u'ÿ'     #  0x00ff -> NO-BREAK SPACE
)

decoding_table_A00 = (
    u'\x00'     #  0x0000 -> NULL
    u'\x01'     #  0x0001 -> START OF HEADING
    u'\x02'     #  0x0002 -> START OF TEXT
    u'\x03'     #  0x0003 -> END OF TEXT
    u'\x04'     #  0x0004 -> END OF TRANSMISSION
    u'\x05'     #  0x0005 -> ENQUIRY
    u'\x06'     #  0x0006 -> ACKNOWLEDGE
    u'\x07'     #  0x0007 -> BELL
    u'\x08'     #  0x0008 -> BACKSPACE
    u'\t'       #  0x0009 -> HORIZONTAL TABULATION
    u'\n'       #  0x000a -> LINE FEED
    u'\x0b'     #  0x000b -> VERTICAL TABULATION
    u'\x0c'     #  0x000c -> FORM FEED
    u'\r'       #  0x000d -> CARRIAGE RETURN
    u'\x0e'     #  0x000e -> SHIFT OUT
    u'\x0f'     #  0x000f -> SHIFT IN

    u'\x10'     #  0x0000 -> NULL
    u'\x11'     #  0x0001 -> START OF HEADING
    u'\x12'     #  0x0002 -> START OF TEXT
    u'\x13'     #  0x0003 -> END OF TEXT
    u'\x14'     #  0x0004 -> END OF TRANSMISSION
    u'\x15'     #  0x0005 -> ENQUIRY
    u'\x16'     #  0x0006 -> ACKNOWLEDGE
    u'\x17'     #  0x0007 -> BELL
    u'\x18'     #  0x0008 -> BACKSPACE
    u'\x19'     #  0x0009 -> HORIZONTAL TABULATION
    u'\x1a'     #  0x000a -> LINE FEED
    u'\x1b'     #  0x000b -> VERTICAL TABULATION
    u'\x1c'     #  0x000c -> FORM FEED
    u'\x1d'     #  0x000d -> CARRIAGE RETURN
    u'\x1e'     #  0x000e -> SHIFT OUT
    u'\x1f'     #  0x000f -> SHIFT IN

    u' '        #  0x0020 -> SPACE
    u'!'        #  0x0021 -> EXCLAMATION MARK
    u'"'        #  0x0022 -> QUOTATION MARK
    u'#'        #  0x0023 -> NUMBER SIGN
    u'$'        #  0x0024 -> DOLLAR SIGN
    u'%'        #  0x0025 -> PERCENT SIGN
    u'&'        #  0x0026 -> AMPERSAND
    u"'"        #  0x0027 -> APOSTROPHE
    u'('        #  0x0028 -> LEFT PARENTHESIS
    u')'        #  0x0029 -> RIGHT PARENTHESIS
    u'*'        #  0x002a -> ASTERISK
    u'+'        #  0x002b -> PLUS SIGN
    u','        #  0x002c -> COMMA
    u'-'        #  0x002d -> HYPHEN-MINUS
    u'.'        #  0x002e -> FULL STOP
    u'/'        #  0x002f -> SOLIDUS

    u'0'        #  0x0030 -> DIGIT ZERO
    u'1'        #  0x0031 -> DIGIT ONE
    u'2'        #  0x0032 -> DIGIT TWO
    u'3'        #  0x0033 -> DIGIT THREE
    u'4'        #  0x0034 -> DIGIT FOUR
    u'5'        #  0x0035 -> DIGIT FIVE
    u'6'        #  0x0036 -> DIGIT SIX
    u'7'        #  0x0037 -> DIGIT SEVEN
    u'8'        #  0x0038 -> DIGIT EIGHT
    u'9'        #  0x0039 -> DIGIT NINE
    u':'        #  0x003a -> COLON
    u';'        #  0x003b -> SEMICOLON
    u'<'        #  0x003c -> LESS-THAN SIGN
    u'='        #  0x003d -> EQUALS SIGN
    u'>'        #  0x003e -> GREATER-THAN SIGN
    u'?'        #  0x003f -> QUESTION MARK

    u'@'        #  0x0040 -> COMMERCIAL AT
    u'A'        #  0x0041 -> LATIN CAPITAL LETTER A
    u'B'        #  0x0042 -> LATIN CAPITAL LETTER B
    u'C'        #  0x0043 -> LATIN CAPITAL LETTER C
    u'D'        #  0x0044 -> LATIN CAPITAL LETTER D
    u'E'        #  0x0045 -> LATIN CAPITAL LETTER E
    u'F'        #  0x0046 -> LATIN CAPITAL LETTER F
    u'G'        #  0x0047 -> LATIN CAPITAL LETTER G
    u'H'        #  0x0048 -> LATIN CAPITAL LETTER H
    u'I'        #  0x0049 -> LATIN CAPITAL LETTER I
    u'J'        #  0x004a -> LATIN CAPITAL LETTER J
    u'K'        #  0x004b -> LATIN CAPITAL LETTER K
    u'L'        #  0x004c -> LATIN CAPITAL LETTER L
    u'M'        #  0x004d -> LATIN CAPITAL LETTER M
    u'N'        #  0x004e -> LATIN CAPITAL LETTER N
    u'O'        #  0x004f -> LATIN CAPITAL LETTER O

    u'P'        #  0x0050 -> LATIN CAPITAL LETTER P
    u'Q'        #  0x0051 -> LATIN CAPITAL LETTER Q
    u'R'        #  0x0052 -> LATIN CAPITAL LETTER R
    u'S'        #  0x0053 -> LATIN CAPITAL LETTER S
    u'T'        #  0x0054 -> LATIN CAPITAL LETTER T
    u'U'        #  0x0055 -> LATIN CAPITAL LETTER U
    u'V'        #  0x0056 -> LATIN CAPITAL LETTER V
    u'W'        #  0x0057 -> LATIN CAPITAL LETTER W
    u'X'        #  0x0058 -> LATIN CAPITAL LETTER X
    u'Y'        #  0x0059 -> LATIN CAPITAL LETTER Y
    u'Z'        #  0x005a -> LATIN CAPITAL LETTER Z
    u'['        #  0x005b -> LEFT SQUARE BRACKET
    u'¥'     #  0x00a5 -> LATIN CAPITAL LETTER N WITH TILDE
#    u'\\'       #  0x005c -> REVERSE SOLIDUS
    u']'        #  0x005d -> RIGHT SQUARE BRACKET
    u'^'        #  0x005e -> CIRCUMFLEX ACCENT
    u'_'        #  0x005f -> LOW LINE

    u'`'        #  0x0060 -> GRAVE ACCENT
    u'a'        #  0x0061 -> LATIN SMALL LETTER A
    u'b'        #  0x0062 -> LATIN SMALL LETTER B
    u'c'        #  0x0063 -> LATIN SMALL LETTER C
    u'd'        #  0x0064 -> LATIN SMALL LETTER D
    u'e'        #  0x0065 -> LATIN SMALL LETTER E
    u'f'        #  0x0066 -> LATIN SMALL LETTER F
    u'g'        #  0x0067 -> LATIN SMALL LETTER G
    u'h'        #  0x0068 -> LATIN SMALL LETTER H
    u'i'        #  0x0069 -> LATIN SMALL LETTER I
    u'j'        #  0x006a -> LATIN SMALL LETTER J
    u'k'        #  0x006b -> LATIN SMALL LETTER K
    u'l'        #  0x006c -> LATIN SMALL LETTER L
    u'm'        #  0x006d -> LATIN SMALL LETTER M
    u'n'        #  0x006e -> LATIN SMALL LETTER N
    u'o'        #  0x006f -> LATIN SMALL LETTER O

    u'p'        #  0x0070 -> LATIN SMALL LETTER P
    u'q'        #  0x0071 -> LATIN SMALL LETTER Q
    u'r'        #  0x0072 -> LATIN SMALL LETTER R
    u's'        #  0x0073 -> LATIN SMALL LETTER S
    u't'        #  0x0074 -> LATIN SMALL LETTER T
    u'u'        #  0x0075 -> LATIN SMALL LETTER U
    u'v'        #  0x0076 -> LATIN SMALL LETTER V
    u'w'        #  0x0077 -> LATIN SMALL LETTER W
    u'x'        #  0x0078 -> LATIN SMALL LETTER X
    u'y'        #  0x0079 -> LATIN SMALL LETTER Y
    u'z'        #  0x007a -> LATIN SMALL LETTER Z
    u'{'        #  0x007b -> LEFT CURLY BRACKET
    u'|'        #  0x007c -> VERTICAL LINE
    u'}'        #  0x007d -> RIGHT CURLY BRACKET
    u'→'        #  0x007e -> TILDE
    u'←'        # 
#    u'~'        #  0x007e -> TILDE
#    u'⌂'        # 

#unused/no characters
    u' '    #  0x0080 -> LATIN CAPITAL LETTER C WITH CEDILLA
    u' '     #  0x0081 -> LATIN SMALL LETTER U WITH DIAERESIS
    u' '     #  0x0082 -> LATIN SMALL LETTER E WITH ACUTE
    u' '     #  0x0083 -> LATIN SMALL LETTER A WITH CIRCUMFLEX
    u' '     #  0x0084 -> LATIN SMALL LETTER A WITH DIAERESIS
    u' '     #  0x0085 -> LATIN SMALL LETTER A WITH GRAVE
    u' '     #  0x0086 -> LATIN SMALL LETTER A WITH RING ABOVE
    u' '     #  0x0087 -> LATIN SMALL LETTER C WITH CEDILLA
    u' '     #  0x0088 -> LATIN SMALL LETTER E WITH CIRCUMFLEX
    u' '     #  0x0089 -> LATIN SMALL LETTER E WITH DIAERESIS
    u' '     #  0x008a -> LATIN SMALL LETTER E WITH GRAVE
    u' '     #  0x008b -> LATIN SMALL LETTER I WITH DIAERESIS
    u' '     #  0x008c -> LATIN SMALL LETTER I WITH CIRCUMFLEX
    u' '     #  0x008d -> LATIN SMALL LETTER I WITH GRAVE
    u' '     #  0x008e -> LATIN CAPITAL LETTER A WITH DIAERESIS
    u' '     #  0x008f -> LATIN CAPITAL LETTER A WITH RING ABOVE

#unused/no characters
    u' '     #  0x0090 -> LATIN CAPITAL LETTER E WITH ACUTE
    u' '     #  0x0091 -> LATIN SMALL LIGATURE AE
    u' '     #  0x0092 -> LATIN CAPITAL LIGATURE AE
    u' '     #  0x0093 -> LATIN SMALL LETTER O WITH CIRCUMFLEX
    u' '     #  0x0094 -> LATIN SMALL LETTER O WITH DIAERESIS
    u' '     #  0x0095 -> LATIN SMALL LETTER O WITH GRAVE
    u' '     #  0x0096 -> LATIN SMALL LETTER U WITH CIRCUMFLEX
    u' '     #  0x0097 -> LATIN SMALL LETTER U WITH GRAVE
    u' '     #  0x0098 ->  BELL
    u' '     #  0x0099 -> LATIN CAPITAL LETTER O WITH DIAERESIS
    u' '     #  0x009a -> LATIN CAPITAL LETTER U WITH DIAERESIS
    u' '     #  0x009b -> CENT SIGN
    u' '     #  0x009c -> POUND SIGN
    u' '     #  0x009d -> YEN SIGN
    u' '   #  0x009e -> PESETA SIGN
    u' '   #  0x009f -> LATIN SMALL LETTER F WITH HOOK


#japanese letters
    u'?'     #  0x00a0 -> Pause sign
    u'?'     #  0x00a1 -> LATIN SMALL LETTER I WITH ACUTE
    u'?'     #  0x00a2 -> LATIN SMALL LETTER O WITH ACUTE
    u'?'     #  0x00a3 -> LATIN SMALL LETTER U WITH ACUTE
    u'?'     #  0x00a4 -> LATIN SMALL LETTER N WITH TILDE
    u'?'     #  0x00a5 -> LATIN CAPITAL LETTER N WITH TILDE
    u'?'     #  0x00a6 -> FEMININE ORDINAL INDICATOR
    u'?'     #  0x00a7 -> MASCULINE ORDINAL INDICATOR
    u'?'     #  0x00a8 -> INVERTED QUESTION MARK
    u'?'   #  0x00a9 -> REVERSED NOT SIGN
    u'?'     #  0x00aa -> NOT SIGN
    u'?'     #  0x00ab -> VULGAR FRACTION ONE HALF
    u'?'     #  0x00ac -> VULGAR FRACTION ONE QUARTER
    u'?'     #  0x00ad -> INVERTED EXCLAMATION MARK
    u'?'     #  0x00ae -> LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'?'     #  0x00af -> RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK

#japanese letters
    u'?'   #  0x00b0 -> LIGHT SHADE
    u'?'   #  0x00b1 -> MEDIUM SHADE
    u'?'   #  0x00b2 -> DARK SHADE
    u'?'   #  0x00b3 -> BOX DRAWINGS LIGHT VERTICAL
    u'?'   #  0x00b4 -> BOX DRAWINGS LIGHT VERTICAL AND LEFT
    u'?'   #  0x00b5 -> BOX DRAWINGS VERTICAL SINGLE AND LEFT DOUBLE
    u'?'   #  0x00b6 -> BOX DRAWINGS VERTICAL DOUBLE AND LEFT SINGLE
    u'?'   #  0x00b7 -> BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE
    u'?'   #  0x00b8 -> BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE
    u'?'   #  0x00b9 -> BOX DRAWINGS DOUBLE VERTICAL AND LEFT
    u'?'   #  0x00ba -> BOX DRAWINGS DOUBLE VERTICAL
    u'?'   #  0x00bb -> BOX DRAWINGS DOUBLE DOWN AND LEFT
    u'?'   #  0x00bc -> BOX DRAWINGS DOUBLE UP AND LEFT
    u'?'   #  0x00bd -> BOX DRAWINGS UP DOUBLE AND LEFT SINGLE
    u'?'   #  0x00be -> BOX DRAWINGS UP SINGLE AND LEFT DOUBLE
    u'?'   #  0x00bf -> BOX DRAWINGS LIGHT DOWN AND LEFT

#japanese letters
    u'?'   #  0x00c0 -> BOX DRAWINGS LIGHT UP AND RIGHT
    u'?'   #  0x00c1 -> BOX DRAWINGS LIGHT UP AND HORIZONTAL
    u'?'   #  0x00c2 -> BOX DRAWINGS LIGHT DOWN AND HORIZONTAL
    u'?'   #  0x00c3 -> BOX DRAWINGS LIGHT VERTICAL AND RIGHT
    u'?'   #  0x00c4 -> BOX DRAWINGS LIGHT HORIZONTAL
    u'?'   #  0x00c5 -> BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL
    u'?'   #  0x00c6 -> BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE
    u'?'   #  0x00c7 -> BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE
    u'?'   #  0x00c8 -> BOX DRAWINGS DOUBLE UP AND RIGHT
    u'?'   #  0x00c9 -> BOX DRAWINGS DOUBLE DOWN AND RIGHT
    u'?'   #  0x00ca -> BOX DRAWINGS DOUBLE UP AND HORIZONTAL
    u'?'   #  0x00cb -> BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL
    u'?'   #  0x00cc -> BOX DRAWINGS DOUBLE VERTICAL AND RIGHT
    u'?'   #  0x00cd -> BOX DRAWINGS DOUBLE HORIZONTAL
    u'?'   #  0x00ce -> BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL
    u'?'   #  0x00cf -> BOX DRAWINGS UP SINGLE AND HORIZONTAL DOUBLE

#japanese letters
    u'?'   #  0x00d0 -> BOX DRAWINGS UP DOUBLE AND HORIZONTAL SINGLE
    u'?'   #  0x00d1 -> BOX DRAWINGS DOWN SINGLE AND HORIZONTAL DOUBLE
    u'?'   #  0x00d2 -> BOX DRAWINGS DOWN DOUBLE AND HORIZONTAL SINGLE
    u'?'   #  0x00d3 -> BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE
    u'?'   #  0x00d4 -> BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE
    u'?'   #  0x00d5 -> BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE
    u'?'   #  0x00d6 -> BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE
    u'?'   #  0x00d7 -> BOX DRAWINGS VERTICAL DOUBLE AND HORIZONTAL SINGLE
    u'?'   #  0x00d8 -> BOX DRAWINGS VERTICAL SINGLE AND HORIZONTAL DOUBLE
    u'?'   #  0x00d9 -> BOX DRAWINGS LIGHT UP AND LEFT
    u'?'   #  0x00da -> BOX DRAWINGS LIGHT DOWN AND RIGHT
    u'?'   #  0x00db -> FULL BLOCK
    u'?'   #  0x00dc -> LOWER HALF BLOCK
    u'?'   #  0x00dd -> LEFT HALF BLOCK
    u'?'   #  0x00de -> RIGHT HALF BLOCK
    u'?'   #  0x00df -> UPPER HALF BLOCK

    u'α'   #  0x00e0 -> GREEK SMALL LETTER ALPHA
    u'ä'     #  0x00e1 -> LATIN SMALL LETTER SHARP S
    u'β'   #  0x00e2 -> GREEK CAPITAL LETTER GAMMA
    u'ε'   #  0x00e3 -> GREEK SMALL LETTER PI
    u'μ'   #  0x00e4 -> GREEK CAPITAL LETTER SIGMA
    u'σ'   #  0x00e5 -> GREEK SMALL LETTER SIGMA
    u'ρ'     #  0x00e6 -> MICRO SIGN
    u'q'   #  0x00e7 -> GREEK SMALL LETTER TAU
    u'√'   #  0x00e8 -> GREEK CAPITAL LETTER PHI
    u'⁻'   #  0x00e9 -> ⁻ⁱ
    u'i'   #  0x00ea -> GREEK CAPITAL LETTER OMEGA
    u'𝄪'   #  0x00eb -> GREEK SMALL LETTER DELTA
    u'¢'   #  0x00ec -> INFINITY
    u'£'   #  0x00ed -> GREEK SMALL LETTER PHI
    u'ā'   #  0x00ee -> GREEK SMALL LETTER EPSILON
    u'ö'   #  0x00ef -> INTERSECTION

    u'p'   #  0x00f0 -> IDENTICAL TO
    u'q'     #  0x00f1 -> PLUS-MINUS SIGN
    u'θ'   #  0x00f2 -> GREATER-THAN OR EQUAL TO
    u'∞'   #  0x00f3 -> LESS-THAN OR EQUAL TO
    u'Ω'   #  0x00f4 -> TOP HALF INTEGRAL
    u'ü'   #  0x00f5 -> BOTTOM HALF INTEGRAL
    u'Σ'     #  0x00f6 -> DIVISION SIGN
    u'π'   #  0x00f7 -> ALMOST EQUAL TO
    u'χ'     #  0x00f8 -> DEGREE SIGN
    u'?'   #  0x00f9 -> BULLET OPERATOR
    u'?'     #  0x00fa -> MIDDLE DOT
    u'?'   #  0x00fb -> SQUARE ROOT
    u'?'   #  0x00fc -> SUPERSCRIPT LATIN SMALL LETTER N
    u'÷'     #  0x00fd -> SUPERSCRIPT TWO
    u' '   #  0x00fe -> BLACK SQUARE
    u'█'     #  0x00ff -> NO-BREAK SPACE
)

### Encoding Map

encoding_map_A00 = {
    0x0: 0x0,
    0x1: 0x1,
    0x2: 0x2,
    0x3: 0x3,
    0x4: 0x4,
    0x5: 0x5,
    0x6: 0x6,
    0x7: 0x7,
    0x8: 0x8,
    0x9: 0x9,
    0xa: 0xa,
    0xb: 0xb,
    0xc: 0xc,
    0xd: 0xd,
    0xe: 0xe,
    0xf: 0xf,
    0x10: 0x10,
    0x11: 0x11,
    0x12: 0x12,
    0x13: 0x13,
    0x14: 0x14,
    0x15: 0x15,
    0x16: 0x16,
    0x17: 0x17,
    0x18: 0x18,
    0x19: 0x19,
    0x1a: 0x1a,
    0x1b: 0x1b,
    0x1c: 0x1c,
    0x1d: 0x1d,
    0x1e: 0x1e,
    0x1f: 0x1f,
    0x20: 0x20,
    0x21: 0x21,
    0x22: 0x22,
    0x23: 0x23,
    0x24: 0x24,
    0x25: 0x25,
    0x26: 0x26,
    0x27: 0x27,
    0x28: 0x28,
    0x29: 0x29,
    0x2a: 0x2a,
    0x2b: 0x2b,
    0x2c: 0x2c,
    0x2d: 0x2d,
    0x2e: 0x2e,
    0x2f: 0x2f,
    0x30: 0x30,
    0x31: 0x31,
    0x32: 0x32,
    0x33: 0x33,
    0x34: 0x34,
    0x35: 0x35,
    0x36: 0x36,
    0x37: 0x37,
    0x38: 0x38,
    0x39: 0x39,
    0x3a: 0x3a,
    0x3b: 0x3b,
    0x3c: 0x3c,
    0x3d: 0x3d,
    0x3e: 0x3e,
    0x3f: 0x3f,
    0x40: 0x40,
    0x41: 0x41,
    0x42: 0x42,
    0x43: 0x43,
    0x44: 0x44,
    0x45: 0x45,
    0x46: 0x46,
    0x47: 0x47,
    0x48: 0x48,
    0x49: 0x49,
    0x4a: 0x4a,
    0x4b: 0x4b,
    0x4c: 0x4c,
    0x4d: 0x4d,
    0x4e: 0x4e,
    0x4f: 0x4f,
    0x50: 0x50,
    0x51: 0x51,
    0x52: 0x52,
    0x53: 0x53,
    0x54: 0x54,
    0x55: 0x55,
    0x56: 0x56,
    0x57: 0x57,
    0x58: 0x58,
    0x59: 0x59,
    0x5a: 0x5a,
    0x5b: 0x5b,
    0xa5: 0x5c,
    0x5d: 0x5d,
    0x5e: 0x5e,
    0x5f: 0x5f,
    0x60: 0x60,
    0x61: 0x61,
    0x62: 0x62,
    0x63: 0x63,
    0x64: 0x64,
    0x65: 0x65,
    0x66: 0x66,
    0x67: 0x67,
    0x68: 0x68,
    0x69: 0x69,
    0x6a: 0x6a,
    0x6b: 0x6b,
    0x6c: 0x6c,
    0x6d: 0x6d,
    0x6e: 0x6e,
    0x6f: 0x6f,
    0x70: 0x70,
    0x71: 0x71,
    0x72: 0x72,
    0x73: 0x73,
    0x74: 0x74,
    0x75: 0x75,
    0x76: 0x76,
    0x77: 0x77,
    0x78: 0x78,
    0x79: 0x79,
    0x7a: 0x7a,
    0x7b: 0x7b,
    0x7c: 0x7c,
    0x7d: 0x7d,
    0x2192: 0x7e,
    0x2190: 0x7f,
    0x3b1: 0xe0,
    0xc4: 0xe1,
    0xe4: 0xe1,
    0xdf: 0xe2,
    0x3b2: 0xe2,
    0x3b5: 0xe3,
    0x3bc: 0xe4,
    0x3c3: 0xe5,
    0x3c1: 0xe6,
    0x70: 0xf0,
    0x71: 0xe7,
    0x71: 0xf1,
    0xa2: 0xec,
    0xa3: 0xed,
    0xf6: 0xef,
    0xd6: 0xef,
    0xf7: 0xfd,
    0xdc: 0xf5,
    0xfc: 0xf5,
    0x101: 0xee,
    0x3a3: 0xf6,
    0x3a9: 0xf4,
    0x3b8: 0xf2,
    0x3c0: 0xf7,
    0x3c7: 0xf8,
    0x207b: 0xe9,
    0x221a: 0xe8,
    0x221e: 0xf3,
    0x2588: 0xff,
    0x1d12a: 0xeb,
}

encoding_map_A02 = {
    0x0: 0x0,
    0x1: 0x1,
    0x2: 0x2,
    0x3: 0x3,
    0x4: 0x4,
    0x5: 0x5,
    0x6: 0x6,
    0x7: 0x7,
    0x8: 0x8,
    0x9: 0x9,
    0xa: 0xa,
    0xb: 0xb,
    0xc: 0xc,
    0xd: 0xd,
    0xe: 0xe,
    0xf: 0xf,
    0x25b6: 0x10,
    0x25c0: 0x11,
    0x201c: 0x12,
    0x201d: 0x13,
    0x23eb: 0x14,
    0x23ec: 0x15,
    0x25cf: 0x16,
    0x21b2: 0x17,
    0x2191: 0x18,
    0x2193: 0x19,
    0x2190: 0x1a,
    0x2192: 0x1b,
    0x2264: 0x1c,
    0x2265: 0x1d,
    0x25b2: 0x1e,
    0x25bc: 0x1f,
    0x20: 0x20,
    0x21: 0x21,
    0x22: 0x22,
    0x23: 0x23,
    0x24: 0x24,
    0x25: 0x25,
    0x26: 0x26,
    0x27: 0x27,
    0x28: 0x28,
    0x29: 0x29,
    0x2a: 0x2a,
    0x2b: 0x2b,
    0x2c: 0x2c,
    0x2d: 0x2d,
    0x2e: 0x2e,
    0x2f: 0x2f,
    0x30: 0x30,
    0x31: 0x31,
    0x32: 0x32,
    0x33: 0x33,
    0x34: 0x34,
    0x35: 0x35,
    0x36: 0x36,
    0x37: 0x37,
    0x38: 0x38,
    0x39: 0x39,
    0x3a: 0x3a,
    0x3b: 0x3b,
    0x3c: 0x3c,
    0x3d: 0x3d,
    0x3e: 0x3e,
    0x3f: 0x3f,
    0x40: 0x40,
    0x41: 0x41,
    0x42: 0x42,
    0x43: 0x43,
    0x44: 0x44,
    0x45: 0x45,
    0x46: 0x46,
    0x47: 0x47,
    0x48: 0x48,
    0x49: 0x49,
    0x4a: 0x4a,
    0x4b: 0x4b,
    0x4c: 0x4c,
    0x4d: 0x4d,
    0x4e: 0x4e,
    0x4f: 0x4f,
    0x50: 0x50,
    0x51: 0x51,
    0x52: 0x52,
    0x53: 0x53,
    0x54: 0x54,
    0x55: 0x55,
    0x56: 0x56,
    0x57: 0x57,
    0x58: 0x58,
    0x59: 0x59,
    0x5a: 0x5a,
    0x5b: 0x5b,
    0x5c: 0x5c,
    0x5d: 0x5d,
    0x5e: 0x5e,
    0x5f: 0x5f,
    0x60: 0x60,
    0x61: 0x61,
    0x62: 0x62,
    0x63: 0x63,
    0x64: 0x64,
    0x65: 0x65,
    0x66: 0x66,
    0x67: 0x67,
    0x68: 0x68,
    0x69: 0x69,
    0x6a: 0x6a,
    0x6b: 0x6b,
    0x6c: 0x6c,
    0x6d: 0x6d,
    0x6e: 0x6e,
    0x6f: 0x6f,
    0x70: 0x70,
    0x71: 0x71,
    0x72: 0x72,
    0x73: 0x73,
    0x74: 0x74,
    0x75: 0x75,
    0x76: 0x76,
    0x77: 0x77,
    0x78: 0x78,
    0x79: 0x79,
    0x7a: 0x7a,
    0x7b: 0x7b,
    0x7c: 0x7c,
    0x7d: 0x7d,
    0x7e: 0x7e,
    0x2302: 0x7f,
    0x411: 0x80,
    0x414: 0x81,
    0x416: 0x82,
    0x417: 0x83,
    0x418: 0x84,
    0x419: 0x85,
    0x41b: 0x86,
    0x41f: 0x87,
    0x423: 0x88,
    0x426: 0x89,
    0x427: 0x8a,
    0x428: 0x8b,
    0x429: 0x8c,
    0x42a: 0x8d,
    0x42c: 0x8e,
    0x42d: 0x8f,
    0x3b1: 0x90,
    0x266a: 0x91,
    0x393: 0x92,
    0x3c0: 0x93,
    0x3a3: 0x94,
    0x3c3: 0x95,
    0x266b: 0x96,
    0x3c4: 0x97,
    0x1f514: 0x98,
    0x398: 0x99,
    0x3a9: 0x9a,
    0x3b4: 0x9b,
    0x221e: 0x9c,
    0x2665: 0x9d,
    0x3b5: 0x9e,
    0x2229: 0x9f,
    0x275a: 0xa0,
    0xa1: 0xa1,
    0xa2: 0xa2,
    0xa3: 0xa3,
    0xa4: 0xa4,
    0xa5: 0xa5,
    0xa6: 0xa6,
    0xa7: 0xa7,
    0x2a0d: 0xa8,
    0xa9: 0xa9,
    0xaa: 0xaa,
    0xab: 0xab,
    0x42e: 0xac,
    0x42f: 0xad,
    0xae: 0xae,
    0x2018: 0xaf,
    0xb0: 0xb0,
    0xb1: 0xb1,
    0xb2: 0xb2,
    0xb3: 0xb3,
    0x20a7: 0xb4,
    0x3bc: 0xb5,
    0xb6: 0xb6,
    0x22c5: 0xb7,
    0x3c9: 0xb8,
    0xb9: 0xb9,
    0xba: 0xba,
    0xbb: 0xbb,
    0xbc: 0xbc,
    0xbd: 0xbd,
    0xbe: 0xbe,
    0xbf: 0xbf,
    0xc0: 0xc0,
    0xc1: 0xc1,
    0xc2: 0xc2,
    0xc3: 0xc3,
    0xc4: 0xc4,
    0xc5: 0xc5,
    0xc6: 0xc6,
    0xc7: 0xc7,
    0xc8: 0xc8,
    0xc9: 0xc9,
    0xca: 0xca,
    0xcb: 0xcb,
    0xcc: 0xcc,
    0xcd: 0xcd,
    0xce: 0xce,
    0xcf: 0xcf,
    0xd0: 0xd0,
    0xd1: 0xd1,
    0xd2: 0xd2,
    0xd3: 0xd3,
    0xd4: 0xd4,
    0xd5: 0xd5,
    0xd6: 0xd6,
    0xd7: 0xd7,
    0x3a6: 0xd8,
    0xd9: 0xd9,
    0xda: 0xda,
    0xdb: 0xdb,
    0xdc: 0xdc,
    0xdd: 0xdd,
    0xde: 0xde,
    0xdf: 0xdf,
    0xe0: 0xe0,
    0xe1: 0xe1,
    0xe2: 0xe2,
    0xe3: 0xe3,
    0xe4: 0xe4,
    0xe5: 0xe5,
    0xe6: 0xe6,
    0xe7: 0xe7,
    0xe8: 0xe8,
    0xe9: 0xe9,
    0xea: 0xea,
    0xeb: 0xeb,
    0xec: 0xec,
    0xed: 0xed,
    0xee: 0xee,
    0xef: 0xef,
    0xf0: 0xf0,
    0xf1: 0xf1,
    0xf2: 0xf2,
    0xf3: 0xf3,
    0xf4: 0xf4,
    0xf5: 0xf5,
    0xf6: 0xf6,
    0xf7: 0xf7,
    0xf8: 0xf8,
    0xf9: 0xf9,
    0xfa: 0xfa,
    0xfb: 0xfb,
    0xfc: 0xfc,
    0xfd: 0xfd,
    0xfe: 0xfe,
    0xff: 0xff
}

if __name__ == '__main__':
    for i in range(256):
        print "0x%x: 0x%x," % (ord(decoding_table_A00[i]),i)
