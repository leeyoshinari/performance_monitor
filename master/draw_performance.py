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
from logger import logger, cfg


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
        post_data = {
            'types': 'system',
            'cpu_time': [],
            'cpu': [],
            'mem': [],
            'jvm': [],
            'io_time': [],
            'io': [],
            'rec': [],
            'trans': [],
            'nic': [],
            'disk': disk}

        res = {'code': 1, 'message': None}

        connection = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
                                             cfg.getInflux('password'), cfg.getInflux('database'))   # 创建数据库连接

        if start_time and end_time:     # 如果存在开始时间和结束时间
            startTime = local2utc(start_time)
            endTime = local2utc(end_time)
        elif start_time is None and end_time is None:   # 如果开始时间和结束时间都不存在，则使用默认时间，即查询所有数据
            startTime = local2utc('2020-02-02 02:02:02')
            endTime = local2utc(time.strftime('%Y-%m-%d %H:%M:%S'))
        else:   # 如果结束时间不存在，则使用当前时间
            startTime = local2utc(start_time)
            endTime = local2utc(time.strftime('%Y-%m-%d %H:%M:%S'))

        if port:    # 读取和端口号相关的CPU使用率、内存使用大小和jvm变化数据
            sql = f"select cpu, mem, jvm from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='{port}'"
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'port'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'])
                    post_data['cpu'].append(data['cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['jvm'].append(data['jvm'])
            else:
                res['message'] = f'未查询到端口{port}的监控数据，请检查端口是否已监控，或者时间设置是否正确！'
                res['code'] = 0

            if disk:  # 读取磁盘IO数据
                disk_n = disk.replace('-', '')
                sql = f"select {disk_n}, net from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system'"
                datas = connection.query(sql)
                if datas:
                    for data in datas.get_points():
                        post_data['io_time'].append(data['time'])
                        post_data['nic'].append(data['net'])
                        post_data['io'].append(float(data[disk_n]))
                else:
                    res['message'] = '未查询到监控数据，请检查磁盘号，或者时间设置！'
                    res['code'] = 0

        if pid:     # 读取和进程号相关的CPU使用率、内存使用大小和jvm变化数据
            pass

        if system and disk:      # 读取整个系统的CPU使用率、剩余内存大小
            disk_n = disk.replace('-', '')
            sql = f"select cpu, mem, {disk_n}, rec, trans, net from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system'"
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'system'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'])
                    post_data['cpu'].append(data['cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['rec'].append(data['rec'])
                    post_data['trans'].append(data['trans'])
                    post_data['nic'].append(data['net'])
                    post_data['io'].append(float(data[disk_n]))

                post_data['io_time'] = post_data['cpu_time']
            else:
                res['message'] = '未查询到系统监控数据，请检查磁盘号，或者时间设置！'
                res['code'] = 0

        img = draw(post_data)  # 画图
        res.update(img)

        lines = get_lines(post_data['cpu'], post_data['io'], post_data['nic'])      # 计算百分位数，75%、90%、95%、99%
        res.update(lines)
        del connection
        del post_data
        return res

    except Exception as err:
        del connection
        del post_data
        logger.error(err)
        return res


def draw(data):
    """
    画图
    :return:
    """
    types = data['types']
    cpu_time = data['cpu_time']
    cpu = data['cpu']
    mem = data['mem']
    jvm = data['jvm']
    io_time = data['io_time']
    io = data['io']
    disk = data['disk']
    rec = data['rec']
    trans = data['trans']
    net = data['nic']

    length = len(cpu_time)
    io_length = len(io_time)
    net_length = len(net)
    if min(length, io_length, net_length) < 7:  # 画图的最小刻度为7，故必须大于7个数据
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

        fig = plt.figure('figure', figsize=(20, 20))
        ax1 = plt.subplot(4, 1, 1)
        ax2 = plt.subplot(4, 1, 2)
        ax3 = plt.subplot(4, 1, 3)
        ax4 = plt.subplot(4, 1, 4)

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

        # 画带宽图
        plt.sca(ax4)
        plt.plot(rec, color='orange', linewidth=1, label='rMbs')
        plt.plot(trans, color='blue', linewidth=1, label='tMbs')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(rec))
        plt.ylim(0, max(max(rec), max(trans)))
        plt.title('NetWork, Rmax:{:.2f}Mb/s, Tmax:{:.2f}Mb/s, NetWork:{:.2f}%, duration:{:.1f}h'.format(
            max(rec), max(trans), max(net), (cpu_end_time - cpu_start_time) / 3600), size=12)
        plt.xticks(index[0], labels[0])
        plt.margins(0, 0)

        ax_net = ax4.twinx()
        plt.sca(ax_net)
        plt.plot(net, color='red', linewidth=1, label='%net')
        plt.legend(loc='upper right')
        plt.ylim(0, max(net))

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


def get_lines(cpu, dutil, nic):
    """
    计算cpu和磁盘IO的百分位数
    :param cpu: CPU使用率(%)
    :param dutil: 磁盘IO(%)
    :return:
    """
    cpu.sort()      # 排序
    dutil.sort()
    nic.sort()

    line75 = 'CPU: {:.2f}%, util: {:.2f}%, network: {:.2f}%'.format(cpu[int(len(cpu) * 0.75)], dutil[int(len(dutil) * 0.75)], nic[int(len(nic) * 0.75)])
    line90 = 'CPU: {:.2f}%, util: {:.2f}%, network: {:.2f}%'.format(cpu[int(len(cpu) * 0.90)], dutil[int(len(dutil) * 0.90)], nic[int(len(nic) * 0.90)])
    line95 = 'CPU: {:.2f}%, util: {:.2f}%, network: {:.2f}%'.format(cpu[int(len(cpu) * 0.95)], dutil[int(len(dutil) * 0.95)], nic[int(len(nic) * 0.95)])
    line99 = 'CPU: {:.2f}%, util: {:.2f}%, network: {:.2f}%'.format(cpu[int(len(cpu) * 0.99)], dutil[int(len(dutil) * 0.99)], nic[int(len(nic) * 0.99)])

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
