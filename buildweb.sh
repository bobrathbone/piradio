#!/bin/bash
# $Id: buildweb.sh,v 1.1 2014/06/01 10:20:50 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

PKG=radiodweb
VERSION=$(grep ^Version: ${PKG} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKG} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb

# Tar build files
BUILDFILES="radiodweb radioweb.postinst"
BUILDTAR=piradio_web_build.tar.gz
tar -cvzf ${BUILDTAR} ${BUILDFILES} > /dev/null

echo "Building package ${PKG} version ${VERSION}"
echo "from input file ${PKG}"
sudo chown pi:pi *.py
sudo chmod +x *.py
equivs-build ${PKG}

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
