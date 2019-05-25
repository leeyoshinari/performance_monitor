#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# 启动命令 nohup python -u server.py > server.log 2>&1 &
import os
import json
import threading
from flask import Flask, request
import config as cfg
from draw_performance import draw_data_from_mysql, delete_database
from performance_monitor import PerMon
from extern import port_to_pid, ports_to_pids

server = Flask(__name__)
permon = PerMon()

t = threading.Thread(target=permon.run, args=())
t.start()


# 开始监控系统cpu和内存占用情况
@server.route('/startMonitor', methods=['get'])
def startMonitor():
    is_run = int(request.args.get('isRun'))
    port = str(request.args.get('port'))
    total_time = int(request.args.get('totalTime'))
    permon.total_time = total_time
    permon.pid = ports_to_pids(port)
    permon.is_run = is_run

    res = {'code': 0, 'data': {'port': port, 'total_time': total_time}}
    return json.dumps(res, ensure_ascii=False)


# 停止监控
@server.route('/stopMonitor', methods=['get'])
def stopMonitor():
    is_run = int(request.args.get('isRun'))
    if is_run == 0:
        permon.is_run = is_run
        res = {'code': 0, 'data': 'success'}
    else:
        res = {'code': -1, 'data': 'isRun must be 0'}
    return json.dumps(res, ensure_ascii=False)


# 获取性能监控的结果
@server.route('/plotMonitor', methods=['get'])
def plotMonitor():
    if request.args.get('type') == 'port':
        pid = port_to_pid(request.args.get('num'))
    if request.args.get('type') == 'pid':
        pid = request.args.get('num')
    try:
        start_time = str(request.args.get('startTime'))
        duration = int(request.args.get('duration'))
    except Exception as err:
        res = {'code': -1, 'data': err}
        return json.dumps(res, ensure_ascii=False)
    html = draw_data_from_mysql(pid, start_time, duration)
    return html


# 删除性能监控的数据库表
@server.route('/dropTable', methods=['get'])
def dropTable():
    try:
        delete_database()
        res = {'code': 0, 'data': 'success'}
    except Exception as err:
        res = {'code': -1, 'data': err}
    return json.dumps(res, ensure_ascii=False)


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # 启动服务
