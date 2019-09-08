#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Start command: nohup python3 server.py &
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

# 开启多线程
t = [threading.Thread(target=permon.write_cpu_mem, args=()),
     threading.Thread(target=permon.write_io, args=())]

for i in range(len(t)):
    t[i].start()


# 开始监控
# http://127.0.0.1:5555/runMonitor?isRun=1&type=pid&num=23121&totalTime=3600
@server.route('/runMonitor', methods=['get'])
def runMonitor():
    try:
        port = ''
        pids = ''
        ports = []
        is_run = int(request.args.get('isRun'))
        if is_run == 0:     # 如果is_run为0，则停止监控
            permon.is_run = 0
            return json.dumps({'code': 0, 'message': 'Success.'}, ensure_ascii=False)

        if is_run == 1:
            if permon.is_run == 1:      # 如果is_run已经是1了，则提示先停止监控，避免页面重复刷新出现异常
                return json.dumps({'code': -1, 'message': 'Please stop monitor first.'}, ensure_ascii=False)

        # 如果传入的是端口号，则需要转换成进程号
        if request.args.get('type') == 'port':
            port = request.args.get('num')
            ports = port.split(',')
            pids = ports_to_pids(ports)

        # 如果传入的是进程号
        if request.args.get('type') == 'pid':
            pid = request.args.get('num')
            pids = pid.split(',')

        # 是否传入监控总时间
        if request.args.get('totalTime'):
            total_time = int(request.args.get('totalTime'))
        else:
            total_time = 66666666       # 如果监控时不传入监控时长，则默认此时长

        # 如果pids为str类型，说明端口号转进程号出现异常，进程可能不存在
        if isinstance(pids, str):
            return json.dumps({'code': -1, 'message': f'The pid of {pids} is not existed.'}, ensure_ascii=False)

        permon.pid = pids
        permon.port = ports
        permon.total_time = total_time
        permon.is_run = is_run
        logger.logger.info('Start monitor.')

        # 将开始监控的时间以追加写入的方式写到文件里
        with open(cfg.START_TIME, 'a') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S') + '\n')

        res = {'code': 0, 'message': {'port': port, 'pid': ','.join(permon.pid), 'total_time': total_time, 'startTime': time.strftime('%Y-%m-%d %H:%M:%S')}}
        return json.dumps(res, ensure_ascii=False)
    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(html)


# 画监控结果图
# http://127.0.0.1:5555/plotMonitor?type=pid&num=23121
@server.route('/plotMonitor', methods=['get'])
def plotMonitor():
    start_time = None
    duration = None
    system = None
    try:
        # 画图开始时间
        if request.args.get('startTime'):
            start_time = str(request.args.get('startTime'))

        # 画图时长
        if request.args.get('duration'):
            duration = int(request.args.get('duration'))

        if request.args.get('type') == 'port':      # 如果是端口号
            port = request.args.get('num')
            pid = port_to_pid(port)     # 端口号转换成进程号

            if port and pid:
                html = draw_data_from_mysql(port=f'port_{port}', pid=f'pid_{pid}', start_time=start_time, duration=duration)
                return html
            else:
                return json.dumps({'code': -1, 'message': 'The PID is not existed.'}, ensure_ascii=False)

        if request.args.get('type') == 'pid':       # 如果是进程号
            pid = request.args.get('num')
            html = draw_data_from_mysql(pid=f'pid_{pid}', start_time=start_time, duration=duration)
            return html

        # 画系统资源使用情况
        if cfg.IS_MONITOR_SYSTEM:
            if request.args.get('system'):
                system = int(request.args.get('system'))

            html = draw_data_from_mysql(start_time=start_time, duration=duration, system=system)
            return html
        else:
            return json.dumps({'code': -1, 'message': 'The current setting is not to monitor system resources.'}, ensure_ascii=False)

    except Exception as err:
        htmls = cfg.ERROR.format(traceback.format_exc())
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        return cfg.HTML.format(htmls)


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # 开启服务
