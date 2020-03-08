#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# 开启服务的IP和端口
IP = '127.0.0.1'
PORT = '5555'

# 主机（服务端）IP和端口
SERVER_IP = '127.0.0.1'
SERVER_PORT = '5556'

# influxdb数据库
INFLUX_IP = '127.0.0.1'
INFLUX_PORT = '8086'
INFLUX_USERNAME = 'root'
INFLUX_PASSWORD = '123456'
INFLUX_DATABASE = 'test'

# 监控端口的线程池大小
THREAD_NUM = 5

# 日志相关配置
LEVEL = 'INFO'      # 日志级别
BACKUP_COUNT = 30   # 日志保存个数
LOG_PATH = 'logs'   # 日志保存路径

# 监控相关配置
INTERVAL = 1      # 执行监控命令的时间间隔，单位：秒
SLEEPTIME = 3     # 暂停时间间隔，当命令执行失败时等待的时间间隔，单位：秒
ERROR_TIMES = 5   # 连续执行监控命令失败的次数，如果大于设置值，则停止监控
IS_JVM_ALERT = False     # 当FGC频率过高时，是否发送邮件提醒；True or False
FGC_FREQUENCY = 3600     # FGC频率允许的最大值，默认为 1次/3600s，即3600秒fgc一次
IS_MEM_ALERT = False     # 当服务器剩余内存过低时，是否发送邮件提醒；True or False
MIN_MEM = 0.2            # 服务器剩余内存允许的最小值，单位：G
ECHO = 0    # 当剩余内存过低时，是否清理缓存；0为不清理，1为清理page caches，2为清理dentries和inodes caches，3为清理1和2
