#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: select_daemon.sh,v 1.7 2014/06/22 12:10:15 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up which
# radio daemon is to be used
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

DAEMON=radiod.py

INIT=/etc/init.d/radiod
# Display types
LCD=3	# LCD screen (direct)
ADA=4	# Adafruit LCD plate

echo
echo "Radio daemon and board revision selection"
echo
echo "Select the radio daemon to be installed 1-5:"
echo
echo "1) Two line LCD with push buttons  (radiod.py)"
echo "2) Four line LCD with push buttons (radio4.py)"
echo "3) Two line LCD with rotary encoders  (rradiod.py)"
echo "4) Four line LCD with rotary encoders (rradio4.py)"
echo "5) Two line Adafruit LCD with push buttons (ada_radio.py)"
echo "x) Exit"
echo -n "Select version: "

while read ans
do
	if [[ ${ans} == '1' ]]; then
		DAEMON=radiod.py
		TYPE=${LCD}
		break
	elif [[ ${ans} == '2' ]]; then
		DAEMON=radio4.py
		TYPE=${LCD}
		break
	elif [[ ${ans} == '3' ]]; then
		DAEMON=rradiod.py
		TYPE=${LCD}
		break
	elif [[ ${ans} == '4' ]]; then
		DAEMON=rradio4.py
		TYPE=${LCD}
		break
	elif [[ ${ans} == '5' ]]; then
		DAEMON=ada_radio.py
		TYPE=${ADA}
		break
	elif [[ ${ans} == 'x' ]]; then
		exit 0
	else
		echo -n "Select version: "
	fi

done 

echo "Daemon ${DAEMON} selected"

# Update the System V init script
sudo sed -i "s/^NAME=.*/NAME=${DAEMON}/g" ${INIT}
echo

# Pass selected daemon to post install script
exit ${TYPE}

# End of script

