import os
import copy
import time
import datetime
from time import strftime
from radio_api import RadioApi
radio_api = RadioApi()
lcd = None
radio = None
rss = None
current_menu = None
log = None

def set_lcd(menu_lcd):
    global lcd
    lcd = menu_lcd

def set_radio(menu_radio):
    global radio
    radio = menu_radio

def set_rss(menu_rss):
    global rss
    rss = menu_rss
    
def submenu(menu):
    global current_menu
    current_menu = menu
    current_menu.update_radio()
    current_menu.displayMode()

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
        log.message("IR event: " + str(event),log.DEBUG)

    def key_channelup(self,event):
        current_menu.channel_up(event)

    def key_channeldown(self,event):
        current_menu.channel_down(event)

menukeys = menukeys_class()

class menu(object):
    changed = False
    ignore_button = None
    ignore_until = 0

    def __init__(self):
        self.changed = False

    def get_parent_menu(self):
        return self

    def parent_menu(self):
        submenu(self.get_parent_menu())

    def update_radio(self):
        return

    def displayMode(self):
        displayTime(lcd,radio)
        lcd.lock()
        lcd.line(0,1, "Unknown menu")
        lcd.unlock()

    def heartbeat(self):
        lcd.heartbeat()

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

    def increase_volume(self,event):
        volume = radio.increaseVolume()
        lcd.lock()
        self.display_volume(0,1)
        lcd.unlock()
        return volume                                                    
        
    def decrease_volume(self,event):
        volume = radio.decreaseVolume()
        lcd.lock()
        self.display_volume(0,1)
        lcd.unlock()
        return volume

    def channel_up(self,event):
        radio.channelUp()

    def channel_down(self,event):
        radio.channelDown()

    def enterbutton(self,event):
        return

    def menubutton(self,event):
        self.parent_menu()
        return

    def reactivate_playmenu(self):
        submenu(date_play_menu())

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
        self.displayMode()

    def rightswitch_off(self,event):
        self.displayMode()

    def leftrightbutton_off(self,event):
        log.message("Released left+right button", log.DEBUG)
        self.displayMode()

    def button1_off(self,event):
        self.displayMode()
        
    def button2_off(self,event):
        self.displayMode()

    def button3_off(self,event):
        self.displayMode()

    def button4_off(self,event):
        self.displayMode()

    def button5_off(self,event):
        self.displayMode()
 
    def update_radio(self):
        self.changed = False

    # Display the currently playing station or track
    def display_current(self,x,y):
	current_id = radio.getCurrentID()
	source = radio.getSource()

	if source == radio.RADIO:
		current = radio.getCurrentStation()
	else:
		current_artist = radio.getCurrentArtist()
		index = radio.getSearchIndex()
		current_artist = radio.getCurrentArtist()
		track_name = radio.getCurrentTitle()
		current = current_artist + " - " + track_name

        lcd.lock()
	# Display any stream error
	leng = len(current)
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll(x,y,errorStr)
		radio.clearError()
	else:
		leng = len(current)
		if leng > 16:
			lcd.scroll(x,y,current)
		elif  leng < 1:
			lcd.line(x,y, "No input!")
			time.sleep(1)
			radio.play(1) # Reset station or track
		else:
			lcd.line(x,y, current)
        lcd.unlock()
	return

    # Display time and timer/alarm
    def display_time(self,x,y):
        beat = int(time.time()) % 2
        if beat:
            timenow = strftime("%H.%M")
            todaysdate = strftime("%d.%m.%Y ") + timenow
        else:
            timenow = strftime("%H %M")
            todaysdate = strftime("%d.%m.%Y ") + timenow
	if radio.getTimer():
            message = timenow + " " + radio.getTimerString()
            if radio.alarmActive():
                message = message + " " + radio.getAlarmTime()
        else:
            message = todaysdate
        lcd.lock()
        lcd.line(x,y, message)
        lcd.unlock()
	return

    def display_volume(self,x,y):
	if radio.getStreaming():
		stream = '*'
        else: stream = ' '
	msg = "Volume %d %s" % (radio.getVolume(),stream)
	lcd.line(x,y, msg)

class shutdown_menu(menu):
    def update_radio(self):
        radio.setDisplayMode(radio.MODE_SHUTDOWN)
        self.displayMode()

    def displayMode(self):
        lcd.lock()
	lcd.line(0,0, "Stopping radio")
	radio.execCommand("service mpd stop")
	lcd.line(0,0, "Radio stopped")
	radio.execCommand("shutdown -h now")
	lcd.line(0,1, "Shutting down")
        lcd.unlock()

class date_play_menu(menu):
    next_time = 0

    def get_parent_menu(self):
        return search_menu()

    def update_radio(self):
        if radio.loadNew():
            log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
            radio.playNew(radio.getSearchIndex())
        radio.setDisplayMode(radio.MODE_TIME)
        self.displayMode()
        return

    def displayMode(self):
        self.display_time(0,0)
        if radio.muted():
            msg = "Sound muted"
            if radio.getStreaming():
                msg = msg + ' *'
            lcd.lock()
            lcd.line(0,1, msg)
            lcd.unlock()
        else:
            self.display_current(0,1)

    def heartbeat(self):
        current_time = time.time()
        if current_time >= self.next_time:
            self.display_time(0,0)
            self.next_time = int(current_time)+1
        lcd.heartbeat()



# search station as well as music files by artist
class search_menu(menu):
    def get_parent_menu(self):
        return top_menu()

    def update_radio(self):
        radio.setDisplayMode(radio.MODE_SEARCH)
        self.displayMode()

    def displayMode(self):
       	index = radio.getSearchIndex()
	source = radio.getSource()
        lcd.lock()
	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		lcd.scroll(0,0, "(" + str(index+1) + ")" + current_artist)
		current_track = radio.getTrackNameByIndex(index)
		lcd.scroll(0,1, current_track)
	else:
		lcd.line(0,0, "Search: " + str(index+1))
		current_station = radio.getStationName(index)
		lcd.scroll(0,1, current_station[0:160])
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

    def previous_song(self,event):
        self.changed = True
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()
	
        leng = len(playlist)
        log.message("len playlist =" + str(leng),log.DEBUG)
        if index > 0:
            index = index - 1
        else: index = leng-1
			
 	radio.setSearchIndex(index)	
	return 

    def next_song(self,event):
        self.changed = True
	playlist = radio.getPlayList()
	index = radio.getSearchIndex()
	
        leng = len(playlist)
        log.message("len playlist =" + str(leng),log.DEBUG)
        index = index + 1
        if index >= leng:
            index = 0
			
 	radio.setSearchIndex(index)	
	return 

    def play(self,event):
 	radio.setLoadNew(True)	
        submenu(date_play_menu())

    def button1(self,event):
        self.previous_artist(event)

    def button2(self,event):
        self.next_artist(event)

    def leftswitch(self,event):
        self.previous_song(event)

    def rightswitch(self,event):
        self.next_song(event)

    def leftrightbutton(self,event):
        if self.changed:
            self.play(event)
        else: 
            super(search_menu,
                  self).leftrightbutton(event)

class top_menu(menu):
    current_entry = None
    entry_list = [ "Radio",
                   "Internet Radio",
                   "Music library",
                   "RSS",
                   "Sleep",
                   "Shut down",
                   "Options",
                   "About" ]
    def __init__(self):
        super(top_menu,self).__init__()
        log.message("top_menu.init()",log.DEBUG)
        source = radio.getSource()
        if source == radio.RADIO:
            self.current_entry = 0
        elif source == radio.PLAYER:
            self.current_entry = 1
        else:
            self.current_entry = 0

    def displayMode(self):
        lcd.lock()
	lcd.line(0,0, "Main Menu:")
        lcd.line(0,1, self.entry_list[self.current_entry])
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
        if (self.current_entry == 0):
            submenu(radio_menu())
        elif self.current_entry == 1:
            radio.setSource(radio.RADIO)
            submenu(search_menu())
            current_menu.changed = True
        elif self.current_entry == 2:
            radio.setSource(radio.PLAYER)
            submenu(search_menu())
            current_menu.changed = True
        elif self.current_entry == 3:
            submenu(rss_menu())
        elif self.current_entry == 4:
            submenu(sleep_menu())
        elif self.current_entry == 5:
            submenu(shutdown_menu())
        elif self.current_entry == 6:
            submenu(options_menu())
        elif self.current_entry == 7:
            submenu(about_menu())
        return
        
            
    def leftswitch(self,event):
        self.previous_entry(event)

    def rightswitch(self,event):
        self.next_entry(event)

    def leftrightbutton(self,event):
        self.enter(event)

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
	lcd.line(0,0, current_str[0])
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
        lcd.line(0, 0, "Radio v" + radio.getVersion())
        lcd.unlock()
   
class rss_menu(menu):
    def get_parent_menu(self):
        return top_menu()

    def displayMode(self):
        self.display_time(0,0)
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
        self.display_time(0,0)
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
	lcd.line(0,0, self.heading % (self.current_entry + 1))
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
