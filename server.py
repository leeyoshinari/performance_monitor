#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Start command: nohup python server.py &
# For more information, please read `README.md`.

import time
import json
import traceback
import threading
from flask import Flask, request

import config as cfg
from logger import logger
from draw_performance import draw_data_from_mysql
from performance_monitor import PerMon
from extern import port_to_pid, ports_to_pids

server = Flask(__name__)
permon = PerMon()

# start multithreading
t = [threading.Thread(target=permon.write_cpu_mem, args=())]
if cfg.IS_IO:
    t.append(threading.Thread(target=permon.write_io, args=()))
if cfg.IS_HANDLE:
    t.append(threading.Thread(target=permon.write_handle, args=()))

for i in range(len(t)):
    t[i].start()


# start monitor
# http://127.0.0.1:5555/startMonitor?isRun=2&type=pid&num=23121&totalTime=3600
@server.route('/runMonitor', methods=['get'])
def runMonitor():
    try:
        port = None
        pids = ''
        ports = []
        is_run = int(request.args.get('isRun'))
        if is_run == 0:
            permon.is_run = 0
            return json.dumps({'code': 0, 'message': 'Success.'}, ensure_ascii=False)

        if is_run == 1:
            if permon.is_run == 1:
                return json.dumps({'code': -1, 'message': 'Please stop monitor first.'}, ensure_ascii=False)

        if request.args.get('type') == 'port':
            port = request.args.get('num')
            ports = port.split(',')
            pids = ports_to_pids(ports)
        if request.args.get('type') == 'pid':
            pid = request.args.get('num')
            pids = pid.split(',')
        total_time = int(request.args.get('totalTime'))
        if isinstance(pids, str):
            return json.dumps({'code': -1, 'message': f'The pid of {pids} is not existed.'}, ensure_ascii=False)

        permon.pid = pids
        permon.port = ports
        permon.total_time = total_time
        permon.is_run = is_run
        logger.logger.info('Start monitor.')

        with open('startTime.txt', 'a') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S') + '\n')

        res = {'code': 0, 'message': {'port': port, 'pid': ','.join(permon.pid), 'total_time': total_time, 'startTime': time.strftime('%Y-%m-%d %H:%M:%S')}}
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


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # run server
