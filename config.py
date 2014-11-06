import os
import sys
import configparser
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
    },
    'Server': {
        'host': 'localhost',
        'port': '6600'
    },
    'Logging': {
        'level' : 'INFO',
        'logfile': '/var/log/'+package+'.log',
        'stdin': '/dev/null',
        'stdout': '/dev/null',
        'stderr': '/dev/null',
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
    retval = configparser.ConfigParser()
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
