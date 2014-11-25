#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import posixpath
import copy
import time
import datetime
import config
from time import strftime
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

class menukeys_class:
    def button1(self,event):
        current_menu.button1(event)
        return

    def button2(self,event):
        current_menu.button2(event)
        return

    def button3(self,event):
        current_menu.button3(event)
        return

    def button4(self,event):
        current_menu.button4(event)
        return

    def button5(self,event):
        current_menu.button5(event)
        return

    def leftswitch(self,event):
        current_menu.leftswitch(event)
        return

    def rightswitch(self,event):
        current_menu.rightswitch(event)
        return

    def leftrightbutton(self,event):
        current_menu.leftrightbutton(event)
        return
 

    def leftswitch_off(self,event):
        current_menu.leftswitch_off(event)

    def rightswitch_off(self,event):
        current_menu.rightswitch_off(event)

    def leftrightbutton_off(self,event):
        current_menu.leftrightbutton_off(event)

    def button1_off(self,event):
        current_menu.button1_off(event)
        
    def button2_off(self,event):
        current_menu.button1_off(event)

    def button3_off(self,event):
        current_menu.button1_off(event)

    def button4_off(self,event):
        current_menu.button1_off(event)

    def button5_off(self,event):
        current_menu.button1_off(event)

    # IR remote control
    def key(self,event):
        log.message("IR event: " + str(event.ir_code),log.DEBUG)

    def home(self,event):
        current_menu.home(event)

    def back(self,event):
        current_menu.back(event)

    def menu(self,event):
        current_menu.menu(event)

    def tv(self,event):
        current_menu.tv(event)

    def radio(self,event):
        current_menu.radio(event)

    def power(self,event):
        current_menu.power(event)

    def up(self,event):
        current_menu.up(event)

    def down(self,event):
        current_menu.down(event)

    def left(self,event):
        current_menu.left(event)

    def right(self,event):
        current_menu.right(event)

    def enter(self,event):
        current_menu.enter(event)

    def ok(self,event):
        current_menu.ok(event)

    def volumeup(self,event):
        current_menu.increase_volume(event)

    def volumedown(self,event):
        current_menu.decrease_volume(event)

    def mute(self,event):
        current_menu.mute(event)

    def channelup(self,event):
        current_menu.channel_up(event)

    def channeldown(self,event):
        current_menu.channel_down(event)

    def previous(self,event):
        current_menu.previous(event)

    def stop(self,event):
        current_menu.stop(event)

    def record(self,event):
        current_menu.record(event)

    def previoussong(self,event):
        current_menu.previoussong(event)

    def nextsong(self,event):
        current_menu.nextsong(event)

    def pause(self,event):
        current_menu.pause(event)

    def play(self,event):
        current_menu.play(event)

    def rewind(self,event):
        current_menu.rewind(event)

    def fastforward(self,event):
        current_menu.fastforward(event)

    def text(self,event):
        current_menu.text(event)

    def subtitle(self,event):
        current_menu.subtitle(event)



menukeys = menukeys_class()

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
        lcd.heartbeat()
        current_time = time.time()
        if self.update <= current_time:
            self.displayMode()
            self.update = int(current_time)+1

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
                submenu(path_menu(radiopath))
            elif radiotype == 'playlist':
                submenu(playlist_menu(radiopath))
        except Exception as e:
            log.message('top_menu.gotoradio: Exception: '+unicode(e),
                        log.ERROR)

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

    def menu(self,event):
        self.menubutton(event)
        return

    def tv(self,event):
        return

    def radio(self,event):
        self.gotoradio({})
        return

    def power(self,event):
        submenu(shutdown_question())
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
        
    def decrease_volume(self,event):
        volume = radio.decreaseVolume()
        lcd.lock()
        self.display_volume(0,1)
        lcd.unlock()
        self.update = 3
        return volume

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
        self.channel_up(event)
        return

    def nextsong(self,event):
        self.channel_down(event)
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

    def formatfile(self,node):
        if (node['title']):
            fmt = '{0} ({1})'
        else:
            msg = ""
            fmt = '{1}'

        if (node['artist']):
            fmt2 = '{0}'
        else:
            fmt2 = ''

        if (node['album']):
            if (len(fmt2)):
                fmt2 += ': {1}'
            else:
                fmt2 = '{1}'

        if (node['track']):
            if (len(fmt2)):
                fmt2 += ': {2}'
            else:
                fmt2 = '{2}'
        msg2 = fmt2.format(node['artist'],
                           node['album'],
                           node['track'])
        return fmt.format(node['title'],msg2)
        

    # Display the currently playing station or track
    def get_current(self,index):
        current_station = radio.getStation(index)
        
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
            text += curret_station['file']
        if has_album:
            if has_track:
                text += '({0}:{1})'.format(current_station['album'],
                                           current_station['track'])
            else:
                text += '({0})'.format(current_station['album'])
	return text

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
	msg = "Volume %d %s" % (radio.getVolume(),stream)
	lcd.line(x,y, msg)

class shutdown_question(menu):
    def displayMode(self):
        lcd.lock()
        lcd.clear()
        lcd.line(0,0,"Really shutdown?")
        lcd.line(0,1,"Press Power")
        lcd.unlock()

    def power(self,event):
        submenu(shutdown_menu())

    

        
class shutdown_menu(menu):
    def update_radio(self):
        radio.setDisplayMode(radio.MODE_SHUTDOWN)
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

    def update_current_index(self):
        index = radio.getCurrentID()
        if index: index -= 1
        radio.setSearchIndex(index)
        self.last_index = index

    def update_radio(self):
        global current_playmenu
        
        self.update_current_index()
        current_playmenu = self
        if radio.loadNew():
            log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
            radio.playNew(radio.getSearchIndex())

        radio.setDisplayMode(radio.MODE_TIME)

        self.display_type = self.CLEAR_DISPLAY
        self.displayMode()
        return

    def displayMode(self):
        lcd.lock()
        if (self.display_type == self.CLEAR_DISPLAY):
            lcd.clear()
        status = radio.getStatus()
        log.message("displayMode:" +  unicode(status),
                    log.DEBUG)
        if 'elapsed' in status:
            secounds = int(round(float(status[u'elapsed'])))
            (minutes,secounds) = divmod(secounds,60)
            elapsed = '{0:4}:{1:02}'.format(minutes,secounds)
        else:
            elapsed = ""
        lcd.line(2,0,elapsed,7)
        if 'state' in status:
            lcd.putSymbol(0,0,status_symbols[status['state']])
        if 'song' in status:
            index = int(status[u'song'])
            if index != self.last_index or \
               self.update % 10 == 0 or \
               self.display_type == self.CLEAR_DISPLAY:
                radio.setSearchIndex(index)
                self.last_index = index
                new_string = self.get_current(index)
                if 'playlistlength' in status:
                    index_length = len(status['playlistlength'])
                    lcd.line(0,1,
                             ("{0}".format(index+1)).rjust(index_length,"0"),
                             index_length)
                    index_length += 1 # one space 
                else: index_length = 0
                if new_string != self.last_string:
                    lcd.scroll(index_length,1,new_string)
                    self.last_string = new_string
        else:
            lcd.line(0,1,_("No music"))
        lcd.unlock()
        self.display_time(10,0)
        self.display_type = self.NORMAL_DISPLAY
        

# search station as well as music files by artist
class search_menu(menu):
    changed = False
    def get_parent_menu(self):
        return top_menu()

    def update_radio(self):
        radio.setDisplayMode(radio.MODE_SEARCH)
        self.changed = True
        self.displayMode()

    def displayMode(self):
        playlist        = radio.getPlayList()
       	index           = radio.getSearchIndex()
	source          = radio.getSource()
        if len(playlist):
            current = radio.playlist[index]
        else: current = None
        
        lcd.lock()
        status = radio.getStatus()
        if 'state' in status:
            lcd.putSymbol(0,0,status_symbols[status['state']])
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
                
    
                lcd.scroll(index_length,1,self.get_current(index))
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
        radio.setSearchIndex(radio.getCurrentID())
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
        radio.setSearchIndex(radio.getCurrentID())
        self.next_entry(event)
        self.play(event)
        return

    def play(self,event):
 	radio.setLoadNew(True)	
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
            
class path_menu(menu):
    current_path = None
    current_dir = None
    parent_path = None
    current_entry = None
    insert_position = 1
    entry_list = None
    index_places = None
    def __init__(self, 
                 path,
                 add_playlists=True,
                 add_directories=True,
                 add_files=True,
                 clear_list = True):
        super(path_menu,self).__init__()
        log.message("path_menu.init({0})".format(path),log.DEBUG)
        self.current_path = path
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
                                           [pusixpath.basename(node['playlist']),
                                            self.gotoplaylist,node])
                    self.insert_position += 1
            elif "file" in node:
                if (add_files):
                    self.entry_list.insert(self.insert_position,
                                           [self.formatfile(node),
                                            self.gotofile,node])
            else:
                log.message("path_menu: Unknown entry: " + unicode(node), log.WARNING)

    def get_parent_menu(self):
        log.message("parent path: " + self.parent_path, log.DEBUG)
        if (self.parent_path == "/" or self.parent_path==""):
            return top_menu()
        else:
            return path_menu(self.parent_path)

    def update_radio(self):
        self.index_places = len(str(len(self.entry_list)))
        super(path_menu,self).update_radio()
        
        
    def gotoparent(self,node):
        self.parent_menu()

    def gotodirectory(self,node):
        submenu(path_menu(node['directory']))

    def gotoplaylist(self,node):
        submenu(playlist_menu(node['playlist']))

    def gotofile(self,node):
        radio.changeDir(self.current_path)
        radio.playNode(node)
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
                ptype = 'directory'
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
            config.libset('Radio','place_uri',path)
            config.libset('Radio','place_type',ptype)
            config.save_libconfig()
        

    def displayMode(self):
        lcd.lock()
        status = radio.getStatus()
        if 'state' in status:
            lcd.putSymbol(0,0,status_symbols[status['state']])
        lcd.scroll(2,0, "{0}:".format(self.current_dir))

        if self.changed:
            if (self.current_entry > 0):
                lcd.line(0,1,"{0}".format(self.current_entry))
                lcd.scroll(self.index_places+1,1, self.entry_list[self.current_entry][0])
            else:
                lcd.scroll(0,1, self.entry_list[self.current_entry][0])
            self.changed = False
        lcd.unlock()
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
        self.entry_list = [ [u"→ current", self.gotocurrent, None],
                            ["Radio", self.gotoradio, None],
                            ["Global playlists", self.gotoplaylists, None],
                            ["RSS", self.gotoRSS, None],
                            ["Sleep", self.gotosleep, None],
                            ["Shut down", self.gotoshutdown, None],
                            ["Options", self.gotooptions, None],
                            ["About", self.gotoabout,None] ]
        self.insert_position = 2
        super(top_menu,self).__init__("/",
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
        submenu(path_menu('{0}'.format(node['directory'])))

    def gotocurrent(self,node):
        if current_playmenu:
            submenu(current_playmenu)
    
    def gotoplaylists(self,node):
        submenu(top_playlist_menu())
        
    def gotoRSS(self,node):
        submenu(rss_menu())
        
    def gotosleep(self,node):
        submenu(sleep_menu())

    def gotoshutdown(self,node):
        submenu(shutdown_menu())

    def gotooptions(self,node):
        submenu(options_menu())

    def gotoabout(self,node):
        submenu(about_menu())


class top_playlist_menu(path_menu):
    def __init__(self):
        super(top_playlist_menu,self).__init__("",
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
    def __init__(self,path):
        super(playlist_menu,self).__init__("",
                                               add_playlists=False,
                                               add_directories=False,
                                               clear_list = True)
        log.message("playlist_menu.init()",log.DEBUG)
        playlist = radio.listPlaylist(path)
        log.message(unicode(playlist),log.DEBUG)
        self.addlist(playlist)

    def displayMode(self):
        lcd.lock()
	lcd.line(2,0, "Playlists:")
        lcd.scroll(0,1, self.entry_list[self.current_entry][0])
        lcd.unlock()
	return


class entry_menu(menu):
    current_entry = 0
    parent_menu_object = None
    entry_list = None
    name = "???"
    def __init__(self, parent_menu,name):
        self.parent_menu_object = parent_menu
        self.name = name
        self.entry_list = [[u"← ..", lambda(event): setmenu(self.get_parent_menu) ],
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
            radio.randomOn()
        elif self.current_entry == 2:
            if (radio.getSource() == radio.PLAYER):
                radio.consumeOn()
            else:
                lcd.lock()
                lcd.line(0,1, "Not allowed")
                time.sleep(2)
                lcd.unlock()
        elif self.current_entry == 3:
            radio.repeatOn()
        elif self.current_entry == 4:
            radio.streamingOn()
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
	radio.optionChangedTrue()

    def option_down(self, event):
        if (self.current_entry == 0):
            parent_menu()
        elif self.current_entry == 1:
            radio.randomOff()
        elif self.current_entry == 2:
            if (radio.getSource() == radio.PLAYER):
                radio.consumeOff()
            else:
                lcd.lock()
                lcd.line(0,1, "Not allowed")
                time.sleep(2)
                lcd.unlock()
        elif self.current_entry == 3:
            radio.repeatOff()
        elif self.current_entry == 4:
            radio.streamingOff()
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
	radio.optionChangedTrue()



    def option_up2(self, event):
        if self.current_entry == 7:
            radio.incrementAlarm(1)
            radio.optionChangedTrue()
        else: self.option_up(event)

    def option_down2(self, event):
        if self.current_entry == 7:
            radio.decrementAlarm(1)
            radio.optionChangedTrue()
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
