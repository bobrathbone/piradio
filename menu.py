menu_lcd = None
menu_radio = None
current_menu = None
top_menu = None

def set_menu_lcd(lcd):
    menu_lcd = lcd

def set_menu_radio(radio):
    menu_radio = radio
    
class menu:
    changed = False
    parent_menu = None

    def __init__(self,parentmenu):
        self.parent_menu = parentmenu
        self.changed = False

    def submenu(self,menu):
        top_menu = menu

    def displayMode(self):
        displayTime(menu_lcd,radio)
        menu_lcd.lock()
        menu_lcd.line2("Unknown menu")
        menu_lcd.unlock()


    def leftswitch(self,event):
        return

    def rightswitch(self,event):
        return

    def enterbutton(self,event):
        if not self.changed and self.parent_menu:
            current_menu = self.parent_menu
        if radio.muted():
            unmuteRadio(lcd,radio)
        # Shutdown if menu button held for > 3 seconds
        MenuSwitch = True
        count = 15
        while MenuSwitch:
            time.sleep(0.2)
            MenuSwitch = menu_lcd.buttonPressed(menu_lcd.ENTER)
            menu_lcd.backlight(True)
            count = count - 1
            if count < 0:
                current_menu = shutdown_menu(self)
                MenuSwitch = False

        current_menu.update_radio()
        return

    def leftbutton(self,event):
        volchange = True
        while volchange:
            if menu_lcd.buttonPressed(lcd.LEFTBUTTON):
                radio.mute()
                lcdlock.acquire()
                lcd.line2("Mute")
                self.fix_display = 3
                lcdlock.release()
                volChange = False
                interrupt = True
            else:
                volume = radio.increaseVolume()
                displayVolume(lcd,radio)
                volChange = lcd.buttonPressed(lcd.RIGHT) 
                
                if volume >= 100:
                    volChange = False
                    time.sleep(0.05)
        return
                                                    
        
    def button2(self,event):
        log.message("2nd switch" ,log.DEBUG)
        # Increase volume
        volChange = True
        while volChange:
            menu_lcd.lock()
            menu_lcd.backlight(True)
            
            # Mute function (Both buttons depressed)
            if menu_lcd.buttonPressed(lcd.LEFTBUTTON):
                menu_radio.mute()
                lcd.line2("Mute")
                self.fix_display = 3
                volChange = False
                interrupt = True
            else:
                volume = menu_radio.increaseVolume()
                displayVolume(menu_lcd,menu_radio)
                volChange = menu_lcd.buttonPressed(lcd.RIGHT) 
                
                if volume >= 100:
                    volChange = False
                    time.sleep(0.05)
            menu_lcd.unlock()


    def button3(self,event):
        return

    def rightbutton(self,event):
        return

    def extrabutton(self,event):
        return
 

    def leftswitch_off(self,event):
        self.displayMode()

    def rightswitch_off(self,event):
        self.displayMode()

    def enterbutton_off(self,event):
        self.displayMode()

    def leftbutton_off(self,event):
        self.displayMode()
        
    def button2_off(self,event):
        self.displayMode()

    def button3_off(self,event):
        self.displayMode()

    def rightbutton_off(self,event):
        self.displayMode()

    def extrabutton_off(self,event):
        self.displayMode()
 
    def update_radio(self):
        self.changed = False

    # Display the currently playing station or track
    def get_current():
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

        lcdlock.acquire()
	# Display any stream error
	leng = len(current)
	if radio.gotError():
		current = radio.getErrorString()
		radio.clearError()
	else:
		leng = len(current)
		if leng > 16:
			lcd.scroll2(current[0:160],interrupt)
		elif  leng < 1:
			lcd.line2("No input!")
			time.sleep(1)
			radio.play(1) # Reset station or track
		else:
			lcd.line2(current)
        lcdlock.release()
	return


class shutdown_menu(menu):
    def update_radio(self):
        radio.setDisplayMode(radio.MODE_SHUTDOWN)
        self.displayMode()

    def displayMode(self):
        menu_lcd.lock()
	menu_lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop")
	menu_lcd.line1("Radio stopped")
	radio.execCommand("shutdown -h now")
	menu_lcd.line2("Shutting down")
        menu_lcd.unlock()

class date_play_menu(menu):
    def displayMode():
        displayTime(menu_lcd,radio)
        if radio.muted():
            msg = "Sound muted"
            if radio.getStreaming():
                msg = msg + ' *'
                menu_lcd.lock()
                menu_lcd.line2(msg)
                menu_lcd.unlock()
            else:
                display_current(lcd,radio)

