#!/bin/bash
# $Id: create_tar.sh,v 1.35 2015/08/30 06:28:08 bob Exp $

FILELIST="README radiod config_class.py lcd_class.py lcd_i2c_pcf8475.py lcd_i2c_class.py log_class.py radio4.py rradio4.py rradiobp.py rradiobp4.py radio_class.py ada_*.py i2c_class.py radio_daemon.py  radiod.py rradiod.py rss_class.py test_lcd.py test_ada_lcd.py test_switches.py rotary_class.py test_rotary_class.py create_podcasts.py create_playlists.py display_current.py rc_daemon.py radio_piface.py remote_control.py test_remote_control.py display_model.py radiod.logrotate playlists translate_class.py station.urls podcasts.dist rss/* cron.hourly/* contributors/*"

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


