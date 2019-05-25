#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import base64
import time
import datetime
import pymysql
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import config as cfg


def draw_data_from_mysql(pid, start_time=None, duration=None):
    db = pymysql.connect(cfg.MySQL_IP, cfg.MySQL_USERNAME, cfg.MySQL_PASSWORD, cfg.MySQL_DATABASE)  # connect MySQL
    cursor = db.cursor()

    c_time = []
    cpu = []
    mem = []
    IO = []
    if start_time and duration:
        seconds = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple()) + duration
        end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(seconds))
        sql = "SELECT time, cpu, mem, io FROM performance WHERE pid={} and time>'{}' and time<'{}';".format(pid, start_time, end_time)
    else:
        sql = "SELECT time, cpu, mem, io FROM performance WHERE pid={};".format(pid)
    cursor.execute(sql)  # 执行mysql命令
    result = cursor.fetchall()
    for i in range(len(result)):
        if result[i][0]:
            c_time.append(result[i][0])
            cpu.append(int(result[i][1]))
            mem.append(result[i][2])
            IO.append(result[i][3])

    db.close()
    # return c_time, cpu, mem
    start_time = time.mktime(datetime.datetime.strptime(str(c_time[0]), '%Y-%m-%d %H:%M:%S').timetuple())
    end_time = time.mktime(datetime.datetime.strptime(str(c_time[-1]), '%Y-%m-%d %H:%M:%S').timetuple())
    return draw(cpu, mem, IO, c_time, end_time-start_time)


def draw(cpu, mem, IO, c_time, total_time):
    fig = plt.figure('cpu and memory', figsize=(20, 11))
    ax1 = plt.subplot(3, 1, 1)
    plt.sca(ax1)
    plt.plot(cpu, color='r')
    plt.grid()
    plt.xlim(0, len(cpu))
    plt.ylim(0, 100)
    plt.title('CPU(%), max:{}%, average:{:.2f}%, duration:{:.1f}h'.format(max(cpu), np.mean(cpu), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    ax2 = plt.subplot(3, 1, 2)
    plt.sca(ax2)
    plt.plot(mem, color='r')
    plt.grid()
    plt.xlim(0, len(mem))
    plt.ylim(0, max(mem) + 1)
    plt.title('Memory(%), max:{}%, average:{:.1f}%, duration:{:.1f}h'.format(max(mem), np.mean(mem[-int(len(mem)/3):]), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    ax3 = plt.subplot(3, 1, 3)
    plt.sca(ax3)
    plt.plot(IO, color='r')
    plt.grid()
    plt.xlim(0, len(IO))
    plt.ylim(0, 100)
    plt.title('IO(%), max:{}%, average:{:.2f}%, duration:{:.1f}h'.format(max(IO), np.mean(IO), np.floor(total_time / 360) / 10), size=12)
    plt.margins(0, 0)

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')
    data = base64.encodebytes(image_byte.getvalue()).decode()

    lines = get_lines(cpu, mem, IO)

    html = '<html><body><img src="data:image/png;base64,{}" />{}</body><html>'.format(data, lines)
    plt.close()
    return html


def get_lines(cpu, mem, IO):
    cpu.sort()
    mem.sort()
    IO.sort()

    line50 = 'CPU: {}%, MEM: {}G, IO: {}%'.format(cpu[int(len(cpu) * 0.5)], mem[int(len(mem) * 0.5)], IO[int(len(IO) * 0.5)])
    line75 = 'CPU: {}%, MEM: {}G, IO: {}%'.format(cpu[int(len(cpu) * 0.75)], mem[int(len(mem) * 0.75)], IO[int(len(IO) * 0.75)])
    line90 = 'CPU: {}%, MEM: {}G, IO: {}%'.format(cpu[int(len(cpu) * 0.9)], mem[int(len(mem) * 0.9)], IO[int(len(IO) * 0.9)])
    line95 = 'CPU: {}%, MEM: {}G, IO: {}%'.format(cpu[int(len(cpu) * 0.95)], mem[int(len(mem) * 0.95)], IO[int(len(IO) * 0.95)])
    line99 = 'CPU: {}%, MEM: {}G, IO: {}%'.format(cpu[int(len(cpu) * 0.99)], mem[int(len(mem) * 0.99)], IO[int(len(IO) * 0.99)])

    htmls = '<h3>Percentile:</h3><p>50%: {}<br>75%: {}<br>90%: {}<br>95%: {}<br>99%: {}</p>'.format(line50, line75, line90, line95, line99)

    return htmls


def delete_database():
    db = pymysql.connect(cfg.MySQL_IP, cfg.MySQL_USERNAME, cfg.MySQL_PASSWORD, cfg.MySQL_DATABASE)
    cursor = db.cursor()
    sql = "DROP TABLE performance;"
    cursor.execute(sql)
    db.close()
