#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

# 开启服务的IP和端口
IP = '127.0.0.1'
PORT = '8000'

# hbase数据库IP和端口
HBASE_IP = '127.0.0.1'
HBASE_PORT = '6379'

# 日志相关配置
LEVEL = 'INFO'      # 日志级别
BACKUP_COUNT = 30   # 日志保存个数
LOG_PATH = 'logs'   # 日志保存路径

# 邮箱配置
SMTP_SERVER = 'smtp.sina.com'       # SMTP服务器
SENDER_NAME = '张三'                # 发件人名字
SENDER_EMAIL = 'zhangsan@qq.com'    # 发件人邮箱地址
PASSWORD = '123456'                 # 发件人邮箱密码
RECEIVER_NAME = 'baidu_all_group'   # 收件人名字
RECEIVER_EMAIL = ['zhangsan@qq.com', 'zhangsi@qq.com']    # 收件人邮箱地址，列表
