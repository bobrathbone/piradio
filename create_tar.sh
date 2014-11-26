#!/bin/bash
# $Id: create_tar.sh,v 1.30 2014/10/05 08:56:15 bob Exp $

FILELIST="README radiod lcd_class.py lcd_i2c_class.py log_class.py radio4.py rradio4.py rradiobp.py rradiobp4.py radio_class.py ada_*.py i2c_class.py radio_daemon.py  radiod.py rradiod.py rss_class.py test_lcd.py test_ada_lcd.py test_switches.py rotary_class.py test_rotary_class.py create_podcasts.py create_playlists.py display_current.py display_model.py radiod.logrotate playlists/* translate_class.py station.urls podcasts.dist rss/* cron.hourly/* contributors/*"

WEBPAGES="/var/www/*  /usr/lib/cgi-bin/select_*"

# Cleanup 
sudo rm -f *.pyc
sudo chown -R  pi:pi /home/pi/develop/pi/radio/${FILELIST}
sudo chmod +x *.py

# Create radio software tar file
sudo tar -cvzf  pi_radio.tar.gz ${FILELIST}

# Create Web pages tar file
sudo tar -cvzf  pi_radio_web.tar.gz ${WEBPAGES}

sudo chown pi:pi *.gz


