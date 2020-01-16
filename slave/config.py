#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# slave (client)
IP = '127.0.0.1'
PORT = '5555'

# master (server)
SERVER_IP = '127.0.0.1'
SERVER_PORT = '5556'

# hbase
HBASE_IP = '127.0.0.1'
HBASE_PORT = '6379'

# monitor thread number
THREAD_NUM = 5

# monitor config
LEVEL = 'INFO'      # log level
BACKUP_COUNT = 30    # log backup counter
LOG_PATH = 'logs'   # log path

INTERVAL = 1  # interval, run command interval.
SLEEPTIME = 3   # interval, when stopping monitor, polling to start monitor when satisfying condition.
ERROR_TIMES = 5     # times, number of running command. When equal, automatically stopped monitor.

IS_JVM_ALERT = False     # Whether to alert when the frequency of Full GC is too high.
IS_MEM_ALERT = False     # Whether to alert when memory is too low. Alert by sending email.
MIN_MEM = 2             # Minxium memory, uint: G
# 0: don't clear cache, 1: clear page caches, 2: clear dentries and inodes caches, 3: include 1 and 2;
# echo 1 >/proc/sys/vm/drop_caches
ECHO = 0

FGC_TIMES = 'FullGC.txt'    # Store the time of every FullGC time.
