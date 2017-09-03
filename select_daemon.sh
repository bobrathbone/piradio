#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: select_daemon.sh,v 1.27 2017/04/15 09:01:02 bob Exp $
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
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

DAEMON=radiod.py

INIT=/etc/init.d/radiod
SERVICE=/lib/systemd/system/radiod.service
BINDIR="\/usr\/share\/radio\/"
DIR=/usr/share/radio
CONFIG=/etc/radiod.conf
PIRADIO_TYPE=/var/lib/radiod/piradio_type

# Display types
LCD=1	# LCD screen (direct)
I2C=2	# Requires I2C libraries
CAD=3	# PiFace Control and Display
NODISPLAY=4	# Retro radio with no display
BACKPACK=0	# Backpack selected 1=yes 0=no

ans=0
while [ $ans == 0 ]
do
	ans=$(whiptail --title "Select wiring version" --menu "Choose your option" 15 75 9 \
	"1" "26 pin version wiring" \
	"2" "40 pin version wiring" \
	"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		echo "26 pin version selected"
		sudo cp -f ${DIR}/radiod.conf ${CONFIG}
	elif [[ ${ans} == '2' ]]; then
		echo "40 pin version selected"
		sudo cp -f ${DIR}/radiod.conf.40_pin ${CONFIG}
	else
		echo "Wiring configuration in ${CONFIG} unchanged"	
	fi
done

# Select the actual radio daemon to run at boot time
selection=1 
while [ $selection != 0 ]
do
	ans=$(whiptail --title "Select radio daemon" --menu "Choose your option" 15 75 9 \
	"1" "Two line LCD with push buttons  (radiod.py)" \
	"2" "Four line LCD with push buttons (radio4.py)" \
	"3" "Two line LCD with rotary encoders  (rradiod.py)" \
	"4" "Four line LCD with rotary encoders (rradio4.py)" \
	"5" "Two line Adafruit LCD with push buttons (ada_radio.py)" \
	"6" "Two line LCD with I2C backpack and rotary encoders (rradiobp.py)" \
	"7" "Four line LCD with I2C backpack and rotary encoders (rradiobp4.py)" \
	"8" "PiFace Control and Display - CAD (radio_piface.py)" \
	"9" "Retro radio with rotary encoders (retro_radio.py)" 3>&1 1>&2 2>&3)

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		DAEMON=radiod.py
		TYPE=${LCD}
		DESC="Two line LCD with buttons"

	elif [[ ${ans} == '2' ]]; then
		DAEMON=radio4.py
		TYPE=${LCD}
		DESC="Four line LCD with buttons"

	elif [[ ${ans} == '3' ]]; then
		DAEMON=rradiod.py
		TYPE=${LCD}
		DESC="Two line LCD with encoders"

	elif [[ ${ans} == '4' ]]; then
		DAEMON=rradio4.py
		TYPE=${LCD}
		DESC="Four line LCD with encoders"

	elif [[ ${ans} == '5' ]]; then
		DAEMON=ada_radio.py
		TYPE=${I2C}
		DESC="AdaFruit LCD"

	elif [[ ${ans} == '6' ]]; then
		DAEMON=rradiobp.py
		TYPE=${I2C}
		BACKPACK=1
		DESC="Two line LCD with I2C backpack"

	elif [[ ${ans} == '7' ]]; then
		DAEMON=rradiobp4.py
		TYPE=${I2C}
		BACKPACK=1
		DESC="Four line LCD with I2C backpack"

	elif [[ ${ans} == '8' ]]; then
		DAEMON=radio_piface.py
		TYPE=${CAD}
		DESC="Piface CAD"

	elif [[ ${ans} == '9' ]]; then
		DAEMON=retro_radio.py
		TYPE=${NODISPLAY}
		DESC="Retro radio no display, "

	fi

	whiptail --title "$DESC ($DAEMON)" --yesno "Is this correct?" 10 60
	selection=$?
done 

echo "Daemon ${DAEMON} selected"

# Update the System V init script
sudo sed -i "s/^NAME=.*/NAME=${DAEMON}/g" ${INIT}

# Update systemd script
sudo sed -i "s/^ExecStart=.*/ExecStart=${BINDIR}${DAEMON} nodaemon/g" ${SERVICE}
sudo sed -i "s/^ExecStop=.*/ExecStop=${BINDIR}${DAEMON} stop/g" ${SERVICE}

# Update system startup 
if [[ -x /bin/systemctl ]]; then
	sudo systemctl daemon-reload
	sudo systemctl enable radiod.service
else
	sudo update-rc.d radiod enable	
fi

# Select the backpack type
if [[ ${BACKPACK} == 1 ]]; then
	sleep 2
	ans=0
	BPTYPE=""
	while [ $ans == 0 ]
	do
		ans=$(whiptail --title "Select backpack type" --menu "Choose I2C backpack" 15 75 9 \
		"1" "ADAFRUIT I2C backpack" \
		"2" "PCF8574 I2C backpack" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0 
		fi

		if [[ ${ans} == '1' ]]; then
			echo "ADAFRUIT I2C backpack selected"
			BPTYPE="ADAFRUIT"
		elif [[ ${ans} == '2' ]]; then
			echo "PCF8574 I2C backpack selected"
			BPTYPE="PCF8574"
		else
			echo "Backpack configuration in ${CONFIG} unchanged"	
		fi
		
		if [[ ${BPTYPE} != "" ]]; then
			sudo sed -i "s/^i2c_backpack=.*/i2c_backpack=${BPTYPE}/g" ${CONFIG}
		fi
	done

fi

echo

# Pass selected daemon type to post install script
echo  ${TYPE} > ${PIRADIO_TYPE}
exit 0

# End of script

