#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Start command: nohup python -u server.py > server.log 2>&1 &
# For more information, please read `README.md`.

import json
import traceback
import threading
from flask import Flask, request

import config as cfg
from logger import logger
from draw_performance import draw_data_from_mysql, delete_database
from performance_monitor import PerMon
from extern import port_to_pid, ports_to_pids

server = Flask(__name__)
permon = PerMon()

# start multithreading
t = []
t.append(threading.Thread(target=permon.write_cpu_mem, args=()))
if cfg.IS_IO:
    t.append(threading.Thread(target=permon.write_io, args=()))
if cfg.IS_HANDLE:
    t.append(threading.Thread(target=permon.write_handle, args=()))

for i in range(len(t)):
    t[i].start()


# start monitor
# http://127.0.0.1:5555/startMonitor?isRun=2&type=pid&num=23121&totalTime=3600
@server.route('/startMonitor', methods=['get'])
def startMonitor():
    try:
        port = None
        pids = ''
        is_run = int(request.args.get('isRun'))
        if is_run == 1 or is_run == 2:
            if permon.is_run == 1 or permon.is_run == 2:
                return json.dumps({'code': -1, 'message': 'Please stop monitor first.'}, ensure_ascii=False)

        if is_run == 1:
            delete_database()

        if request.args.get('type') == 'port':
            port = request.args.get('num')
            pids = ports_to_pids(port)
        if request.args.get('type') == 'pid':
            pid = request.args.get('num')
            pids = pid.split(',')
        total_time = int(request.args.get('totalTime'))
        if isinstance(pids, str):
            return json.dumps({'code': -1, 'message': f'The pid of {pids} is not existed.'}, ensure_ascii=False)
        permon.pid = pids
        permon.total_time = total_time
        permon.is_run = is_run

        res = {'code': 0, 'message': {'port': port, 'pid': ','.join(permon.pid), 'total_time': total_time}}
        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(html)


# stop monitor
# http://127.0.0.1:5555/stopMonitor?isRun=0
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
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(html)


# plotting
# http://127.0.0.1:5555/plotMonitor?type=pid&num=23121
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
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(htmls)


# drop table from MySQL.
# http://127.0.0.1:5555/dropTable
@server.route('/dropTable', methods=['get'])
def dropTable():
    try:
        delete_database()
        res = {'code': 0, 'message': 'success'}
        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(html)


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # run server
