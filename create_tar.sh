#!/bin/bash
# $Id: create_tar.sh,v 1.28 2014/07/12 13:18:31 bob Exp $

FILELIST="README radiod lcd_class.py log_class.py radio4.py rradio4.py radio_class.py ada_*.py i2c_class.py radio_daemon.py  radiod.py rradiod.py rss_class.py test_lcd.py test_ada_lcd.py test_switches.py rotary_class.py test_rotary_class.py create_podcasts.py create_playlists.py display_current.py display_model.py radiod.logrotate playlists/* translate_class.py station.urls podcasts.dist rss/* cron.hourly/* contributors/*"

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


