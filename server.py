#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Start command: nohup python3 server.py &
# For more information, please read `README.md`.

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


# start monitor
# http://127.0.0.1:5555/startMonitor?isRun=1&type=port&num=9999
@server.route('/startMonitor', methods=['get'])
def startMonitor():
    try:
        is_run = int(request.args.get('isRun'))

        if request.args.get('type') and request.args.get('num'):
            if request.args.get('type') == 'port':
                port = request.args.get('num')
                pid = port_to_pid(port)     # `port` to `pid`
                if pid is None:
                    return cfg.HTML.format(cfg.ERROR.format('Error: The pid of {} is not existed.'.format(port)))

                if is_run == 0:
                    if port in permon.stop['port']:
                        permon.stop = {'port': port, 'pid': pid, 'is_run': 0}   # stop monitor
                        return cfg.HTML.format(cfg.ERROR.format(
                            'Stop monitor successfully, the port is {}, the pid is {} .'.format(port, pid)))
                    else:
                        return cfg.HTML.format(cfg.ERROR.format('Warning: Please monitor {} firstly.'.format(port)))

                if is_run == 1:
                    permon.start = {'port': port, 'pid': pid, 'is_run': 1}  # start monitor
                    return cfg.HTML.format(cfg.ERROR.format(
                        'Start monitor successfully, the port is {}, the pid is {} .'.format(port, pid)))

            if request.args.get('type') == 'pid':
                return cfg.HTML.format(cfg.ERROR.format('This request is not supported'))

        else:
            return cfg.HTML.format(cfg.ERROR.format('This request is not supported'))

    except Exception as err:
        html = cfg.ERROR.format(traceback.format_exc())
        logger.error(err)
        return cfg.HTML.format(html)


# plot figure
# http://127.0.0.1:5555/plotMonitor?type=port&num=9999&startTime=2019-10-01 10:00:00&duration=3600&system=1&showIO=1
@server.route('/plotMonitor', methods=['get'])
def plotMonitor():
    start_time = None
    duration = None
    system = None
    is_io = True
    try:
        if request.args.get('startTime'):   # start time
            start_time = str(request.args.get('startTime'))

        if request.args.get('duration'):    # duration
            duration = int(request.args.get('duration'))

        if request.args.get('showIO'):      # show IO, for port or pid
            is_io = False

        if request.args.get('type') == 'port':
            port = request.args.get('num')
            pid = port_to_pid(port)

            if start_time is None:
                start_time = permon.stop['startTime'][permon.stop['port'].index(port)]

            if port and pid:
                html = draw_data_from_mysql(port=f'port_{port}', pid=f'pid_{pid}', start_time=start_time,
                                            duration=duration, is_io=is_io)
                return html
            else:
                return json.dumps({'code': -1, 'message': 'The PID is not existed.'}, ensure_ascii=False)

        if request.args.get('type') == 'pid':
            pid = request.args.get('num')

            if start_time is None:
                start_time = permon.stop['startTime'][permon.stop['pid'].index(pid)]

            html = draw_data_from_mysql(pid=f'pid_{pid}', start_time=start_time, duration=duration, is_io=is_io)
            return html

        # plot system
        if request.args.get('system'):
            system = int(request.args.get('system'))

        html = draw_data_from_mysql(start_time=start_time, duration=duration, system=system)
        return html

    except Exception as err:
        htmls = cfg.ERROR.format(traceback.format_exc())
        logger.error(err)
        return cfg.HTML.format(htmls)


# get list of monitoring
# http://127.0.0.1:5555/getMonitorList?type=1
@server.route('/getMonitorList', methods=['get'])
def getMonitorList():
    if request.args.get('type'):
        flag = 0    # show all port
    else:
        flag = 1    # show monitoring port

    msg = permon.start
    status = ['Stopped', 'Monitoring', 'Queuing']

    lines = []
    HTML = '<html><meta http-equiv="Content-Type";content="text/html";charset="utf-8"><body>{}</body></html>'
    p1 = '<h2 align="center">The size of thread pool is {}, current active thread number ' \
         'is {}.</h2>'.format(cfg.THREAD_NUM, msg['isRun'].count(1))
    TABLE = '<table width="50%" border="1" cellspacing="0" cellpadding="6" align="center">{}</table>'
    table_head = f'<tr bgcolor="#99CCFF" align="center"><th width=20%>PORT</th><th width=20%>PID</th>' \
        f'<th width=25%>Status</th><th width=35%>startTime</th></tr>'
    for i in range(len(msg['port'])):
        if flag:
            lines.append(f"<tr align='center'><td>{msg['port'][i]}</td><td>{msg['pid'][i]}</td>"
                         f"<td>{status[msg['isRun'][i]]}</td><td>{msg['startTime'][i]}</td></tr>")
        else:
            if msg['isRun'][i] == 1:
                lines.append(f"<tr align='center'><td>{msg['port'][i]}</td><td>{msg['pid'][i]}</td>"
                             f"<td>{status[msg['isRun'][i]]}</td><td>{msg['startTime'][i]}</td></tr>")

    return HTML.format(p1 + TABLE.format(table_head + ''.join(lines)))


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # start flask server
