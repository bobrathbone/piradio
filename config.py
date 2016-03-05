import os
import sys
import ConfigParser
import threading
import traceback

config = None
libconfig = None

package       = 'piradio'
configfile    = '/etc/'+package+'/'+package+'.conf'
srcdir        = '/usr/share/'+package
configlock    = threading.Lock()

configdefaults = {
    'DEFAULT':{
        'package': package
    },
    
    'Paths': {
        'pidfile': '/var/run/'+package+'.pid',
        'playlist': '/var/lib/'+package+'/playlists',
        'mountpoints': '/home/pi/Musik/media'
    },
    'Server': {
        'host': 'localhost',
        'port': '6600',
        'update_database_cmd': '/usr/bin/mopidy local update'
    },
    'Logging': {
        'level' : 'INFO',
        'logfile': '/var/log/'+package+'.log',
        'stdin': '/dev/null',
        'stdout': '/dev/null',
        'stderr': '/dev/null',
    },
    'Settings': {
        'playlist_format' : '%Y-%m-%d_%X',
        'playlist_type': 'm3u',
        'mount_command': "mount -t '{0}' -o user=pi '{1}' '{2}'",
        'umount_command': "umount '{0}'",
        'mount_devices':'/dev/sd*', 
        'mount_label': "/sbin/blkid -s LABEL -o value '{0}'",
        'mount_type': "/sbin/blkid -s TYPE -o value '{0}'",
        'mount_UUID': "/sbin/blkid -s UUID -o value '{0}'",
        'mount_devtypes': 'ext2:ext3:ext4:fat:vfat'
    }
}

libconfigdefaults = {
    'Radio': {
        'current':'1',
        'place_uri':'Radio',
        'place_type':'playlist'
    },
    'Current Track': {
        'type':'radio',
        'path':None,
        'index':0
    },
    'Settings': {
        'volume':75,
        'timer':30,
        'alarm_type':None,
        'alarm_hour':7,
        'alarm_minute':0,
        'streaming':False,
        'random':False,
        'repeat':False,
        'consume':False
    }
}


def load_config(filename,defaults=None):
    configlock.acquire()
    retval = ConfigParser.ConfigParser()
    retval.read(filename)
    configlock.release()
    return retval

def save_config(configobj,filename):
    configlock.acquire()
    cfgfile = open(filename,'w')
    configobj.write(cfgfile)
    cfgfile.flush()
    cfgfile.close()
    configlock.release()

                        
def save_libconfig():
    global libconfig
    # mkdir -p "libdir"
    save_config(libconfig,get("Paths","libconfigfile"))


def get(section, option):
    configlock.acquire()
    if not config.has_section(section): 
        retval = configdefaults[section][option]
    elif not config.has_option(section,option):
        retval = configdefaults[section][option]
    else:
        retval = config.get(section,option)
    configlock.release()
    return retval

def get_boolean(section, option):
    configlock.acquire()
    if not config.has_section(section): 
        retval = configdefaults[section][option]
    elif not config.has_option(section,option):
        retval = configdefaults[section][option]
    else:
        retval = config.getboolean(section,option)
    configlock.release()
    return retval

def libget(section, option):
    configlock.acquire()
    if not libconfig.has_section(section): 
        retval = libconfigdefaults[section][option]
    elif not libconfig.has_option(section,option):
        retval = libconfigdefaults[section][option]
    else:
        retval = libconfig.get(section,option)
    configlock.release()
    return retval

def libget_boolean(section, option):
    configlock.acquire()
    if not libconfig.has_section(section): 
        retval = libconfigdefaults[section][option]
    elif not libconfig.has_option(section,option):
        retval = libconfigdefaults[section][option]
    else:
        retval = libconfig.getboolean(section,option)
    configlock.release()
    return retval

def libset(section, option, value):
    global libconfig
    configlock.acquire()
    if not libconfig.has_section(section): 
        libconfig.add_section(section)
    libconfig.set(section,option,value)
    configlock.release()

config = load_config(configfile)
configdefaults['DEFAULT']['libdir'] = '/var/lib/'+ get("DEFAULT","package")
configdefaults['Paths']['radiodir'] = get("Paths","libdir") + '/radio'
configdefaults['Paths']['stationlist'] = get("Paths","radiodir") \
                                         +'/stationlist'
configdefaults['Paths']['libconfigfile'] = get("Paths",
                                               "libdir")+\
    '/'+get("DEFAULT",'package')+'.conf'

try:
    os.makedirs(get("Paths","libdir"),
                mode=0o755)
except:
    pass

libconfig = load_config(get("Paths","libconfigfile"))
