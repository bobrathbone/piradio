#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import posixpath
import copy
import time
import math
import datetime
import string
import traceback
import config
import radio_class
import pifacecad
from time import strftime
from glob import glob
from radio_api import RadioApi

radio_api = RadioApi()
lcd = None
radio = None
rss = None
current_menu = None
current_playmenu = None
log = None


status_symbols = None

CLOCK_SYMBOL = 5

def set_lcd(menu_lcd):
    global lcd
    global status_symbols
    lcd = menu_lcd
    status_symbols = {
        'stop': lcd.STOP_SYMBOL_INDEX,
        'play': lcd.PLAY_SYMBOL_INDEX,
        'pause': lcd.PAUSE_SYMBOL_INDEX
    }

def set_radio(menu_radio):
    global radio
    radio = menu_radio

def set_rss(menu_rss):
    global rss
    rss = menu_rss
    
def submenu(menu):
    global current_menu
    current_menu = menu
    current_menu.activate()

def heartbeat():
    current_menu.heartbeat()

def _(string):
    return string

# Execute system command
def exec_cmd(cmd):
    p = os.popen(cmd)
    result = p.readline().rstrip('\n')
    return result

if hasattr(os, 'sync'):
    sync = os.sync
else:
    import ctypes
    libc = ctypes.CDLL("libc.so.6")
    def sync():
        libc.sync()

def addCallbacks(radio):
    callback_list = []
    for key in radio_class.RadioState.callback_init:
        callback = getattr(menukeys,key+'_changed_callback')
        radio.addUpdateCallback(key, callback)
        callback_list.append(callback)

    for callback in callback_list:
        callback()

ir_keys = [
    'home',
    'back',
    'clear',
    'menu',
    'tv',
    'radio',
    'power',
    'up',
    'down',
    'left',
    'right',
    'enter',
    'ok',
    'volumeup',
    'volumedown',
    'mute',
    'channelup',
    'channeldown',
    'previous',
    'stop',
    'record',
    'previoussong',
    'nextsong',
    'pause',
    'play',
    'rewind',
    'fastforward',
    'text',
    'subtitle',
    'key0',
    'key1',
    'key2',
    'key3',
    'key4',
    'key5',
    'key6',
    'key7',
    'key8',
    'key9'
]

buttons = [
    'button1',
    'button2',
    'button3',
    'button4',
    'button5',
    'leftrightbutton',
    'leftswitch',
    'rightswitch'
]

class menukeys_class:
    def button(self,button_type,args):
        log.message("button({0})".format(button_type),log.DEBUG)
        current_menu.button(button_type,args)

    def button_off(self,button_type,args):
        log.message("button({0})".format(button_type),log.DEBUG)
        current_menu.button_off(button_type,args)

    def ir_key(self,event):
        key = event.ir_code
        log.message("ir_key({0})".format(key),log.DEBUG)
        menu = current_menu
        log.message('Got IR Key: ' + key, log.DEBUG)
        if key < '0' or key > '9':
            method = getattr(menu,key,None)
        else:
            method = getattr(menu,'key'+key,None)
        if method is not None:
            method(event)
        else:
            method = getattr(menu,'ir_key',None)
            if method is not None:
                method(event)

    # IR remote control
    def changed_callback(self,cb_type,args):
        log.message("changed_callback({0})".format(cb_type),log.DEBUG)
        getattr(current_menu,cb_type + '_changed_callback')()

    @classmethod
    def add_changed_callback(cls, name):
        print ("adding changed callback: "+name)
        callback = getattr(cls,'changed_callback')
        method = new_changed_callback(callback, key)

        escaped_name = name.replace(" ", "_") + '_changed_callback'
        setattr(cls, escaped_name, method)

    @classmethod
    def add_button_callbacks(cls, name):
        print "adding button callback: "+name
        callback = getattr(cls,'button')
        off_callback = getattr(cls,'button_off')
        method = new_changed_callback(callback, key)
        off_method = new_changed_callback(off_callback, key)

        escaped_name = name.replace(" ", "_")
        setattr(cls, escaped_name, method)
        setattr(cls, escaped_name + '_off', off_method)


# top level functions:
def new_changed_callback(wrapper, name):
    def decorator(self, *args):
        return wrapper(self, name, args)
    return decorator

for key in radio_class.RadioState.callback_init:
    menukeys_class.add_changed_callback(key)

for key in buttons:
    menukeys_class.add_button_callbacks(key)

menukeys = menukeys_class()

def register_buttons(listener):
    for value in range(8):
        key = buttons[value]
        method = getattr(menukeys,key)
        listener.register(value,
                          pifacecad.IODIR_ON,
                          method)
        
        method = getattr(menukeys,key+'_off')
        listener.register(value,
                          pifacecad.IODIR_OFF,
                          method)

def register_irkeys(listener):
    method = getattr(menukeys,'ir_key')
    for key in ir_keys:
        listener.register(key,method)

    for key in range(10):
        listener.register(str(key),method)

class menu(object):
    changed = False
    ignore_button = None
    ignore_until = 0
    update = 0
    time_index = 0
    time_formats = [
        "{0:c}%H.%M".format(CLOCK_SYMBOL),
        "{0:c}%H %M".format(CLOCK_SYMBOL),
        "{0:c}%H:%M".format(CLOCK_SYMBOL),
        "{0:c}%H %M".format(CLOCK_SYMBOL),
        "{0:c}%H.%M".format(CLOCK_SYMBOL),
        "{0:c}%H %M".format(CLOCK_SYMBOL),
        "{0:c}%H:%M".format(CLOCK_SYMBOL),
        "{0:c}%H %M".format(CLOCK_SYMBOL),
        "{0:c}%H.%M".format(CLOCK_SYMBOL),
        "{0:c}%H %M".format(CLOCK_SYMBOL),
        "%d.%m ",
        "%d %m.",
        "%d.%m.",
        "%d.%m.",
        "%d %m ",
        "%d %m.",
        "%d.%m ",
        "%d.%m.",
        "%d %m ",
    ]


    def __init__(self):
        self.changed = False

    def activate(self):
        self.update_radio()
        self.displayMode()

    def get_parent_menu(self):
        return self

    def parent_menu(self):
        submenu(self.get_parent_menu())

    def update_radio(self):
        self.changed = True
        return

    def displayMode(self):
        self.display_time(10,0)
        lcd.lock()
        lcd.line(0,1, "Unknown menu")
        lcd.unlock()

    def heartbeat(self):
        if False:
            current_time = time.time()
            if self.update >= 0 \
               and self.update <= current_time:
                self.displayMode()
                self.update = -1

    def status_changed_callback(self):
        return
    def database_changed_callback(self):
        return
    def update_changed_callback(self):
        return
    def stored_playlist_changed_callback(self):
        return
    def playlist_changed_callback(self):
        return
    def player_changed_callback(self):
        lcd.lock()
        status = radio.getStatusField('state')
        if status:
            lcd.putSymbol(0,0,status_symbols[status])
        lcd.unlock()
        return
    def mixer_changed_callback(self):
        return
    def output_changed_callback(self):
        return
    def options_changed_callback(self):
        return

    def button(self,button_type,args):
        getattr(self,button_type)(args[0])

    def button_off(self,button_type,args):
        getattr(self,button_type + '_off')(args[0])

    def enterbutton(self,event):
        return

    def menubutton(self,event):
        self.parent_menu()
        return

    def reactivate_playmenu(self):
        submenu(date_play_menu())

    def gotoradio(self,node):
        radiopath = config.libget('Radio','place_uri')
        radiotype = config.libget('Radio','place_type')
        if not radiopath or not radiotype: return
        try:
            if radiotype == 'directory':
                submenu(path_menu(radiopath,'radio'))
            elif radiotype == 'playlist':
                submenu(playlist_menu(radiopath,'radio'))
        except Exception as e:
            log.message('top_menu.gotoradio: Exception: '+unicode(e),
                        log.ERROR)
            log.message(string.join(traceback.format_stack()),log.ERROR)
        

    # LCD buttons
    # we must ignore the following interrupt if we 
    def button1(self,event):
        if self.ignore_button == lcd.BUTTON1:
            if time.time() < self.ignore_time:
                self.ignore_time = time.time()+0.1
                return
            else: self.ignore_button = None
        sleeptime = 0.4
        volchange = True
        while volchange:
            if lcd.buttonPressed(lcd.BUTTON2):
                self.mute(event)
                volchange = False
                self.ignore_time = time.time()+0.2
                self.ignore_button = lcd.BUTTON2

                while lcd.buttonPressed(lcd.BUTTON1) \
                      or lcd.buttonPressed(lcd.BUTTON2):
                    time.sleep(0.1)
                    self.ignore_time = time.time()+0.2
            else:
                volume = self.decrease_volume(event)
                volchange = lcd.buttonPressed(lcd.BUTTON1) 
                
                if volume >= 100:
                    volchange = False
                    time.sleep(sleeptime)
                    sleeptime = 0.1
        return

    def button2(self,event):
        if self.ignore_button == lcd.BUTTON2:
            if time.time() < self.ignore_time:
                self.ignore_time = time.time()+0.1
                return
            else: self.ignore_button = None
        volchange = True
        sleeptime = 0.4
        while volchange:
            if lcd.buttonPressed(lcd.BUTTON1):
                self.mute(event)
                volchange = False
                self.ignore_time = time.time()+0.2
                self.ignore_button = lcd.BUTTON1

                while lcd.buttonPressed(lcd.BUTTON1) \
                      or lcd.buttonPressed(lcd.BUTTON2):
                    time.sleep(0.1)
                    self.ignore_time = time.time()+0.2
            else:
                volume = self.increase_volume(event)
                volchange = lcd.buttonPressed(lcd.BUTTON2) 
                
                if volume >= 100:
                    volchange = False
                    time.sleep(sleeptime)
                    sleeptime = 0.1
        return

    def button3(self,event):
        self.channel_down(event)
        return

    def button4(self,event):
        self.channel_up(event)
        return

    def button5(self,event):
        return

    def leftswitch(self,event):
        self.channel_down(event)
        return

    def rightswitch(self,event):
        self.channel_up(event)
        return

    def leftrightbutton(self,event):
        log.message("Processing left+right button", log.DEBUG)
        # Shutdown if menu button held for > 3 seconds
        MenuSwitch = True
        count = 30
        while MenuSwitch:
            time.sleep(0.1)
            MenuSwitch = lcd.buttonPressed(lcd.ENTER)
            lcd.backlight(True)
            count = count - 1
            if count < 0:
                submenu(shutdown_menu())
                MenuSwitch = False

        if not self.changed:
            self.menubutton(event)
        return
 

    def leftswitch_off(self,event):
        return

    def rightswitch_off(self,event):
        return
    
    def leftrightbutton_off(self,event):
        return

    def button1_off(self,event):
        return
        
    def button2_off(self,event):
        return

    def button3_off(self,event):
        return

    def button4_off(self,event):
        return

    def button5_off(self,event):
        return
 
    def update_radio(self):
        self.changed = True


    def home(self,event):
        return

    def back(self,event):
        return

    def clear(self,event):
        return

    def menu(self,event):
        self.menubutton(event)
        return

    def setup(self,event):
        submenu(options_menu())

    def tv(self,event):
        return

    def radio(self,event):
        self.gotoradio({})
        return

    def power(self,event):
        submenu(shutdown_question(self))
        return

    def up(self,event):
        self.parent_menu()
        return

    def down(self,event):
        self.parent_menu()
        return

    def left(self,event):
        self.channel_down(event)
        return

    def right(self,event):
        self.channel_up(event)
        return
    
    def enter(self,event):
        log.message("Enter",log.DEBUG)
        self.ok(event)

    def ok(self,event):
        log.message("OK",log.DEBUG)
        self.enterbutton(event)
        return

    def mute(self,event):
        if radio.muted():
            radio.unmute() 
            lcd.lock()
            self.display_volume(0,1)
            lcd.unlock()
        else:
            radio.mute()
            lcd.lock()
            lcd.line(0,1, "Mute")
            lcd.unlock()        
        self.update = 3

    def increase_volume(self,event):
        volume = radio.increaseVolume()
        lcd.lock()
        self.display_volume(0,1)
        lcd.unlock()
        self.update = 3
        return volume

    def volumeup(self,event):
        self.increase_volume(event)
        
    def decrease_volume(self,event):
        volume = radio.decreaseVolume()
        lcd.lock()
        self.display_volume(0,1)
        lcd.unlock()
        self.update = 3
        return volume

    def volumedown(self,event):
        self.decrease_volume(event)

    def channel_up(self,event):
        radio.channelUp()
        self.displayMode()

    def channel_down(self,event):
        radio.channelDown()
        self.displayMode()

    def previous(self,event):
        self.channel_down()
        return

    def stop(self,event):
        radio.doStop()
        return

    def record(self,event):
        return

    def previoussong(self,event):
        self.channel_down(event)
        return

    def nextsong(self,event):
        self.channel_up(event)
        return

    def pause(self,event):
        radio.doPause()
        return

    def play(self,event):
        radio.doPlay()
        return

    def rewind(self,event):
        return

    def fastforward(self,event):
        return

    def text(self,event):
        return

    def subtitle(self,event):
        return

    def key0(self,event):
        self.number_pressed(0)
    def key1(self,event):
        self.number_pressed(1)
    def key2(self,event):
        self.number_pressed(2)
    def key3(self,event):
        self.number_pressed(3)
    def key4(self,event):
        self.number_pressed(4)
    def key5(self,event):
        self.number_pressed(5)
    def key6(self,event):
        self.number_pressed(6)
    def key7(self,event):
        self.number_pressed(7)
    def key8(self,event):
        self.number_pressed(8)
    def key9(self,event):
        self.number_pressed(9)

    def number_pressed(self,number):
        return

    def formatfile(self,node):
        if (node['title']):
            fmt = u'{0} ({1})'
        else:
            msg = u""
            fmt = u'{1}'

        if (node['artist']):
            fmt2 = u'{0}'
        else:
            fmt2 = u''

        if (node['album']):
            if (len(fmt2)):
                fmt2 += u': {1}'
            else:
                fmt2 = u'{1}'

        if (node['track']):
            if (len(fmt2)):
                fmt2 += u': {2}'
            else:
                fmt2 = u'{2}'
        msg2 = fmt2.format(node['artist'],
                           node['album'],
                           node['track'])
        return fmt.format(node['title'],msg2)

    def format_entry(self,current_station):
        text = ''
        has_message = (('message' in current_station)
                       and len(current_station['message']))
        has_title = (('title' in current_station)
                       and len(current_station['title']))
        has_file = (('file' in current_station)
                       and len(current_station['file']))
        has_album = (('album' in current_station)
                       and len(current_station['album']))
        has_track = (('track' in current_station)
                     and current_station['track'])
        if has_message:
            text = current_station['message']
        if has_title:
            text += current_station['title']
        elif has_file:
            text += current_station['file']
        if has_album:
            if has_track and current_station['track'] != '0':
                text += ' ({0}:{1})'.format(current_station['album'],
                                           current_station['track'])
            else:
                text += ' ({0})'.format(current_station['album'])
        return text

    
    # Display the currently playing station or track
    def get_current_string(self,index):
        current_station = radio.getPlayListEntry(index)
        return self.format_entry(current_station)
        

    # Display time and timer/alarm
    def display_time(self,x,y):
        beat = int(time.time()) % len(self.time_formats)
        timenow = strftime(self.time_formats[beat])
	if radio.getTimer():
            message = timenow + " " + radio.getTimerString()
            if radio.alarmActive():
                message = message + " " + radio.getAlarmTime()
        lcd.lock()
        lcd.line(x,y, timenow)
        lcd.unlock()
	return

    def display_volume(self,x,y):
	if radio.getStreaming():
		stream = '*'
        else: stream = ' '
	msg = "Volume %s %s" % (radio.getVolume(),stream)
	lcd.line(x,y, msg)

    def please_wait(self):
        lcd.lock()
        lcd.line(0,1,_(" Please wait...  "))
        lcd.unlock()

    def save_playlist_m3u(self,playlist):
        lines = ['#EXTM3U']
        for entry in playlist:
            lines.append("#EXTINF:{0},{1}".format(-1,entry['title']))
            lines.append(entry['file'])
        filename = config.get('Paths','playlist') + '/' + \
                   time.strftime(config.get('Settings','playlist_format')) + '.m3u'
        m3ufile = open(filename,'w')
        try:
            for line in lines:
                m3ufile.write(line.encode('utf8', 'replace') + "\n")
            m3ufile.close()
        except Exception as e:
            lcd.lock()
            lcd.line(0,1,_('Error'))
            lcd.unlock()
            log.message("Failed to create {0}.\n{1}".
                        format(filename,unicode(e)),log.ERROR)
        return

        
    def get_playlist_types(self):
        return {
            'm3u': self.save_playlist_m3u
        }

        
class shutdown_question(menu):
    def __init__(self, parent):
        self._parent = parent
        
    def displayMode(self):
        lcd.lock()
        lcd.clear()
        lcd.line(0,0,"Really shutdown?")
        lcd.line(0,1,"Press Power")
        lcd.unlock()

    def power(self,event):
        submenu(shutdown_menu())

    def ir_key(self,event):
        submenu(self._parent)
        return

    @classmethod
    def del_command(cls, name):
        if getattr(cls, name, None) is not None:
            try:
                delattr(cls, name)
            except AttributeError:
                setattr(cls, name, cls.ir_key)

for key in ir_keys:
    if key != "power":
        shutdown_question.del_command(key)



class number_entry(menu):
    _number = 0
    _count = 0
    _maxcount = 0
    _exitnumber = 0
    _maxnumber = 0
    _parent = None
    _line = 1
    _row = 0
    
    def __init__(self,parent,maxnumber, x, y):
        self._count = 0
        self._maxnumber = maxnumber
        if maxnumber > 0:
            self._maxcount = int(math.floor(math.log10(maxnumber))+1)
        else:
            self._maxcount = 1
        self._exitnumber = int(maxnumber) / 10
        log.message("max: {0}, exit: {1}".format(maxnumber,
                                                 self._exitnumber),
                    log.DEBUG)
        self._parent = parent

    def get_parent(self):
        return self._parent()

    def number_pressed(self,key):
        self._number = self._number * 10 + key
        self._count += 1
        self.displayMode()
        if ((self._number > self._exitnumber) 
            or (self._count > self._maxcount)):
            if self._number < self._maxnumber:
                self._parent.number_entry(self._number)
            submenu(self._parent)
            return

    def back(self,event):
        submenu(self._parent)
        return

    def clear(self,event):
        submenu(self._parent)
        return


    def displayMode(self):
        lcd.lock()
        lcd.line(self._row,self._line,
                 ("{0}".format(self._number).rjust(self._maxcount," ")),
                 self._maxcount)
        lcd.unlock()
        return
    
                            

        
class shutdown_menu(menu):
    def update_radio(self):
        self.displayMode()

    def displayMode(self):
        lcd.lock()
	lcd.line(0,0, "Stopping radio")
	radio.execCommand("shutdown -h now")
	lcd.line(0,1, "Shutting down")
        lcd.backlight(False)
        lcd.display(False)
        lcd.unlock()
        
class date_play_menu(menu):
    last_index = 0
    last_string = ""
    display_type = 0
    NORMAL_DISPLAY = 0
    CLEAR_DISPLAY = 1

    def get_parent_menu(self):
        return search_menu()

    def update_radio(self):
        global current_playmenu
        current_playmenu = self
        self.display_type = self.CLEAR_DISPLAY
        self.last_string = ""
        self.displayMode()
        return

    def display_elapsed(self):
        secounds = radio.getElapsedTime()
        if secounds:
            secounds = int(round(secounds))
            (minutes,secounds) = divmod(secounds,60)
            elapsed = '{0:4}:{1:02}'.format(minutes,secounds)
        else:
            elapsed = ""
        lcd.lock()
        lcd.line(2,0,elapsed,7)
        lcd.unlock()

    def displayMode(self):
        if (self.display_type == self.CLEAR_DISPLAY):
            lcd.lock()
            lcd.clear()
            lcd.unlock()
            # avoid calling displayMode
            super(date_play_menu,self).player_changed_callback()
        currentsong = radio.getCurrentSong()
        if currentsong:
            index = int(currentsong[u'pos'])
            radio.setSearchIndex(index)
            new_string = self.format_entry(currentsong)
            playlistlength = radio.getStatusField('playlistlength')
            lcd.lock()
            if (playlistlength):
                index_length = len(playlistlength) + 1
                lcd.line(0,1,
                         ("{0}".format(index+1)).rjust(index_length-1,"0"),
                         index_length)
            else: index_length = 0
            lcd.scroll(index_length,1,new_string)
            lcd.unlock()
        else:
            lcd.lock()
            lcd.line(0,1,_("   No music"))
            lcd.unlock()
        self.display_type = self.NORMAL_DISPLAY
        self.update = 1
        
    def heartbeat(self):
        current_time = time.time()
        if self.update >= 0 \
           and self.update <= current_time:
            self.display_time(10,0)
            self.display_elapsed()
            self.update = float(current_time + 1)

    def player_changed_callback(self):
        super(date_play_menu,self).player_changed_callback()
        self.displayMode()

    def number_pressed(self,number):
        length = radio.getStatusField('playlistlength')
        if length == None:
            length = -1
        submenu(number_entry(self,
                             int(length)+1,
                             0,1
                         ))
        current_menu.number_pressed(number)

    def number_entry(self,key):
        if (key < 1):
            self.displayMode()
            return
        radio.play(key-1)

    def menu(self,event):
        currentsong = radio.getCurrentSong()
        submenu(playlist_entry_menu(self,self.format_entry(currentsong)))

        

# search station as well as music files by artist
class search_menu(menu):
    changed = False
    def get_parent_menu(self):
        return top_menu()

    def update_radio(self):
        self.changed = True
        self.displayMode()

    def displayMode(self):
        playlist        = radio.getPlayList()
       	index           = radio.getSearchIndex()
        if len(playlist):
            current = radio.getPlayListEntry(index)
        else: current = None
        
        lcd.lock()
        status = radio.getStatus()
        if self.changed:
            if current != None:
                if (('artist' in current) and 
                    len(current['artist'])):
                    lcd.scroll(2,0, current['artist'])
                else:
                    lcd.line(2,0, "Playlist")
                count = len(playlist)
                if count:
                    index_length = len("{0}".format(len(playlist)))
                    lcd.line(0,1,
                             ("{0}".format(index+1)).rjust(index_length,"0"),
                             index_length)
                    index_length+=1
                else: index_length = 0
                lcd.scroll(index_length,1,self.format_entry(current))
            else:
                index_length = 0
                lcd.line(0,1,_("*Empty playlist*"))
            self.changed = False
        lcd.unlock()
	return

    def previous_artist(self,event):
	index = radio.getSearchIndex()
	playlist = radio.getPlayList()
	current_artist = radio.getArtistName(index)

	found = False
	leng = len(playlist)
	count = leng
	while not found:
            if index > 0:
                index = index - 1
            else: index = leng - 1

            new_artist = radio.getArtistName(index)
            if current_artist != new_artist:
                found = True

            count = count - 1

            # Prevent everlasting loop
            if count < 1:
                found = True
        if count > 0:
            self.changed = True
            radio.setSearchIndex(index)
	return

    def next_artist(self,event):
	index = radio.getSearchIndex()
	playlist = radio.getPlayList()
	current_artist = radio.getArtistName(index)

	found = False
	leng = len(playlist)
	count = leng
	while not found:
            index = index + 1
            if index >= leng:
                index = 0

            new_artist = radio.getArtistName(index)
            if current_artist != new_artist:
                found = True

            count = count - 1

            # Prevent everlasting loop
            if count < 1:
                found = True
                
        if count > 0:
            radio.setSearchIndex(index)
            self.changed = True
	return

    def previous_entry(self,event):
        self.changed = True
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()
	
        leng = len(playlist)
        log.message("len playlist =" + str(leng),log.DEBUG)
        if index > 0:
            index = index - 1
        else: index = leng-1
			
 	radio.setSearchIndex(index)
        self.changed = True
        self.displayMode()
	return 

    def previous_song(self,event):
        radio.setSearchIndex(radio.getCurrentId())
        self.previous_entry(event)
        self.play(event)
        return

    def next_entry(self,event):
        self.changed = True
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()
	
        leng = len(playlist)
        log.message("len playlist =" + str(leng),log.DEBUG)
        index = index + 1
        if index >= leng:
            index = 0
			
 	radio.setSearchIndex(index)
        self.changed = True
        self.displayMode()
	return 

    def next_song(self,event):
        radio.setSearchIndex(radio.getCurrentId())
        self.next_entry(event)
        self.play(event)
        return

    def play(self,event):
        radio.play(radio.getSearchIndex())
        submenu(date_play_menu())

    def enterbutton(self,event):
        self.play(event)

    def button1(self,event):
        self.previous_artist(event)

    def button2(self,event):
        self.next_artist(event)

    def leftswitch(self,event):
        self.previous_entry(event)

    def left(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def right(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        if self.changed:
            self.play(event)
        else: 
            super(search_menu,
                  self).leftrightbutton(event)

    def number_pressed(self,number):
        submenu(number_entry(self,
                             int(radio.getStatusField('playlistlength')),
                             0,1
                         ))
        current_menu.number_pressed(number)

    def number_entry(self,key):
        if (key < 1): return
 	radio.setSearchIndex(key-1)
        self.changed = True
        self.displayMode()
            
    def back(self,event):
        submenu(current_playmenu)
        return

    def clear(self,event):
        submenu(current_playmenu)
        return

class path_menu(menu):
    current_path = None
    current_dir = None
    current_type = None
    parent_path = None
    current_entry = None
    insert_position = 1
    entry_list = None
    index_places = None
    def __init__(self, 
                 path,
                 current_type,
                 add_playlists=True,
                 add_directories=True,
                 add_files=True,
                 clear_list = True):
        super(path_menu,self).__init__()
        log.message("path_menu.init({0})".format(path),log.DEBUG)
        self.current_path = path
        self.current_type = current_type
        (self.parent_path,self.current_dir) = posixpath.split(path)
        if clear_list:
            self.entry_list = [ [u'← ..', self.gotoparent, None]]
        self.current_entry = 0
        if (add_playlists or add_directories or
            add_files):
            top_list = radio.listNode(path)
            self.addlist(top_list,add_playlists, add_directories, add_files)
        log.message("path_menu: got {0} entries".format(len(self.entry_list)),
                    log.DEBUG)
            
    def addlist(self, rawlist,
                add_playlists=True,
                add_directories=True,
                add_files=True
            ):
        for node in rawlist:
            if "directory" in node:
                if (add_directories):
                    self.entry_list.insert(self.insert_position,
                                           [posixpath.basename(node['directory']),
                                            self.gotodirectory,node])
                    self.insert_position += 1
            elif "playlist" in node:
                if (add_playlists):
                    self.entry_list.insert(self.insert_position,
                                           [posixpath.basename(node['playlist']),
                                            self.gotoplaylist,node])
                    self.insert_position += 1
            elif "file" in node:
                if (add_files):
                    self.entry_list.insert(self.insert_position,
                                           [self.formatfile(node),
                                            self.gotofile,node])
                    self.insert_position += 1
            else:
                log.message("path_menu: Unknown entry: " + unicode(node), log.WARNING)

    def get_parent_menu(self):
        log.message("parent path: " + self.parent_path, log.DEBUG)
        if (self.parent_path == "/" or self.parent_path==""):
            return top_menu()
        else:
            return path_menu(self.parent_path,'directory')

    def update_radio(self):
        self.index_places = len(str(len(self.entry_list)))
        super(path_menu,self).update_radio()
        
        
    def gotoparent(self,node):
        self.please_wait()
        self.parent_menu()

    def gotodirectory(self,node):
        self.please_wait()
        submenu(path_menu(node['directory'],'directory'))

    def gotoplaylist(self,node):
        self.please_wait()
        submenu(playlist_menu(node['playlist']),'playlist')

    def gotofile(self,node):
        self.please_wait()
        log.message("loading {0}: {1}".format(self.current_type,
                                              self.current_path),
                    log.DEBUG)
        
        radio.changeDir(self.current_path)
        log.message("loaded {0}: {1}".format(self.current_type,
                                             self.current_path),
                    log.DEBUG)
        radio.playNode(node)
        log.message("Playback started", log.DEBUG)
        radio.save_current_dir(self.current_type,
                               self.current_entry,
                               self.current_path)
        submenu(date_play_menu())

    def play(self,event):
        self.entry_list[self.current_entry][1](self.entry_list[self.current_entry][2])

    def addtoradio(self,event):
        try:
            entry = self.entry_list[self.current_entry][2]
            log.message("addtoradio: " + unicode(entry), log.DEBUG)
            if ('file' in entry and len(entry['file'])):
                path = entry['file']
            elif ('directory' in entry and len(entry['directory'])):
                path = entry['directory']
            elif ('playlist' in entry and len(entry['playlist'])):
                path = entry['playlist']
            else: return
            log.message("path: " + paths, log.DEBUG)
            radio.addToStoredPlaylist(path,_('Radio'))
        except:
            lcd.lock()
            lcd.line(0,1,"Possibly failed.")
            time.sleep(1.0)
            lcd.unlock()
            self.displayMode()

    def setplaceradio(self,event):
            entry = self.entry_list[self.current_entry][2]
            log.message("addtoradio: " + unicode(entry), log.DEBUG)
            if ('file' in entry and len(entry['file'])):
                path = self.current_path
                ptype = self.current_type
            elif ('directory' in entry and len(entry['directory'])):
                path = entry['directory']
                ptype = 'directory'
            elif ('playlist' in entry and len(entry['playlist'])):
                path = entry['playlist']
                ptype = 'playlist'
            else:
                lcd.lock()
                lcd.line(0,1,"Possibly failed.")
                time.sleep(1.0)
                lcd.unlock()
                self.displayMode()
                return
            if ptype is not 'radio':
                config.libset('Radio','place_uri',path)
                config.libset('Radio','place_type',ptype)
                config.save_libconfig()
        

    def displayMode(self):
        lcd.lock()
        if self.changed:
            lcd.scroll(2,0, "{0}:".format(self.current_dir))
            if (self.current_entry > 0):
                lcd.line(0,1,
                         ("{0}".format(self.current_entry)).rjust(self.index_places,"0"),
                         self.index_places+1)
                lcd.scroll(self.index_places+1,1,
                           self.entry_list[self.current_entry][0])
            else:
                lcd.scroll(0,1, self.entry_list[self.current_entry][0])
            self.changed = False
        lcd.unlock()
	return

    def number_pressed(self,number):
        with lcd:
            lcd.line(0,1,"")
        length = radio.getStatusField('playlistlength')
        if length == None:
            length = -1
        submenu(number_entry(self,
                             len(self.entry_list),
                             0,1))
        current_menu.number_pressed(number)

    def number_entry(self,key):
        if (key < 1):
            self.displayMode()
            return
        self.current_entry = key
        self.displayMode()

    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.changed = True
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        log.message("New entry: " + unicode(self.entry_list[self.current_entry]),log.DEBUG)
        self.changed = True
        self.displayMode()

    def enterbutton(self,event):
        log.message("EnterButton",log.DEBUG)
        self.play(event)

    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        self.enterbutton(event)

    def left(self,event):
        self.previous_entry(event)

    def right(self,event):
        self.next_entry(event)

    def down(self,event):
        self.parent_menu()

    def menu(self,event):
        submenu(entry_menu(self,self.entry_list[self.current_entry][0]))

class top_menu(path_menu):
    def __init__(self):
        log.message("top_menu.init()",log.DEBUG)
        self.entry_list = [ [u"→ current",       self.gotocurrent,   None],
                            ["Radio",            self.gotoradio,     None],
                            ["Global playlists", self.gotoplaylists, None],
                            ["RSS",              self.gotoRSS,       None],
                            ["Sleep",            self.gotosleep,     None],
                            ["Shut down",        self.gotoshutdown,  None],
                            ["Options",          self.gotooptions,   None],
                            ["Mount/Unmount",    self.gotomount,     None],
                            ["About",            self.gotoabout,     None] ]
        self.insert_position = 3
        super(top_menu,self).__init__("/",
                                      'directory',
                                      add_playlists = False,
                                      clear_list = False)

    def get_parent_menu(self):
        return self

    def displayMode(self):
        lcd.lock()
	lcd.line(2,0, "Main Menu:")
        log.message(unicode(self.entry_list[self.current_entry]),log.DEBUG)
        lcd.scroll(0,1, self.entry_list[self.current_entry][0])
        lcd.unlock()
	return

    def gotodirectory(self,node):
        self.please_wait()
        submenu(path_menu('{0}'.format(node['directory']),'directory'))

    def gotocurrent(self,node):
        self.please_wait()
        if current_playmenu:
            submenu(current_playmenu)
    
    def gotoplaylists(self,node):
        self.please_wait()
        submenu(top_playlist_menu())
        
    def gotoRSS(self,node):
        self.please_wait()
        submenu(rss_menu())
        
    def gotosleep(self,node):
        self.please_wait()
        submenu(sleep_menu())

    def gotoshutdown(self,node):
        self.please_wait()
        submenu(shutdown_menu())

    def gotooptions(self,node):
        self.please_wait()
        submenu(options_menu())

    def gotomount(self,node):
        self.please_wait()
        submenu(mount_menu())

    def gotoabout(self,node):
        self.please_wait()
        submenu(about_menu())


class top_playlist_menu(path_menu):
    def __init__(self):
        super(top_playlist_menu,self).__init__("",
                                               'directory',
                                               add_playlists=False,
                                               add_directories=False,
                                               clear_list = True)
        log.message("top_playlist_menu.init()",log.DEBUG)
        top_list = radio.listPlaylists("")
        self.addlist(top_list)

    def displayMode(self):
        lcd.lock()
	lcd.line(2,0, "Playlists:")
        lcd.scroll(0,1, self.entry_list[self.current_entry][0])
        lcd.unlock()
	return

class playlist_menu(path_menu):
    def __init__(self,path,playlist_type):
        super(playlist_menu,self).__init__(path, playlist_type,
                                           add_playlists=False,
                                           add_directories=False,
                                           clear_list = True)
        log.message("playlist_menu.init()",log.DEBUG)
        playlist = radio.listPlaylist(path)
        log.message(unicode(playlist),log.DEBUG)
        self.addlist(playlist)

        if False:
            def displayMode(self):
                lcd.lock()
                lcd.line(2,0, "Playlists:")
                lcd.scroll(0,1, self.entry_list[self.current_entry][0])
                lcd.unlock()
            return

    def gotofile(self,node):
        self.please_wait()
        log.message("loading real playlist: " + self.current_path,
                    log.DEBUG)
        radio.loadPlaylist(self.current_path, True)
        log.message("playing node: " + unicode(node),
                    log.DEBUG)
        currentid = radio.playNode(node)
        radio.save_current_dir(self.current_type,
                               currentid,
                               self.current_path)
        log.message("done.", log.DEBUG)
        submenu(date_play_menu())

class entry_menu(menu):
    current_entry = 0
    parent_menu_object = None
    entry_list = None
    name = "???"
    def __init__(self, parent_menu,name):
        self.parent_menu_object = parent_menu
        self.name = name
        self.entry_list = [[u"← ..", lambda(event): self.parent_menu() ],
                           [u"Play", self.play],
                           [u"Add to Radio", self.addtoradio],
                           [u"Set directory for local radio", self.setplaceradio] ]

    def get_parent_menu(self):
        if self.parent_menu_object:
            return self.parent_menu_object
        else:
            return top_menu()

    def play(self,event):
        self.parent_menu_object.play(event)

    def addtoradio(self,event):
        submenu(self.parent_menu_object)
        self.parent_menu_object.addtoradio(event)

    def setplaceradio(self,event):
        submenu(self.parent_menu_object)
        self.parent_menu_object.setplaceradio(event)

    def displayMode(self):
        lcd.lock()
        log.message("displaymode: " + self.name, log.DEBUG)
	lcd.scroll(1,0, _(u"{0}").format(self.name))
        lcd.line(0,1, self.entry_list[self.current_entry][0])
        lcd.unlock()
	return

    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        self.displayMode()

    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def left(self,event):
        self.previous_entry(event)

    def right(self,event):
        self.next_entry(event)

    def ok(self,event):
        self.entry_list[self.current_entry][1](event)

class playlist_entry_menu(entry_menu):
    def __init__(self, parent_menu,name):
        self.parent_menu_object = parent_menu
        self.name = name
        self.entry_list = [[u"← ..", lambda(event): self.parent_menu() ],
                           [u"Remove from list", self.removefromplaylist],
                           [u"Add to Radio", self.addtoradio],
                           [u"Save playlist", self.saveplaylist] ]

    def saveplaylist(self,event):
        pltype   = config.get('Settings','playlist_type')
        self.get_playlist_types()[pltype](radio.getPlayList())
        self.parent_menu()
        return

    def removefromplaylist(self,event):
        return
    

class options_menu(menu):
    current_entry = 0
    entry_list = [["Options:"        , "Go back"],
                  ["Playback Options", "Random "],
                  ["Playback Options", "Consume "],
                  ["Playback Options", "Repeat "],
                  ["Output to Stream", "Streaming "],
                  ["Set Timer:"      , "Timer "],
                  ["Set alarm mode:" , "" ],
                  ["Set alarm time:" , "" ],
                  ["Update library:" , "Update list: "]]
    def get_parent_menu(self):
        return top_menu()

    def option_up(self, event):
        if (self.current_entry == 0):
            parent_menu()
        elif self.current_entry == 1:
            radio.setRandom(True)
        elif self.current_entry == 2:
            radio.setConsume(True)
        elif self.current_entry == 3:
            radio.setRepeat(True)
        elif self.current_entry == 4:
            radio.setStreaming(True)
        elif self.current_entry == 5:
            if radio.getTimer():
                radio.incrementTimer(1)
            else:
                radio.timerOn()
        elif self.current_entry == 6:
            radio.alarmCycle(radio.UP)
        elif self.current_entry == 7:
            radio.incrementAlarm(60)
        elif self.current_entry == 8:
            radio.setUpdateLibOn()
        self.displayMode()

    def option_down(self, event):
        if (self.current_entry == 0):
            parent_menu()
        elif self.current_entry == 1:
            radio.setRandom(False)
        elif self.current_entry == 2:
            radio.setConsume(False)
        elif self.current_entry == 3:
            radio.setRepeat(False)
        elif self.current_entry == 4:
            radio.setStreaming(False)
        elif self.current_entry == 5:
            if (radio.getTimerValue > 0):
                radio.decrementTimer(1)
            else: radio.timerOff()
        elif self.current_entry == 6:
            radio.alarmCycle(radio.DOWN)
        elif self.current_entry == 7:
            radio.decrementAlarm(60)
        elif current_enty == 8:
            radio.setUpdateLibOff()
        self.displayMode()

    def option_up2(self, event):
        if self.current_entry == 7:
            radio.incrementAlarm(1)
            self.displayMode()
        else: self.option_up(event)

    def option_down2(self, event):
        if self.current_entry == 7:
            radio.decrementAlarm(1)
            self.displayMode()
        else: self.option_down(event)
            
    def onoffstr(self,value):
        if (value):
            return "On"
        else: return "Off"

    def displayMode(self):
        current_str = list(self.entry_list[self.current_entry]);
        if self.current_entry == 1:
            current_str[1] += self.onoffstr(radio.getRandom())
        elif self.current_entry == 2:
            current_str[1] += self.onoffstr(radio.getConsume())
        elif self.current_entry == 3:
            current_str[1] += self.onoffstr(radio.getRepeat())
        elif self.current_entry == 4:
            current_str[1] += self.onoffstr(radio.getStreaming())
        elif self.current_entry == 5:
            if radio.getTimer():
                current_str[1] += radio.getTimerString()
            else:
                current_str[1] += "Off"
        elif self.current_entry == 6:
            alarmType = radio.getAlarmType()
            if alarmType == radio.ALARM_OFF:
                current_str[1] = "No alarm"
            elif alarmType == radio.ALARM_ON:
                current_str[1] = "Do not repeat"
            elif alarmType == radio.ALARM_REPEAT:
                current_str[1] = "Repeat every day"
            elif alarmType == radio.ALARM_WEEKDAYS:
                current_str[1] = "Weekdays only"
        elif self.current_entry == 7:
            current_str[1] += radio.getAlarmTime()
        elif self.current_entry == 8:
            current_str[1] += self.onoffstr(radio.getUpdateLibrary())
            
            
        lcd.lock()
	lcd.line(2,0, current_str[0])
        lcd.line(0,1, current_str[1])
        lcd.unlock()
	return

    def options_changed_callback(self):
        self.displayMode()
    
    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        self.displayMode()

    def button1(self,event):
        button_pressed = True
        twait = 0.4
        while button_pressed:
            self.option_down(event)
            self.displayMode()
            if (self.current_entry == 5 or 
                self.current_entry == 7):
                time.sleep(twait)
                twait = 0.1
                button_pressed = lcd.buttonPressed(lcd.BUTTON1)
            else: button_pressed = False

    def button2(self,event):
        button_pressed = True
        twait = 0.4
        while button_pressed:
            self.option_up(event)
            self.displayMode()
            if (self.current_entry == 5 or 
                self.current_entry == 7):
                time.sleep(twait)
                twait = 0.1
                button_pressed = lcd.buttonPressed(lcd.BUTTON2)
            else: button_pressed = False

    def button3(self,event):
        button_pressed = True
        twait = 0.4
        while button_pressed:
            self.option_down2(event)
            self.displayMode()
            if (self.current_entry == 5 or 
                self.current_entry == 7):
                time.sleep(twait)
                twait = 0.1
                button_pressed = lcd.buttonPressed(lcd.BUTTON1)
            else: button_pressed = False

    def button4(self,event):
        button_pressed = True
        twait = 0.4
        while button_pressed:
            self.option_up2(event)
            self.displayMode()
            if (self.current_entry == 5 or 
                self.current_entry == 7):
                time.sleep(twait)
                twait = 0.1
                button_pressed = lcd.buttonPressed(lcd.BUTTON2)
            else: button_pressed = False

    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def left(self,event):
        self.previous_entry(event)

    def right(self,event):
        self.next_entry(event)

    def up(self,event):
        self.option_up(event)
        
    def down(self,event):
        self.option_down(event)

    def menu(self,event):
        self.menubutton(event)
        return

    def enterbutton(self,event):
        self.option_up(event)
        return

    def back(self,event):
        self.parent_menu()

class about_menu(menu):
    def get_parent_menu(self):
        return top_menu()

    def displayMode(self):
        lcd.lock()
        ipaddr = exec_cmd('hostname -I')
        if ipaddr is "":
            lcd.line(0, 1, "No IP network")
        else:
            lcd.scroll(0, 1, "IP " + ipaddr)
        lcd.line(2, 0, "Radio v" + radio.getVersion())
        lcd.unlock()
   
class rss_menu(menu):
    def get_parent_menu(self):
        return top_menu()

    def displayMode(self):
        self.display_time(10,0)
	rss_line = rss.getFeed()
        with lcd:
            lcd.setScrollSpeed(0.2) # Display rss feeds a bit quicker
            lcd.scroll(0, 1, rss_line)

class sleep_menu(menu):
    def get_parent_menu(self):
        return top_menu()

    def update_radio(self):
        lcd.backlight(False)
        radio.mute()

    def displayMode(self):
        self.display_time(10,0)
        message = 'Sleep mode'
	if radio.alarmActive():
            message = "Alarm " + radio.getAlarmTime()
        lcd.lock()
        lcd.line(0,1, message)
        lcd.unlock()

    def heartbeat(self):
        super(sleep_menu,self).heartbeat()
        # Alarm wakeup function
        if radio.alarmFired():
            log.message("Alarm fired", log.INFO)
            self.wakeup()

    def wakeup(self):
        log.message("Alarm fired", log.INFO)
        radio.unmute()
        message = 'Good day'
	t = datetime.datetime.now()
	if t.hour >= 0 and t.hour < 12:
		message = 'Good morning'
	if t.hour >= 12 and t.hour < 18:
		message = 'Good afternoon'
	if t.hour >= 16 and t.hour <= 23:
		message = 'Good evening'
        lcd.lock()
	lcd.line(0,1, message)
        lcd.backlight(True)
        lcd.unlock()
	time.sleep(3)
        self.reactivate_playmenu()

    def button1(self,event):
        self.wakeup()

    def button2(self,event):
        self.wakeup()

    def button3(self,event):
        self.wakeup()

    def button4(self,event):
        self.wakeup()

    def button5(self,event):
        self.wakeup()

    def leftswitch(self,event):
        self.wakeup()

    def rightswitch(self,event):
        self.wakeup()

    def leftrightbutton(self,event):
        self.wakeup()

class radio_station_menu(menu):
    current_entry = 0
    heading = "Unknown menu"
    entry_list = {}
    
    def __init__(self, stations, heading):
        self.heading = heading
        self.entry_list = stations

    def displayMode(self):
        log.message("Current Station: " + 
                    unicode(self.entry_list[self.current_entry]), 
                    log.DEBUG)
        lcd.lock()
	lcd.line(2,0, self.heading % (self.current_entry + 1))
        lcd.line(0,1, self.entry_list[self.current_entry]['name'])
        lcd.unlock()
	return

    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        self.displayMode()

    def enter(self,event):
        return
            
    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        self.enter(event)


class radio_menu(menu):
    current_entry = 0

    def unimplemented():
        lcd.line(0,1,_("Unimplemented"))
        return
    def local_stations():
        submenu(radio_station_menu(radio_api.get_local_stations(99),
                                    "Local radio: %d"))
        return

    entry_list = (
        {'label': _('Local Stations'),
         'method': local_stations},
        {'label': _('Recomendations'),
         'method': unimplemented},
        {'label': _('Top 100'),
         'method': unimplemented},
        {'label': _('Genre'),
         'method': unimplemented},
        {'label': _('Topic'),
         'method': unimplemented},
        {'label': _('Category'),
         'method': unimplemented},
        {'label': _('City'),
         'method': unimplemented},
        {'label': _('Language'),
         'method': unimplemented},
        {'label': _('Search'),
         'method': unimplemented},
        {'label': _('My stations'),
         'method': unimplemented},
    )

    def __init__(self):
        super(radio_menu,self).__init__()
        log.message("radio_menu.init()",log.DEBUG)


    def displayMode(self):
        lcd.lock()
	lcd.line(0,0, "Search Radio:")
        lcd.line(0,1, self.entry_list[self.current_entry]['label'])
        lcd.unlock()
	return

    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        self.displayMode()

    def enter(self,event):
        self.entry_list[self.current_entry]['method']()
        return
        
            
    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        self.enter(event)


class mount_menu(menu):
    def __init__(self):
        super(menu,self).__init__()
        self.current_entry = 0

    def chop_dev(self,string):
        if not string.startswith("/dev/"):
            return string
        return string[len("/dev/"):len(string)]

    def update_radio(self):
        log.message("top_playlist_menu.init()",log.DEBUG)
        devlist = glob(config.get('Settings','mount_devices'))
        label_cmd = config.get('Settings','mount_label')
        type_cmd = config.get('Settings','mount_type')
        UUID_cmd = config.get('Settings','mount_UUID')
        devtypes = config.get('Settings','mount_devtypes').split(':')

        mounts = {}
        for line in file('/proc/mounts'):
            if line[0] != '/':
                continue
            line = line.split()
            if os.path.islink(line[0]):
                devname = os.readlink(line[0])
            else:
                devname = line[0]
            mounts[devname] = {
                'dev': line[0],
                'mountpoint': line[1],
                'type': line[2],
                'options': line[3]
            }
        
        self.entry_list = [[u"Mount/Umount",
                            u"← ..",
                            None,
                            self.gotoparent]]
        for dev in devlist:
            devtype = exec_cmd(type_cmd.format(dev))
            if devtype not in devtypes:
                continue
            label = exec_cmd(label_cmd.format(dev))
            UUID = exec_cmd(UUID_cmd.format(dev))
            if  len(label) == 0:
                label = None
            if dev in mounts:
                mount = mounts[dev]
                entry = {
                    'device': dev,
                    'type': devtype,
                    'UUID' : UUID,
                    'mountpoint': mount['mountpoint'],
                    'options': mount['options'],
                    'mounttype': mount['type']
                }
                if label:
                    entry['label'] = label
                else:
                    label = entry['UUID']
                mountlabel = "{0}: {1} ({2})".format(
                    label,
                    entry['mountpoint'],
                    entry['mounttype'])
                function = self.unmountentry
            else:
                entry = {
                    'device': dev,
                    'type': devtype,
                    'UUID' : UUID }
                if label:
                    entry['label'] = label
                else:
                    label = entry['UUID']
                mountlabel = label
                function = self.mountentry

            
            devlabel = "{0} ({1})".format(
                self.chop_dev(entry['device']),
                entry['type'])
            self.entry_list.append([
                devlabel,
                mountlabel,
                entry,
                function
            ])
        if self.current_entry >= len(self.entry_list):
            self.current_entry = 0
        self.displayMode()

    def get_parent_menu(self):
        return top_menu()


    def displayMode(self):
        entry = self.entry_list[self.current_entry]
        with lcd:
            lcd.scroll(2,0,entry[0])
            lcd.scroll(0,1,entry[1])
	return

    def gotoparent(self,node):
        self.please_wait()
        self.parent_menu()

    def mountentry(self,node):
        self.please_wait()
        self.update_radio()
        return

    def unmountentry(self,node):
        self.please_wait()
        dev = self.entry_list[self.current_entry][2]['device']
        label = exec_cmd(config.get('Settings',
                                    'umount_command').format(dev))
        sync()
        self.update_radio()
        return

    def previous_entry(self,event):
        size = len(self.entry_list)
        if self.current_entry > 0:
            self.current_entry = self.current_entry - 1
        else: self.current_entry = size - 1
        self.changed = True
        self.displayMode()

    def next_entry(self,event):
        size = len(self.entry_list)
        self.current_entry = self.current_entry + 1
        if self.current_entry >= size:
            self.current_entry = 0
        log.message("New entry: " +
                    unicode(self.entry_list[self.current_entry]),
                    log.DEBUG)
        self.changed = True
        self.displayMode()

    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        self.enterbutton(event)


