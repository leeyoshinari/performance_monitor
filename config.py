#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# server
IP = '127.0.0.1'
PORT = '5555'

# monitor config
LEVEL = 'INFO'      # log level
BACKUP_COUNT = 7    # log backup counter
LOG_PATH = 'logs'   # log path

INTERVAL = 0.5  # interval, run command interval.
SLEEPTIME = 3   # interval, when stopping monitor, polling to start monitor when satisfying condition.
ERROR_TIMES = 5     # times, number of running command. When equal, automatically stopped monitor.

IS_MONITOR_SYSTEM = True    # Whether to monitor system's CPU and Memory.
IS_MEM_ALERT = True     # Whether to alert when memory is too low. Alert by sending email.
MIN_MEM = 1             # Minxium memory, uint: G
IS_CLEAR_CACHE = True   # Whether to clear cache when memory is too low.
# 0: don't clear cache, 1: clear page caches, 2: clear dentries and inodes caches, 3: include 1 and 2;
# echo 1 >/proc/sys/vm/drop_caches
ECHO = 0

IS_SEND_RESULT = True       # Whether to send monitoring results periodically.
SEND_INTERVAL = 3600        # Interval, send results interval.

SMTP_SERVER = 'smtp.sina.com'       # SMTP server
SENDER_NAME = '张三'          # sender name
SENDER_EMAIL = 'zhangsan@qq.com'        # sender's email
PASSWORD = 'UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09'       # email password, base64 encode.
RECEIVER_NAME = 'baidu_all'     # receiver name
RECEIVER_EMAIL = ['zhangsan@qq.com', 'zhangsi@qq.com']    # receiver's email

IS_IO = True    # Whether to monitor IO
IS_HANDLE = False   # Whether to monitor handles

DISK = 'device1'   # Which disk your application runs

START_TIME = 'startTime.txt'
FGC_TIMES = 'FullGC.txt'

# html
HTML = '<html><body>{}</body><html>'
ERROR = '<p style="color:red">{}</p>'
HEADER = '<div id="header"><h2 align="center">Performance Monitor (pid={})</h2></div>'
ANALYSIS = '<div id="container" style="width:730px; margin:0 auto">{}</div>'
