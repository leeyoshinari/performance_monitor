#---!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# 启动命令 nohup python -u server.py > server.log 2>&1 &
import os
import json
from flask import Flask, request
from draw_performance import draw_data_from_mysql, delete_database
from performance_monitor import PerMon

server = Flask(__name__)


# 开始监控系统cpu和内存占用情况
@server.route('/startMonitor', methods=['get'])
def startMonitor():
    flag = int(request.args.get('is_start'))
    if flag:
        perform = PerMon(request.args.get('PID'), request.args.get('total_time'), request.args.get('interval'),
                         request.args.get('ip'), request.args.get('username'), request.args.get('password'),
                         request.args.get('database_name'))
        perform.run()

        del perform


# 停止监控
@server.route('/stopMonitor', methods=['get'])
def stopMonitor():
    flag = int(request.args.get('is_stop'))
    if flag:
        os.popen('kill -9 {}'.format(request.args.get('PID')))

        res = {'code': 0, 'data': '操作成功'}
        return json.dumps(res, ensure_ascii=False)


# 获取性能监控的结果
@server.route('/getCpuAndMem', methods=['get'])
def getCpuAndMem():
    html = read_data_from_mysql(request.args.get('ip'), request.args.get('username'),
                                request.args.get('password'), request.args.get('database_name'),
                                request.args.get('PID'), request.args.get('times'))
    return html


# 删除性能监控的数据库表
@server.route('/dropTable', methods=['get'])
def dropTable():
    delete_database(request.args.get('ip'), request.args.get('username'),
                    request.args.get('password'), request.args.get('database_name'))

    res = {'code': 0, 'data': '操作成功'}
    return json.dumps(res, ensure_ascii=False)


server.run(port='5555', debug=True, host='127.0.0.1')  # 启动服务
