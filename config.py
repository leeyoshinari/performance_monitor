#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# server
IP = '127.0.0.1'
PORT = '5555'

# monitor thread number
THREAD_NUM = 5

# monitor config
LEVEL = 'INFO'      # log level
BACKUP_COUNT = 30    # log backup counter
LOG_PATH = 'logs'   # log path

INTERVAL = 1  # interval, run command interval.
SLEEPTIME = 3   # interval, when stopping monitor, polling to start monitor when satisfying condition.
ERROR_TIMES = 5     # times, number of running command. When equal, automatically stopped monitor.

IS_JVM_ALERT = True     # Whether to alert when the frequency of Full GC is too high.
IS_MEM_ALERT = True     # Whether to alert when memory is too low. Alert by sending email.
MIN_MEM = 2             # Minxium memory, uint: G
# 0: don't clear cache, 1: clear page caches, 2: clear dentries and inodes caches, 3: include 1 and 2;
# echo 1 >/proc/sys/vm/drop_caches
ECHO = 0

DISK = 'device1'   # Which disk your application runs

START_TIME = 'startTime.txt'    # Store the time of start monitoring.
FGC_TIMES = 'FullGC.txt'        # Store the time of every FullGC time.

SMTP_SERVER = 'smtp.sina.com'       # SMTP server
SENDER_NAME = '张三'          # sender name
SENDER_EMAIL = 'zhangsan@qq.com'        # sender's email
PASSWORD = 'UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09'       # email password, base64 encode.
RECEIVER_NAME = 'baidu_all'     # receiver name
RECEIVER_EMAIL = ['zhangsan@qq.com', 'zhangsi@qq.com']    # receiver's email

# html
HTML = '<html><body>{}</body><html>'
ERROR = '<p style="color:red">{}</p>'
HEADER = '<div id="header"><h2 align="center">Performance Monitor (pid={})</h2></div>'
ANALYSIS = '<div id="container" style="width:730px; margin:0 auto">{}</div>'
