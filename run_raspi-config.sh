#!/bin/bash
# Radio daemon post install script 2
# $Id: run_raspi-config.sh,v 1.4 2017/07/14 08:03:42 bob Exp $

TYPE=$1 # No instructions before this line

I2C=4   # Uses I2C libraries
CAD=5   # PiFace control and display

echo "The installation will now run the raspi-config cofiguration program!"
echo "When it runs select Interfacing options"

if [[ ${TYPE} -eq ${CAD} ]]; then
	echo "and enable automatic loading of the SPI kernel module"
elif [[ ${TYPE} -eq ${I2C} ]]; then
	echo "and enable automatic loading of the I2C kernel module"
fi
	
echo -n "Enter y to continue or x to exit: "
read ans
if [[ ${ans} == 'x' ]]; then
        echo "Installation stopped"
        exit 0
fi
/usr/bin/raspi-config


exit 0
