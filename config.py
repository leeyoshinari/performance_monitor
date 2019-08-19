#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# server
IP = '127.0.0.1'
PORT = '5555'

# monitor config
LEVEL = 'INFO'  # log level
BACKUP_COUNT = 7    # log backup counter
LOG_PATH = 'logs'   # log path

INTERVAL = 0.5
SLEEPTIME = 3   # interval, when stopping monitor, polling to start monitor when satisfying condition.

IS_IO = True    # Whether monitoring IO
IS_HANDLE = False   # Whether monitoring handles

DISK = 'device1'   # Which disk your application runs.

START_TIME = 'startTime.txt'
FGC_TIMES = 'FullGC.txt'

# html
HTML = '<html><body>{}</body><html>'
ERROR = '<p style="color:red">{}</p>'
HEADER = '<div id="header"><h2 align="center">Performance Monitor (pid={})</h2></div>'
ANALYSIS = '<div id="container" style="width:730px; margin:0 auto">{}</div>'
