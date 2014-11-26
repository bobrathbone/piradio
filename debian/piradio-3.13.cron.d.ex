#
# Regular cron jobs for the piradio-3.13 package
#
0 4	* * *	root	[ -x /usr/bin/piradio-3.13_maintenance ] && /usr/bin/piradio-3.13_maintenance
