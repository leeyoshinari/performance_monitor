#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import base64
import time
import glob
import traceback
import datetime
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

import config as cfg
from logger import logger
from extern import DealLogs


def draw_data_from_mysql(port, pid, start_time=None, duration=None):
    """
    Read data from MySQL.
    Return html included plotting, and data.
    """
    search = 0
    pid_num = int(pid.split('_')[-1])

    if port:
        search = port
    elif pid:
        search = pid

    logs = glob.glob(cfg.LOG_PATH + '/*.log')  # 获取所有日志

    deal_logs = DealLogs(search)

    try:
        if start_time and duration:
            # 将开始时间和结果时间转换成1970纪元后经过的浮点秒数
            startTime = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple())
            endTime = startTime + duration
            deal_logs.read_data_from_logs(logs, startTime, endTime)      # 从日志中获取数据
        else:
            deal_logs.read_data_from_logs(logs)

        start_time = time.mktime(datetime.datetime.strptime(str(deal_logs.total_time[0]), '%Y-%m-%d %H:%M:%S').timetuple())
        end_time = time.mktime(datetime.datetime.strptime(str(deal_logs.total_time[-1]), '%Y-%m-%d %H:%M:%S').timetuple())

        # 画图
        image_html = draw(deal_logs.cpu_and_mem[0], deal_logs.cpu_and_mem[1:3], deal_logs.io, deal_logs.handles, end_time - start_time)
        # 计算百分位数
        per_html = get_lines(deal_logs.cpu_and_mem[0], deal_logs.io[2], deal_logs.io[5])
        # 获取java应用垃圾回收相关数据
        gc_html = get_gc(pid_num)
        # 将所有数据组装成html
        html = cfg.HTML.format(cfg.HEADER.format(pid_num) + image_html + cfg.ANALYSIS.format(per_html + gc_html))
        del deal_logs

        return html
    except Exception as err:
        del deal_logs
        logger.logger.error(err)
        logger.logger.error(traceback.format_exc())
        raise Exception(err)


def draw(cpu, mem, IO, handles, total_time):
    """
        画图
    """
    if cfg.IS_IO:
        fig = plt.figure('figure', figsize=(20, 15))
        ax1 = plt.subplot(3, 1, 1)
        ax2 = plt.subplot(3, 1, 2)
        ax3 = plt.subplot(3, 1, 3)
    elif cfg.IS_HANDLE:
        fig = plt.figure('figure', figsize=(20, 20))
        ax1 = plt.subplot(4, 1, 1)
        ax2 = plt.subplot(4, 1, 2)
        ax3 = plt.subplot(4, 1, 3)
        ax4 = plt.subplot(4, 1, 4)
    else:
        fig = plt.figure('figure', figsize=(20, 10))
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)

    plt.sca(ax1)
    plt.plot(cpu, color='r')
    plt.grid()
    plt.xlim(0, len(cpu))
    plt.ylim(0, 100)
    plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(max(cpu), np.mean(cpu), np.floor(total_time / 3600)), size=12)
    plt.margins(0, 0)

    plt.sca(ax2)
    plt.plot(mem[0], color='r', label='Memory')

    if sum(mem[1]) == 0:
        plt.title('Memory(G) max:{:.2f}G, duration:{:.1f}h'.format(max(mem[0]), np.floor(total_time / 3600)), size=12)
    else:
        plt.plot(mem[1], color='b', label='JVM')
        plt.legend(loc='upper right')
        plt.title('Memory(G) max:{:.2f}G, JVM(G) max:{:.2f}G, duration:{:.1f}h'.format(max(mem[0]), max(mem[1]), np.floor(total_time / 3600)), size=12)

    plt.grid()
    plt.xlim(0, len(mem[0]))
    plt.ylim(0, max(mem[0]) + 1)
    plt.margins(0, 0)

    if cfg.IS_IO:
        plt.sca(ax3)
        plt.plot(IO[3], color='black', label='rkB/s')
        plt.plot(IO[4], color='b', label='wkB/s')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(IO[3]))
        plt.ylim(0, max(max(IO[3]), max(IO[4])))
        plt.title('IO, max:{:.2f}%, duration:{:.1f}h'.format(max(IO[5]), np.floor(total_time / 3600)), size=12)
        plt.margins(0, 0)

        ax_util = ax3.twinx()
        plt.sca(ax_util)
        plt.plot(IO[5], color='red', label='%util')
        plt.legend(loc='upper right')
        plt.ylim(0, max(IO[5]))

    if cfg.IS_HANDLE:
        plt.sca(ax4)
        plt.plot(handles, color='r')
        plt.grid()
        plt.xlim(0, len(handles))
        plt.ylim(0, max(handles) + 10)
        plt.title('Handle, max:{}, duration:{:.1f}h'.format(int(max(handles)), np.floor(total_time / 3600)), size=12)
        plt.margins(0, 0)

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')      # 把图片保存成二进制格式
    data = base64.encodebytes(image_byte.getvalue()).decode()       # 编码成base64格式

    html = f'<div align="center"><img src="data:image/png;base64,{data}" /></div>'
    plt.close()     # 关闭绘图窗口
    return html


def get_lines(cpu, util, dutil):
    """
        计算百分位数，75%line、90%line、95%line、99%line
    """
    # 从小到大排序
    cpu.sort()
    dutil.sort()

    if cfg.IS_IO:
        line75 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)], dutil[int(len(dutil) * 0.75)])
        line90 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)], dutil[int(len(dutil) * 0.90)])
        line95 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)], dutil[int(len(dutil) * 0.95)])
        line99 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)], dutil[int(len(dutil) * 0.99)])
        htmls = f'<div id="Percentile" style="float:left; background-color:#FF9933; height:200px; width:300px; margin-right:10px"><h3 align="center">Percentile</h3><p align="center">75%:&nbsp&nbsp&nbsp&nbsp{line75}<br>90%:&nbsp&nbsp&nbsp&nbsp{line90}<br>95%:&nbsp&nbsp&nbsp&nbsp{line95}<br>99%:&nbsp&nbsp&nbsp&nbsp{line99}</p></div>'
    else:
        line75 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)])
        line90 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)])
        line95 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)])
        line99 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)])
        htmls = f'<div id="Percentile" style="float:left; background-color:#FF9933; height:200px; width:300px; margin-right:10px"><h3 align="center">Percentile</h3><p align="center">75%:&nbsp&nbsp&nbsp&nbsp{line75}<br>90%:&nbsp&nbsp&nbsp&nbsp{line90}<br>95%:&nbsp&nbsp&nbsp&nbsp{line95}<br>99%:&nbsp&nbsp&nbsp&nbsp{line99}</p></div>'

    return htmls


def get_gc(pid):
    """
        获取java应用的垃圾回收相关信息，包括ygc, ygct, fgc, fgct, 和ygc频率, fgc频率.
    """
    try:
        result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]
        res = result.strip().split(' ')

        ygc = int(res[12])
        ygct = float(res[13])
        fgc = int(res[14])
        fgct = float(res[15])
        fygc = 0
        ffgc = 0

        result = os.popen(f'ps -p {pid} -o etimes').readlines()[1]      # 获取服务启动时间
        runtime = int(result.strip())

        if ygc > 0:
            fygc = runtime / ygc
        if fgc > 0:
            ffgc = runtime / fgc

    except Exception as err:
        logger.logger.error(err)
        ygc, ygct, fgc, fgct, fygc, ffgc = -1, -1, -1, -1, -1, -1

    htmls = f'<div id="GC" style="float:left; background-color:#CC6633; height:200px; width:300px"><h3 align="center">GC</h3><p align="center">YGC:&nbsp{ygc}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspYGCT:&nbsp{ygct}s<br>FGC:&nbsp{fgc}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspFGCT:&nbsp{fgct}s<br>Frequence of YGC:&nbsp{fygc:.2f}s<br>Frequence of FGC:&nbsp{ffgc:.2f}s</p></div>'

    return htmls
