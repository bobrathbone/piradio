#!/bin/bash
# $Id: create_tar.sh,v 1.23 2014/05/19 08:59:03 bob Exp $

FILELIST="README radiod lcd_class.py log_class.py radio4.py rradio4.py radio_class.py ada_*.py i2c_class.py radio_daemon.py  radiod.py rradiod.py rss_class.py test_lcd.py test_ada_lcd.py test_switches.py rotary_class.py test_rotary_class.py create_playlists.py display_current.py radiod.logrotate playlists/* translate_class.py station.urls rss/*"

WEBPAGES="/var/www/*  /usr/lib/cgi-bin/select_*"

# Cleanup 
rm -f *.pyc
chown -R  pi:pi /home/pi/develop/pi/radio/${FILELIST}
chmod +x *.py

# Create radio software tar file
tar -cvzf  pi_radio.tar.gz ${FILELIST}

# Create Web pages tar file
tar -cvzf  pi_radio_web.tar.gz ${WEBPAGES}

chown pi:pi *.gz


