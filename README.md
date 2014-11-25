Raspberry Pi Internet Radio
===========================
Author : Tobias Schlemmer
Email  : keinstein@users.soureforge.net
Github : https://github.com/keinstein/piradio

This program uses Music Player Daemon 'mpd' (untested) or 'mopidy'
(tested) and the python-mpd2 library See http://www.musicpd.org/ Use
"apt-get install mpd mpc python-mpd2" to install the library Modified
to use python-mpd library. See
https://pypi.python.org/pypi/python-mpd2/

This project is based on the Internet Radio project by:
Original Author : Bob Rathbone
Original Site   : http://www.bobrathbone.com
Original Email  : bob@bobrathbone.com
Original Manual : http://www.bobrathbone.com/raspberrypi/Raspberry%20PI%20Radio.pdf
Original Github : https://github.com/bobrathbone/piradio 

For a detailed changelog of earlier versions look at the pages of the original author.

Differences from the original Software
--------------------------------------
- New, modular menu system
- Reduced radio_class
- Usage of the idle command
- Support for Piface Control & Display
- No other boards supported yet
- Optimized for mopidy and he musicbox project
- Supports Mopidys TuneIn plugin
- IR remote control support
- More flexible Debian Package

TODO
----
- further abstractions in order to support other LCD designs (e.g. 4 lines)
- Other board drivers
- Test and implement features I did not use so far.

License
-------
GNU V3, See https://www.gnu.org/copyleft/gpl.html

Disclaimer 
----------
Software is provided as is and absolutly no warranties are implied or given.
The authors shall not be liable for any loss or damage however caused.


