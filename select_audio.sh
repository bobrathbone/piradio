#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: select_audio.sh,v 1.31 2017/01/16 14:02:37 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used to select the sound card to be used.
# It also configures /etc/mpd.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

BOOTCONFIG=/boot/config.txt
MPDCONFIG=/etc/mpd.conf
ASOUNDCONF=/etc/asound.conf
MODPROBE=/etc/modprobe.d/alsa-base.conf
MODULES=/proc/asound/modules

# Audio types
JACK=1	# Audio Jack or Sound Cards
HDMI=2	# HDMI
TYPE=${JACK}

# dtoverlay parameter in /etc/config.txt
DTOVERLAY=""

# Device and Name
DEVICE="0,0"
CARD=0
NAME="Onboard jack"
MIXER="hardware"
NUMID=1

# Wheezy not supported
cat /etc/os-release | grep -i wheezy 2>&1 >/dev/null
if [[ $? == 0 ]]; then 	# Don't seperate from above
	echo "This prograqm is not supported on Debian Wheezy!"
	echo "Exiting program."
	exit 1
fi

# Stop the radio
echo "Stopping the radio"
sudo service radiod stop
sudo service mpd stop

selection=1 
while [ $selection != 0 ]
do
	ans=$(whiptail --title "Select audio output" --menu "Choose your option" 18 75 12 \
	"1" "On-board audio output jack" \
	"2" "HDMI output" \
	"3" "USB DAC" \
	"4" "HiFiBerry DAC" \
	"5" "HiFiBerry DAC plus" \
	"6" "HiFiBerry DAC Digi" \
	"7" "HiFiBerry Amp" \
	"8" "IQAudio DAC" \
	"9" "IQAudio DAC plus and Digi/AMP " \
	"10" "JustBoom DAC/Zero/Amp" \
	"11" "JustBoom Digi HAT/zero" \
	"12" "Manually configure" 3>&1 1>&2 2>&3)

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		DESC="On-board audio output Jack"

	elif [[ ${ans} == '2' ]]; then
		DESC="HDMI output"
		TYPE=${HDMI}
		NUMID=3

	elif [[ ${ans} == '3' ]]; then
		DESC="USB DAC"
		NAME=${DESC}
		DEVICE="1,0"
		CARD=1
		MIXER="software"
		NUMID=6

	elif [[ ${ans} == '4' ]]; then
		DESC="HiFiBerry DAC or Light"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dac"
		MIXER="software"

	elif [[ ${ans} == '5' ]]; then
		DESC="HiFiBerry DAC Plus"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dacplus"
		MIXER="software"

	elif [[ ${ans} == '6' ]]; then
		DESC="HiFiBerry Digi"
		NAME=${DESC}
		DTOVERLAY="hifiberry-digi"
		MIXER="software"

	elif [[ ${ans} == '7' ]]; then
		DESC="HiFiBerry Amp"
		NAME=${DESC}
		DTOVERLAY="hifiberry-amp"
		MIXER="software"

	elif [[ ${ans} == '8' ]]; then
		DESC="IQAudio DAC"
		NAME=${DESC}
		DTOVERLAY="iqaudio-dacplus,unmute_amp"
		MIXER="software"

	elif [[ ${ans} == '9' ]]; then
		DESC="IQAudio DAC plus or DigiAMP"
		NAME="IQAudio DAC+"
		DTOVERLAY="iqaudio-dacplus,unmute_amp"
		MIXER="software"

	elif [[ ${ans} == '10' ]]; then
		DESC="JustBoom DAC/Amp"
		NAME="JustBoom DAC"
		DTOVERLAY="justboom-dac"
		MIXER="software"

	elif [[ ${ans} == '11' ]]; then
		DESC="JustBoom DAC/Amp"
		NAME="JustBoom Digi HAT"
		DTOVERLAY="justboom-digi"
		#DEVICE="1,0"
		MIXER="software"

	elif [[ ${ans} == '12' ]]; then
		DESC="Manual configuration"
	fi

	whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
	selection=$?
done 

echo "${DESC} selected"

# Install alsa-utils if not already installed
PKG="alsa-utils"
dpkg-query --status ${PKG} 2>&1 >/dev/null
if [[ $? != 0 ]]; then 	# Don't seperate from above
	echo "Installing ${PKG} package"
	sudo apt-get --yes install ${PKG}
fi

# Remove pulseaudio package
PKG="pulseaudio"
if [[ -x /usr/bin/${PKG} ]]; then 	# Don't seperate from above
	echo "Removing ${PKG} package"
	sudo apt-get --yes remove ${PKG} 2>&1 >/dev/null
fi

# Select HDMI or audio jack/DACs Alsa output
if [[ ${TYPE} == ${HDMI} ]]; then
	echo "Configuring HDMI as output"
	sudo amixer cset numid=${NUMID} 2 2>&1 >/dev/null
else
	sudo amixer cset numid=3 1 2>&1 >/dev/null
fi

# Configure the Alsa sound mixer for maximum volume
amixer cset numid=1 100% 2>&1 >/dev/null
if [[ $? != 0 ]]; then 	# Don't seperate from above
	echo "Failed to configure Alsa mixer"
fi

# Set up asound configuration for espeak and aplay
echo "Configuring card ${CARD} for aplay (${ASOUNDCONF})"
if [[ ! -f ${ASOUNDCONF} ]]; then
	sudo cp -f asound.conf.dist ${ASOUNDCONF}
fi

if [[ ${CARD} == 0 ]]; then
        sudo sed -i -e "0,/card/s/1/0/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/1,0/0,0/" ${ASOUNDCONF}
else
        sudo sed -i -e "0,/card/s/0/1/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/0,0/1,0/" ${ASOUNDCONF}
fi

# Save original configuration 
if [[ ! -f ${MPDCONFIG}.orig ]]; then
	sudo cp -f -p ${MPDCONFIG} ${MPDCONFIG}.orig
fi

# Configure name device and mixer type in mpd.conf
sudo cp -f -p ${MPDCONFIG}.orig ${MPDCONFIG}
sudo sed -i -e "0,/^\sname/{s/\sname.*/\tname\t\t\"${NAME}\"/}" ${MPDCONFIG}
sudo sed -i -e "0,/device/{s/.*device.*/\tdevice\t\t\"hw:${DEVICE}\"/}" ${MPDCONFIG}
sudo sed -i -e "0,/mixer_type/{s/.*mixer_type.*/\tmixer_type\t\"${MIXER}\"/}" ${MPDCONFIG}

# Save all new alsa settings
sudo alsactl store
if [[ $? != 0 ]]; then 	# Don't seperate from above
	echo "Failed to alsa settings"
fi

# Bind address  to any
sudo sed -i -e "0,/bind_to_address/{s/.*bind_to_address.*/bind_to_address\t\t\"any\"/}" ${MPDCONFIG}

# Delete existing dtoverlays
sudo sed -i '/dtoverlay=iqaudio/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=hifiberry/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=justboom/d' ${BOOTCONFIG}

# Add dtoverlay for sound cards
if [[ ${DTOVERLAY} != "" ]]; then
	TEMP="/tmp/awk$$"
	sudo awk -v s="dtoverlay=${DTOVERLAY}" '/^dtoverlay/{f=1;$0=s}7;END{if(!f)print s}' ${BOOTCONFIG} > ${TEMP}
	sudo cp -f ${TEMP} ${BOOTCONFIG}
	sudo rm -f ${TEMP}
	dtcommand=$(echo ${DTOVERLAY} | sudo sed 's/\,/ /' )
	sudo dtoverlay -v ${dtcommand}
	sudo dtparam audio=off
	sudo sed -i -e "/^dtparam=audio=/{s/on/off/}" ${BOOTCONFIG}
else 	
	sudo sed -i -e "/^dtparam=audio=/{s/off/on/}" ${BOOTCONFIG}
	sudo dtparam audio=on
fi

# Configure the Alsa sound mixer on second card for 100 volume
# This must be done after the dtoverlay command above
aplay -l | grep "card 1"  2>&1 >/dev/null
if [[ $? == 0 ]]; then 	# Don't seperate from above
	amixer -c1 cset numid=${NUMID} 100% 2>&1 >/dev/null
	if [[ $? != 0 ]]; then 	# Don't seperate from above
		echo "Failed to configure second Alsa mixer"
	fi
else
	amixer -c0 cset numid=${NUMID} 100% 2>&1 >/dev/null
	if [[ $? != 0 ]]; then 	# Don't seperate from above
		echo "Failed to configure first Alsa mixer"
	fi
fi

echo "${DESC} configured"
sleep 2

# Reboot dialogue
if (whiptail --title "Audio selection" --yesno "Reboot Raspberry Pi (Recommended)" 10 60) then
	echo "Rebooting Raspberry Pi"
	sudo reboot 
else
	echo
	echo "You chose not to reboot!"
	echo "Changes made will not become active until the next reboot"
fi

# End of script

