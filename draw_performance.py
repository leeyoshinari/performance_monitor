#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import base64
import time
import traceback
import datetime
import pymysql
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import config as cfg


def draw_data_from_mysql(pid, start_time=None, duration=None):
    db = pymysql.connect(cfg.MySQL_IP, cfg.MySQL_USERNAME, cfg.MySQL_PASSWORD, cfg.MySQL_DATABASE)  # connect MySQL
    cursor = db.cursor()

    try:
        c_time = []
        cpu = []
        mem = []
        jvm = []
        IO = []
        reader = []
        writer = []
        handles = []
        if start_time and duration:
            seconds = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple()) + duration
            end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))
            cpu_sql = "SELECT time, cpu, mem, jvm FROM cpu_and_mem WHERE pid={} and time>'{}' and time<'{}';".format(pid, start_time, end_time)
            io_sql = "SELECT time, reader, writer, io, FROM io WHERE pid={} and time>'{}' and time<'{}';".format(pid, start_time, end_time)
            h_sql = "SELECT time, handles FROM handles WHERE pid={} and time>'{}' and time<'{}';".format(pid, start_time, end_time)
        else:
            cpu_sql = "SELECT time, cpu, mem, jvm FROM cpu_and_mem WHERE pid={};".format(pid)
            io_sql = "SELECT time, reader, writer, io FROM io WHERE pid={};".format(pid)
            h_sql = "SELECT time, handles FROM handles WHERE pid={};".format(pid)

        cursor.execute(cpu_sql)
        result = cursor.fetchall()
        for i in range(len(result)):
            if result[i][0]:
                c_time.append(result[i][0])
                cpu.append(result[i][1])
                mem.append(result[i][2])
                jvm.append(result[i][3])

        cursor.execute(io_sql)
        result = cursor.fetchall()
        for i in range(len(result)):
            if result[i][0]:
                # c_time.append(result[i][0])
                reader.append(result[i][1])
                writer.append(result[i][2])
                IO.append(result[i][3])

        '''cursor.execute(h_sql)
        result = cursor.fetchall()
        for i in range(len(result)):
            if result[i][0]:
                c_time.append(result[i][0])
                handles.append(result[i][1])'''

        start_time = time.mktime(datetime.datetime.strptime(str(c_time[0]), '%Y-%m-%d %H:%M:%S').timetuple())
        end_time = time.mktime(datetime.datetime.strptime(str(c_time[-1]), '%Y-%m-%d %H:%M:%S').timetuple())

        image_html = draw(cpu, [mem, jvm], reader, writer, IO, handles, end_time-start_time)
        per_html = get_lines(cpu, IO)
        gc_html = get_gc(pid)
        html = cfg.HTML.format(cfg.HEADER.format(pid) + image_html + cfg.ANALYSIS.format(per_html + gc_html))

        cursor.close()
        db.close()

        return html
    except Exception as err:
        cursor.close()
        db.close()
        raise Exception(traceback.format_exc())


def draw(cpu, mem, reader, writer, IO, handles, total_time):
    fig = plt.figure('figure', figsize=(20, 15))
    ax1 = plt.subplot(3, 1, 1)
    plt.sca(ax1)
    plt.plot(cpu, color='r')
    plt.grid()
    plt.xlim(0, len(cpu))
    plt.ylim(0, 100)
    plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(max(cpu), np.mean(cpu), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    ax2 = plt.subplot(3, 1, 2)
    plt.sca(ax2)
    plt.plot(mem[0], color='r', label='Memory')
    plt.plot(mem[1], color='b', label='JVM')
    plt.legend()
    plt.grid()
    plt.xlim(0, len(mem[0]))
    plt.ylim(0, max(mem[0]) + 1)
    plt.title('Memory(G) max:{:.2f}G, JVM(G) max:{:.2f}G, duration:{:.1f}h'.format(max(mem[0]), max(mem[1]), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    ax3 = plt.subplot(3, 1, 3)
    plt.sca(ax3)
    plt.plot(reader, color='r', label='reader')
    plt.plot(writer, color='b', label='writer')
    plt.legend()
    plt.grid()
    plt.xlim(0, len(IO))
    plt.ylim(0, max([max(reader), max(writer)])+50)
    plt.title('Reader and Writer(K/s), duration:{:.1f}h'.format(np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    '''ax4 = plt.subplot(4, 1, 4)
    plt.sca(ax4)
    plt.plot(handles, color='r')
    plt.grid()
    plt.xlim(0, len(handles))
    plt.ylim(0, max(handles) + 10)
    plt.title('Handle, max:{}, duration:{:.1f}h'.format(int(max(handles)), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)'''

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')
    data = base64.encodebytes(image_byte.getvalue()).decode()

    html = '<div align="center"><img src="data:image/png;base64,{}" /></div>'.format(data)
    plt.close()
    return html


def get_lines(cpu, IO):
    cpu.sort()
    IO.sort()

    line75 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)])
    line90 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.9)])
    line95 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)])
    line99 = 'CPU: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)])

    htmls = '<div id="Percentile" style="float:left; background-color:#FF9933; height:200px; width:300px; margin-right:10px"><h3 align="center">Percentile</h3><p align="center">75%:&nbsp&nbsp&nbsp&nbsp{}<br>90%:&nbsp&nbsp&nbsp&nbsp{}<br>95%:&nbsp&nbsp&nbsp&nbsp{}<br>99%:&nbsp&nbsp&nbsp&nbsp{}</p></div>'.format(line75, line90, line95, line99)

    return htmls


def get_gc(pid):
    try:
        result = os.popen('jstat -gc {} |tr -s " "'.format(pid)).readlines()[1]
        res = result.strip().split(' ')

        ygc = int(res[12])
        ygct = float(res[13])
        fgc = int(res[14])
        fgct = float(res[15])
        fygc = 0
        ffgc = 0

        result = os.popen('ps -p {} -o etimes'.format(pid)).readlines()[1]
        runtime = int(result.strip())

        if ygc > 0:
            fygc = runtime / ygc
        if fgc > 0:
            ffgc = runtime / fgc

    except Exception as err:
        ygc, ygct, fgc, fgct, fygc, ffgc = -1, -1, -1, -1, -1, -1

    htmls = '<div id="GC" style="float:left; background-color:#CC6633; height:200px; width:300px"><h3 align="center">GC</h3><p align="center">YGC:&nbsp{}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspYGCT:&nbsp{}s<br>FGC:&nbsp{}&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspFGCT:&nbsp{}s<br>Frequence of YGC:&nbsp{:.2f}s<br>Frequence of FGC:&nbsp{:.2f}s</p></div>'.format(ygc, ygct, fgc, fgct, fygc, ffgc)

    return htmls


def delete_database():
    db = pymysql.connect(cfg.MySQL_IP, cfg.MySQL_USERNAME, cfg.MySQL_PASSWORD, cfg.MySQL_DATABASE)
    cursor = db.cursor()
    try:
        for table in ['cpu_and_mem', 'io']:
            sql = "DROP TABLE {};".format(table)
            cursor.execute(sql)
        cursor.close()
        db.close()
    except Exception as err:
        cursor.close()
        db.close()
        raise Exception(traceback.format_exc())
