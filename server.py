#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# 启动命令 nohup python -u server.py > server.log 2>&1 &
import json
import traceback
import threading
from flask import Flask, request
import config as cfg
from draw_performance import draw_data_from_mysql, delete_database
from performance_monitor import PerMon
from extern import port_to_pid, ports_to_pids

server = Flask(__name__)
permon = PerMon()

t = []
t.append(threading.Thread(target=permon.write_cpu_mem, args=()))
t.append(threading.Thread(target=permon.write_io, args=()))
# t.append(threading.Thread(target=permon.write_handle, args=()))

for i in range(2):
    t[i].start()


# 开始监控系统cpu和内存占用情况
@server.route('/startMonitor', methods=['get'])
def startMonitor():
    try:
        is_run = int(request.args.get('isRun'))
        if is_run == 1 or is_run == 2:
            if permon.is_run == 1 or permon.is_run == 2:
                return json.dumps({'code': -1, 'message': 'Please stop monitor first.'}, ensure_ascii=False)

        if is_run == 1:
            delete_database()

        port = str(request.args.get('port'))
        total_time = int(request.args.get('totalTime'))
        permon.total_time = total_time
        pids = ports_to_pids(port)
        if isinstance(pids, str):
            return json.dumps({'code': -1, 'message': 'The pid of {} is not existed.'.format(pids)}, ensure_ascii=False)
        permon.pid = pids
        permon.is_run = is_run

        res = {'code': 0, 'message': {'port': port, 'pid': ','.join(permon.pid), 'total_time': total_time}}
        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        return cfg.HTML.format(html)


# 停止监控
@server.route('/stopMonitor', methods=['get'])
def stopMonitor():
    try:
        is_run = int(request.args.get('isRun'))
        if is_run == 0:
            permon.is_run = is_run
            res = {'code': 0, 'message': 'success'}
        else:
            res = {'code': -1, 'message': 'isRun must be 0'}

        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        return cfg.HTML.format(html)


# 获取性能监控的结果
@server.route('/plotMonitor', methods=['get'])
def plotMonitor():
    start_time = None
    duration = None
    pid = None
    try:
        if request.args.get('type') == 'port':
            pid = port_to_pid(request.args.get('num'))
        if request.args.get('type') == 'pid':
            pid = request.args.get('num')

        if request.args.get('startTime'):
            start_time = str(request.args.get('startTime'))
        if request.args.get('duration'):
            duration = int(request.args.get('duration'))

        if pid:
            html = draw_data_from_mysql(pid, start_time, duration)
            return html
        else:
            return json.dumps({'code': -1, 'message': 'The PID is not existed.'}, ensure_ascii=False)
    except Exception as err:
        htmls = cfg.ERROR.format(traceback.format_exc())
        return cfg.HTML.format(htmls)


# 删除性能监控的数据库表
@server.route('/dropTable', methods=['get'])
def dropTable():
    try:
        delete_database()
        res = {'code': 0, 'message': 'success'}
        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        return cfg.HTML.format(html)


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # 启动服务
