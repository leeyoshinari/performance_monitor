#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Start command: nohup python3 server.py &
# For more information, please read `README.md`.

import time
import json
import traceback
from flask import Flask, request

import config as cfg
from logger import logger
from draw_performance import draw_data_from_mysql
from performance_monitor import PerMon
from extern import port_to_pid

server = Flask(__name__)
permon = PerMon()
permon.monitor()


# 开始监控
# http://127.0.0.1:5555/runMonitor?isRun=1&type=pid&num=23121
@server.route('/runMonitor', methods=['get'])
def runMonitor():
    try:
        is_run = int(request.args.get('isRun'))

        if request.args.get('type') and request.args.get('num'):
            # 如果传入的是端口号，则需要转换成进程号
            if request.args.get('type') == 'port':
                port = request.args.get('num')
                pid = port_to_pid(port)
                if pid is None:
                    return cfg.HTML.format(cfg.ERROR.format('Error: The pid of {} is not existed.'.format(port)))

                if is_run == 0:
                    if port in permon.stop['port']:
                        permon.stop = {'port': port, 'pid': pid, 'is_run': 0}
                        return cfg.HTML.format(cfg.ERROR.format(
                            'Stop monitor successfully, the port is {}, the pid is {} .'.format(port, pid)))
                    else:
                        return cfg.HTML.format(cfg.ERROR.format('Warning: Please monitor {} firstly.'.format(port)))

                if is_run == 1:
                    permon.start = {'port': port, 'pid': pid, 'is_run': 1}
                    return cfg.HTML.format(cfg.ERROR.format(
                        'Start monitor successfully, the port is {}, the pid is {} .'.format(port, pid)))

            # 如果传入的是进程号
            if request.args.get('type') == 'pid':
                return cfg.HTML.format(cfg.ERROR.format('This request is not supported'))

        else:
            return cfg.HTML.format(cfg.ERROR.format('This request is not supported'))

    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        logger.error(err)
        logger.error(traceback.format_exc())
        return cfg.HTML.format(html)


# 画监控结果图
# http://127.0.0.1:5555/plotMonitor?type=pid&num=23121
@server.route('/plotMonitor', methods=['get'])
def plotMonitor():
    start_time = None
    duration = None
    system = None
    is_io = False
    try:
        # 画图开始时间
        if request.args.get('startTime'):
            start_time = str(request.args.get('startTime'))

        # 画图时长
        if request.args.get('duration'):
            duration = int(request.args.get('duration'))

        if request.args.get('showIO'):
            is_io = True

        if request.args.get('type') == 'port':      # 如果是端口号
            port = request.args.get('num')
            pid = port_to_pid(port)     # 端口号转换成进程号

            if port and pid:
                html = draw_data_from_mysql(port=f'port_{port}', pid=f'pid_{pid}', start_time=start_time,
                                            duration=duration, is_io=is_io)
                return html
            else:
                return json.dumps({'code': -1, 'message': 'The PID is not existed.'}, ensure_ascii=False)

        if request.args.get('type') == 'pid':       # 如果是进程号
            pid = request.args.get('num')
            html = draw_data_from_mysql(pid=f'pid_{pid}', start_time=start_time, duration=duration)
            return html

        # 画系统资源使用情况
        if request.args.get('system'):
            system = int(request.args.get('system'))

        html = draw_data_from_mysql(start_time=start_time, duration=duration, system=system)
        return html

    except Exception as err:
        htmls = cfg.ERROR.format(traceback.format_exc())
        logger.error(err)
        logger.error(traceback.format_exc())
        return cfg.HTML.format(htmls)


@server.route('/getMonitorList', methods=['get'])
def getMonitorList():
    if request.args.get('type') == 1:
        flag = 1    # 显示所有端口
    else:
        flag = 0    # 显示正在监控的端口

    msg = permon.start
    port = msg['port']
    pid = msg['pid']
    is_run = msg['isRun']
    start_time = msg['startTime']

    lines = []
    HTML = '<html><meta http-equiv="Content-Type";content="text/html";charset="utf-8"><body>{}</body></html>'
    p1 = f'<p align="right">The size of thread pool is {cfg.THREAD_NUM}, ' \
        f'current active thread num is {is_run.count(1)}.</p>'
    TABLE = '<table width="100%" border="1" cellspacing="0" cellpadding="6" align="center">{}</table>'
    table_head= f'<tr bgcolor="#99CCFF" align="center"><th width=25%>PORT</th><th width=25%>PID</th>' \
        f'<th width=25%>isRun</th><th width=25%></th>startTime</tr>'
    for i in range(len(port)):
        if flag:
            lines.append(f'<tr><td>{port[i]}</td><td>{pid[i]}</td><td>{is_run[i]}</td><td>{start_time[i]}</td></tr>')
        else:
            if is_run[i]:
                lines.append(f'<tr><td>{port[i]}</td><td>{pid[i]}</td><td>{is_run[i]}</td><td>{start_time[i]}</td></tr>')

    return HTML.format(p1 + TABLE.format(table_head + ''.join(lines)))


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # 开启服务
