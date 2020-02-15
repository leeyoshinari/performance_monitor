#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import base64
import time
import datetime
from io import BytesIO
import influxdb
import matplotlib
'''
Due to you are using an interactive backend which is trying to create figure windows, which are failing because 
you have disconnected the x-server that was available when you started the simulations.
'''
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import config as cfg
from logger import logger
# from extern import DealLogs


def draw_data_from_db(host, port=None, pid=None, start_time=None, end_time=None, system=None, disk=None):
    """
    从hbase数据库中读取数据并画图
    :param host: 客户端服务器IP，必传参数
    :param port: 端口号，即画该端口号的图；可选参数，和pid、system参数互斥，三选一
    :param pid: 进程号，即画该进程号的图；可选参数，和port、system参数互斥，三选一
    :param start_time: 画图数据开始时间；可选参数
    :param end_time: 画图数据截止时间；可选参数
    :param system: 画整个系统CPU和内存图，可选参数，和port、pid参数互斥，三选一
    :param disk: 磁盘号，查看指定磁盘号的IO，可选参数
    :return:
    """
    try:
        cpu_time = []
        cpu = []
        mem = []
        jvm = []
        io_time = []
        io = []
        res = {}

        connection = influxdb.InfluxDBClient(cfg.INFLUX_IP, cfg.INFLUX_PORT, cfg.INFLUX_USERNAME,
                                             cfg.INFLUX_PASSWORD, cfg.INFLUX_DATABASE)   # 创建数据库连接

        if start_time and end_time:     # 如果存在开始时间和结束时间
            startTime = local2utc(start_time)
            endTime = local2utc(end_time)
        elif start_time is None and end_time is None:   # 如果开始时间和结束时间都不存在，则使用默认时间，即查询所有数据
            startTime = local2utc('2020-02-02 02:02:02')
            endTime = local2utc(time.strftime('%Y-%m-%d %H:%M:%S'))
        else:   # 如果结束时间不存在，则使用当前时间
            startTime = local2utc(start_time)
            endTime = local2utc(time.strftime('%Y-%m-%d %H:%M:%S'))

        if disk:    # 读取磁盘IO数据
            sql = f"select {disk} from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system'"
            datas = connection.query(sql)
            for data in datas.get_points():
                io_time.append(data['time'])
                io.append(float(data[disk]))

        if port:    # 读取和端口号相关的CPU使用率、内存使用大小和jvm变化数据
            sql = f"select cpu, mem, jvm from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='{port}'"
            datas = connection.query(sql)
            for data in datas.get_points():
                cpu_time.append(data['time'])
                cpu.append(data['cpu'])
                mem.append(data['mem'])
                jvm.append(data['jvm'])

            img = draw(types='port', cpu_time=cpu_time, cpu=cpu, mem=mem, jvm=jvm)      # 画图
            res.update(img)

        if pid:     # 读取和进程号相关的CPU使用率、内存使用大小和jvm变化数据
            pass

        if system:      # 读取整个系统的CPU使用率、剩余内存大小
            sql = f"select cpu, mem from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system'"
            datas = connection.query(sql)
            for data in datas.get_points():
                cpu_time.append(data['time'])
                cpu.append(data['cpu'])
                mem.append(data['mem'])

            img = draw(types='system', cpu_time=cpu_time, cpu=cpu, mem=mem, io_time=io_time, io=io, disk=disk)  # 画图
            res.update(img)

        lines = get_lines(cpu, io)      # 计算百分位数，75%、90%、95%、99%
        res.update(lines)

        return res

    except Exception as err:
        logger.error(err)

# def draw_data_from_log1(port=None, pid=None, start_time=None, end_time=None, system=0):
#     """
#     Read data from logs.
#     Return html included plotting, and data.
#     """
#     search = None
#     result = {}
#
#     if port:
#         search = port
#     elif pid:
#         search = pid
#
#     if pid is not None:
#         pid_num = int(pid.split('_')[-1])
#     elif system is not None:
#         pid_num = 'system'
#     else:
#         pid_num = None
#
#     if system == 1:
#         search = 'system'
#
#     logs = glob.glob(cfg.LOG_PATH + '/*.log')  # get all logs
#
#     deal_logs = DealLogs(search, 1)
#
#     try:
#         if start_time and end_time:
#             # Convert `start_time` to floating point seconds after 1970.
#             startTime = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple())
#             endTime = time.mktime(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S').timetuple())
#         elif start_time is None and end_time is None:
#             startTime = time.mktime(datetime.datetime.strptime('2020-01-01 08:08:08', '%Y-%m-%d %H:%M:%S').timetuple())
#             endTime = time.time()
#         else:
#             startTime = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple())
#             endTime = time.time()
#
#         deal_logs.read_data_from_logs(logs, startTime, endTime)  # read data from logs
#
#         # plotting
#         image = draw(search, deal_logs.system, deal_logs.cpu_and_mem[0], deal_logs.cpu_and_mem[1:3],
#                      deal_logs.disk_io, deal_logs.total_time, deal_logs.io_total_time)
#         # calculate Percentile
#         per = get_lines(deal_logs.system[0], deal_logs.cpu_and_mem[0], deal_logs.disk_io[2], search)
#         # gc
#         gc = get_gc(pid_num, search)
#
#         result.update({'data': image})
#         result.update(per)
#         result.update(gc)
#
#         del deal_logs
#
#         return result
#     except Exception as err:
#         del deal_logs
#         logger.error(err)
#         raise Exception(err)


def draw(types, cpu_time=None, cpu=None, mem=None, jvm=None, io_time=None, io=None, disk=None):
    """
    画图
    :param types: 传入数据类型，是和端口号或进程号相关的数据，还是和系统相关的数据
    :param cpu_time: 每一个cpu数据对应的时间戳
    :param cpu: CPU使用率(%)
    :param mem: 内存大小(G)
    :param jvm: jvm大小(G)
    :param io_time: 每一个磁盘IO数据对应的时间戳
    :param io: 磁盘IO(%)
    :param disk:磁盘号
    :return:
    """
    length = len(cpu_time)
    io_length = len(io_time)
    if min(length, io_length) < 7:  # 画图的最小刻度为7，故必须大于7个数据
        logger.error('数据太少，请稍后再试')
        raise Exception('当前数据太少，请稍后再试')

    index = [[], []]        # x轴坐标，一个是CPU和内存的x轴，一个是IO的x轴
    labels = [[], []]       # x轴刻度
    delta = length / 6      # x轴每个坐标间隔
    io_delta = io_length / 6    # x轴每个坐标间隔，IO
    for i in range(6):
        index[0].append(int(i * delta))
        labels[0].append(utc2local(cpu_time[int(i * delta)]))
        if types == 'system':
            index[1].append(int(i * io_delta))
            labels[1].append(utc2local(io_time[int(i * io_delta)]))

    # 添加最后一个时刻的数据
    index[0].append(length - 1)
    labels[0].append(utc2local(cpu_time[length - 1]))

    # 数据的开始时间和结束时间，用于计算图中展示数据的总时长
    cpu_start_time = time.mktime(datetime.datetime.strptime(cpu_time[0].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())
    cpu_end_time = time.mktime(datetime.datetime.strptime(cpu_time[-1].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())

    if types == 'system':
        # 添加最后一个时刻的数据
        index[1].append(io_length - 1)
        labels[1].append(utc2local(io_time[io_length - 1]))
        # 用于计算总时长
        io_start_time = time.mktime(datetime.datetime.strptime(io_time[0].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())
        io_end_time = time.mktime(datetime.datetime.strptime(io_time[-1].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())

        fig = plt.figure('figure', figsize=(20, 15))
        ax1 = plt.subplot(3, 1, 1)
        ax2 = plt.subplot(3, 1, 2)
        ax3 = plt.subplot(3, 1, 3)

        # 画CPU使用率
        plt.sca(ax1)
        plt.plot(cpu, color='r', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(cpu))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(cpu), sum(cpu) / len(cpu), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        # 画内存使用大小
        plt.sca(ax2)
        plt.plot(mem, color='r', linewidth=1, label='Memory')
        plt.title('Free Memory(G), min:{:.2f}G, duration:{:.1f}h'.format(
            min(mem), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.grid()
        plt.xlim(0, len(mem))
        plt.ylim(0, max(mem) + 1)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        # 画磁盘IO
        plt.sca(ax3)
        plt.plot(io, color='r', linewidth=1, label='%util')
        plt.grid()
        plt.xlim(0, len(io))
        plt.ylim(0, max(io))
        plt.title('IO({}), max:{:.2f}%, duration:{:.1f}h'.format(disk, max(io), (io_end_time - io_start_time) / 3600), size=12)
        plt.xticks(index[1], labels[1])
        plt.margins(0, 0)

    else:
        fig = plt.figure('figure', figsize=(20, 10))
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)

        # 画CPU使用率
        plt.sca(ax1)
        plt.plot(cpu, color='r', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(cpu))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(cpu), sum(cpu) / len(cpu), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        # 画内存使用大小和jvm
        plt.sca(ax2)
        plt.plot(mem, color='r', linewidth=1, label='Memory')

        if sum(jvm) == 0:   # 如果没有jvm数据，则不画jvm
            plt.title('Memory(G), max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem), (cpu_end_time - cpu_start_time) / 3600), size=12)
        else:
            plt.plot(jvm, color='b', linewidth=1, label='JVM')
            plt.legend(loc='upper right')
            plt.title('Memory(G) max:{:.2f}G, JVM(G) max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem), max(jvm), (cpu_end_time - cpu_start_time) / 3600), size=12)

        plt.grid()
        plt.xlim(0, len(mem))
        plt.ylim(0, max(max(mem), max(jvm)) + 1)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')     # 把图像保存成二进制
    img = base64.encodebytes(image_byte.getvalue()).decode()       # 二进制图片流转base64编码

    plt.close()
    return {'img': img}


def get_lines(cpu, dutil):
    """
    计算cpu和磁盘IO的百分位数
    :param cpu: CPU使用率(%)
    :param dutil: 磁盘IO(%)
    :return:
    """
    cpu.sort()      # 排序
    dutil.sort()

    line75 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)], dutil[int(len(dutil) * 0.75)])
    line90 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)], dutil[int(len(dutil) * 0.90)])
    line95 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)], dutil[int(len(dutil) * 0.95)])
    line99 = 'CPU: {:.2f}%, util: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)], dutil[int(len(dutil) * 0.99)])

    return {'line75': line75, 'line90': line90, 'line95': line95, 'line99': line99}


def utc2local(utc_time):
    """
    UTC时间转北京时间
    influexdb数据库的时间戳是UTC格式，例如：2020-02-02T02:02:02.20200202Z。按照"%Y-%m-%dT%H:%M:%S.%fZ"格式化UTC时间戳时，
    只能匹配小数点后6位，大于6位无法匹配，故根据"."分割，然后转换
    :param utc_time: UTC时间
    :return: 北京时间
    """
    local_format = "%Y-%m-%d %H:%M:%S"
    utc_format = "%Y-%m-%dT%H:%M:%S"
    local_time = datetime.datetime.strptime(utc_time.split('.')[0], utc_format) + datetime.timedelta(hours=8)
    return local_time.strftime(local_format)


def local2utc(local_time):
    """
    北京时间转UTC时间
    :param local_time: 北京时间
    :return: UTC时间
    """
    local_format = "%Y-%m-%d %H:%M:%S"
    utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    utc_time = datetime.datetime.strptime(local_time, local_format) - datetime.timedelta(hours=8)
    return utc_time.strftime(utc_format)
