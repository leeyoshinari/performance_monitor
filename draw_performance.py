#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import base64
import time
import glob
import traceback
import datetime
import matplotlib.pyplot as plt
from io import BytesIO

import config as cfg
from logger import logger
from extern import DealLogs


def draw_data_from_mysql(port=None, pid=None, start_time=None, duration=None, system=None, is_io=True):
    """
    Read data from logs.
    Return html included plotting, and data.
    """
    search = None

    if port:
        search = port
    elif pid:
        search = pid

    if pid is not None:
        pid_num = int(pid.split('_')[-1])
    elif system is not None:
        pid_num = 'system'
    else:
        pid_num = None

    if system is not None:
        search = 'system'

    logs = glob.glob(cfg.LOG_PATH + '/*.log')  # get all logs

    deal_logs = DealLogs(search, is_io)

    try:
        if start_time and duration:
            # Convert `start_time` to floating point seconds after 1970.
            startTime = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple())
            endTime = startTime + duration
            deal_logs.read_data_from_logs(logs, startTime, endTime)      # read data from logs
        else:
            deal_logs.read_data_from_logs(logs)

        # plotting
        image_html = draw(search, deal_logs.system, deal_logs.cpu_and_mem[0], deal_logs.cpu_and_mem[1:3],
                          deal_logs.disk_io, deal_logs.total_time, deal_logs.io_total_time)
        # calculate Percentile
        per_html = get_lines(deal_logs.system[0], deal_logs.cpu_and_mem[0], deal_logs.disk_io[2], search, is_io)
        # get GC, just for java
        if search == 'system':
            gc_html = ''
        else:
            gc_html = get_gc(pid_num)

        html = cfg.HTML.format(cfg.HEADER.format(pid_num) + image_html + cfg.ANALYSIS.format(per_html + gc_html))
        del deal_logs

        return html
    except Exception as err:
        del deal_logs
        logger.error(err)
        logger.error(traceback.format_exc())
        raise Exception(err)


def draw(types, system, cpu, mem, disk_io, times, io_times):
    """
        plot
    """
    length = len(times)
    io_length = len(io_times)
    if length < 7:
        logger.error('Too less data, please wait a minute.')
        return cfg.ERROR.format('Too less data, please wait a minute.')

    # x-axis and x-ticks
    index = [[], []]
    labels = [[], []]
    delta = length / 6
    io_delta = io_length / 6
    for i in range(6):
        index[0].append(int(i * delta))
        index[1].append(int(i * io_delta))
        labels[0].append(times[int(i * delta)])
        labels[1].append(io_times[int(i * io_delta)])

    index[0].append(length - 1)
    index[1].append(io_length - 1)
    labels[0].append(times[length - 1])
    labels[1].append(io_times[io_length - 1])

    cpu_start_time = time.mktime(datetime.datetime.strptime(str(times[0]), '%Y-%m-%d %H:%M:%S').timetuple())
    cpu_end_time = time.mktime(datetime.datetime.strptime(str(times[-1]), '%Y-%m-%d %H:%M:%S').timetuple())
    io_start_time = time.mktime(datetime.datetime.strptime(str(io_times[0]), '%Y-%m-%d %H:%M:%S').timetuple())
    io_end_time = time.mktime(datetime.datetime.strptime(str(io_times[-1]), '%Y-%m-%d %H:%M:%S').timetuple())

    if types == 'system':
        fig = plt.figure('figure', figsize=(20, 15))
        ax1 = plt.subplot(3, 1, 1)
        ax2 = plt.subplot(3, 1, 2)
        ax3 = plt.subplot(3, 1, 3)

        plt.sca(ax1)
        plt.plot(system[0], color='r', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(system[0]))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(system[0]), sum(system[0]) / len(system[0]), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        plt.sca(ax2)
        plt.plot(system[1], color='r', linewidth=1, label='Memory')
        plt.title('Free Memory(G), min:{:.2f}G, duration:{:.1f}h'.format(
            min(system[1]), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.grid()
        plt.xlim(0, len(system[1]))
        plt.ylim(0, max(system[1]) + 1)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        plt.sca(ax3)
        plt.plot(disk_io[0], color='black', linewidth=1, label='rkB/s')
        plt.plot(disk_io[1], color='b', linewidth=1, label='wkB/s')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(disk_io[2]))
        plt.ylim(0, max(max(disk_io[0]), max(disk_io[1])))
        plt.title('IO, max:{:.2f}%, duration:{:.1f}h'.format(
            max(disk_io[2]), (io_end_time - io_start_time) / 3600), size=12)
        plt.xticks(index[1], labels[1])
        plt.margins(0, 0)

        ax_util = ax3.twinx()
        plt.sca(ax_util)
        plt.plot(disk_io[2], color='red', linewidth=1, label='%util')
        plt.legend(loc='upper right')
        plt.ylim(0, max(disk_io[2]))

    else:
        fig = plt.figure('figure', figsize=(20, 10))
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)

        plt.sca(ax1)
        plt.plot(cpu, color='r', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(cpu))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(cpu), sum(cpu) / len(cpu), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        plt.sca(ax2)
        plt.plot(mem[0], color='r', linewidth=1, label='Memory')

        if sum(mem[1]) == 0:
            plt.title('Memory(G), max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem[0]), (cpu_end_time - cpu_start_time) / 3600), size=12)
        else:
            plt.plot(mem[1], color='b', linewidth=1, label='JVM')
            plt.legend(loc='upper right')
            plt.title('Memory(G) max:{:.2f}G, JVM(G) max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem[0]), max(mem[1]), (cpu_end_time - cpu_start_time) / 3600), size=12)

        plt.grid()
        plt.xlim(0, len(mem[0]))
        plt.ylim(0, max(mem[0]) + 1)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')      # save figure to bytes
    data = base64.encodebytes(image_byte.getvalue()).decode()       # encode to base64

    html = f'<div align="center"><img src="data:image/png;base64,{data}" /></div>'
    plt.close()     # close figure
    return html


def get_lines(system_cpu, cpu, dutil, types, is_io):
    """
        Calculate Percentile，75%line、90%line、95%line、99%line
    """
    # sort
    system_cpu.sort()
    cpu.sort()
    dutil.sort()

    if types == 'system':
        line75 = 'CPU: {:.2f}%, util: {:.2f}%'.format(system_cpu[int(len(system_cpu) * 0.75)], dutil[int(len(dutil) * 0.75)])
        line90 = 'CPU: {:.2f}%, util: {:.2f}%'.format(system_cpu[int(len(system_cpu) * 0.90)], dutil[int(len(dutil) * 0.90)])
        line95 = 'CPU: {:.2f}%, util: {:.2f}%'.format(system_cpu[int(len(system_cpu) * 0.95)], dutil[int(len(dutil) * 0.95)])
        line99 = 'CPU: {:.2f}%, util: {:.2f}%'.format(system_cpu[int(len(system_cpu) * 0.99)], dutil[int(len(dutil) * 0.99)])
    else:
        if is_io:
            line75 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)], dutil[int(len(dutil) * 0.75)])
            line90 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)], dutil[int(len(dutil) * 0.90)])
            line95 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)], dutil[int(len(dutil) * 0.95)])
            line99 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)], dutil[int(len(dutil) * 0.99)])
        else:
            line75 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)])
            line90 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)])
            line95 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)])
            line99 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)])

    htmls = f'<div id="Percentile" style="float:left; background-color:#FF9933; height:200px; width:300px; ' \
        f'margin-right:10px"><h3 align="center">Percentile</h3><p align="center">75%:' \
        f'&nbsp&nbsp&nbsp&nbsp{line75}<br>90%:&nbsp&nbsp&nbsp&nbsp{line90}<br>95%:' \
        f'&nbsp&nbsp&nbsp&nbsp{line95}<br>99%:&nbsp&nbsp&nbsp&nbsp{line99}</p></div>'

    return htmls


def get_gc(pid):
    """
        Get GC, include ygc, ygct, fgc, fgct, ygc frequency, fgc frequency, just for java.
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

        result = os.popen(f'ps -p {pid} -o etimes').readlines()[1]      # get `pid` running time
        runtime = int(result.strip())

        if ygc > 0:
            fygc = runtime / ygc
        if fgc > 0:
            ffgc = runtime / fgc

    except Exception as err:
        logger.error(err)
        ygc, ygct, fgc, fgct, fygc, ffgc = -1, -1, -1, -1, -1, -1

    htmls = f'<div id="GC" style="float:left; background-color:#CC6633; height:200px; width:300px">' \
        f'<h3 align="center">GC</h3><p align="center">YGC:&nbsp{ygc}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspYGCT:' \
        f'&nbsp{ygct}s<br>FGC:&nbsp{fgc}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspFGCT:&nbsp{fgct}s<br>' \
        f'Frequence of YGC:&nbsp{fygc:.2f}s<br>Frequence of FGC:&nbsp{ffgc:.2f}s</p></div>'

    return htmls
