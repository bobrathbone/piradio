#!/bin/bash
# $Id: build.sh,v 1.9 2014/06/18 06:50:03 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

PKGDEF=piradio
PKG=radiod
VERSION=$(grep ^Version: piradio | awk '{print $2}')
ARCH=$(grep ^Architecture: piradio | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb

# Tar build files
BUILDFILES="piradio piradio.postinst  piradio.postrm  piradio.preinst"
BUILDTAR=piradio_build.tar.gz
tar -cvzf ${BUILDTAR} ${BUILDFILES} > /dev/null

echo "Building package ${PKG} version ${VERSION}"
echo "from input file ${PKGDEF}"
sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
equivs-build ${PKGDEF}
if [[ $? -ne 0 ]]; then # Don't seperate from above line
	exit 1
fi

echo -n "Check using Lintian y/n: "
read ans
if [[ ${ans} == 'y' ]]; then
	echo "Checking package ${DEBPKG} with lintian"
	lintian ${DEBPKG}
	if [[ $? = 0 ]]
	then
	    dpkg -c ${DEBPKG}
	    echo "Package ${DEBPKG} OK"
	else
	    echo "Package ${DEBPKG} has errors"
	fi
fi

# End of build script
