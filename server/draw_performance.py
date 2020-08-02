#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import base64
import time
import datetime
import traceback
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
            'disk_r': [],
            'disk_w': [],
            'rec': [],
            'trans': [],
            'nic': [],
            'tcp': [],
            'close_wait': [],
            'time_wait': [],
            'retrans': [],
            'disk': disk}

        res = {'code': 1, 'flag': 1, 'message': '查询成功'}

        connection = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
                                             cfg.getInflux('password'), cfg.getInflux('database'))   # 创建数据库连接

        if start_time and end_time:     # 如果存在开始时间和结束时间
            pass
        elif start_time is None and end_time is None:   # 如果开始时间和结束时间都不存在，则使用默认时间，即查询所有数据
            start_time = '2020-05-20 20:20:20'
            end_time = time.strftime('%Y-%m-%d %H:%M:%S')
        else:   # 如果结束时间不存在，则使用当前时间
            end_time = time.strftime('%Y-%m-%d %H:%M:%S')

        s_time = time.time()
        if port:    # 读取和端口号相关的CPU使用率、内存使用大小和jvm变化数据
            sql = f"select cpu, mem, tcp, jvm, close_wait, time_wait from \"{host}\" where time>'{start_time}' and time<'{end_time}' and type='{port}' tz('Asia/Shanghai')"
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'port'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'].split('.')[0].replace('T', ' '))
                    post_data['cpu'].append(data['cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['tcp'].append(data['tcp'])
                    post_data['jvm'].append(data['jvm'])
                    post_data['close_wait'].append(data['close_wait'])
                    post_data['time_wait'].append(data['time_wait'])
            else:
                res['message'] = f'未查询到{port}端口的监控数据，请检查端口是否已监控，或者时间设置是否正确！'
                res['code'] = 0

            if disk:  # 读取磁盘IO数据
                disk_n = disk.replace('-', '')
                disk_r = disk_n + '_r'
                disk_w = disk_n + '_w'
                sql = f"select {disk_n}, {disk_r}, {disk_w}, rec, trans, net from \"{host}\" where time>'{start_time}' and time<'{end_time}' and type='system' tz('Asia/Shanghai')"
                datas = connection.query(sql)
                if datas:
                    for data in datas.get_points():
                        post_data['nic'].append(data['net'])
                        post_data['rec'].append(data['rec'])
                        post_data['trans'].append(data['trans'])
                        post_data['io'].append(data[disk_n])
                        post_data['disk_r'].append(data[disk_r])
                        post_data['disk_w'].append(data[disk_w])
                else:
                    res['message'] = '未查询到监控数据，请检查磁盘号，或者时间设置！'
                    res['code'] = 0

        if pid:     # 读取和进程号相关的CPU使用率、内存使用大小和jvm变化数据
            pass

        if system and disk:      # 读取整个系统的CPU使用率、剩余内存大小
            disk_n = disk.replace('-', '')
            disk_r = disk_n + '_r'
            disk_w = disk_n + '_w'
            sql = f"select cpu, mem, {disk_n}, {disk_r}, {disk_w}, rec, trans, net, tcp, retrans from \"{host}\" where time>'{start_time}' and time<'{end_time}' and type='system' tz('Asia/Shanghai')"
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'system'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'].split('.')[0].replace('T', ' '))
                    post_data['cpu'].append(data['cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['rec'].append(data['rec'])
                    post_data['trans'].append(data['trans'])
                    post_data['nic'].append(data['net'])
                    post_data['io'].append(data[disk_n])
                    post_data['disk_r'].append(data[disk_r])
                    post_data['disk_w'].append(data[disk_w])
                    post_data['tcp'].append(data['tcp'])
                    post_data['retrans'].append(data['retrans'])

                post_data['io_time'] = post_data['cpu_time']
            else:
                res['message'] = '未查询到系统监控数据，请检查磁盘号，或者时间设置！'
                res['code'] = 0

        logger.info(f'查询数据库耗时：{time.time() - s_time}')
        s_time = time.time()
        img = draw(post_data)  # 画图
        res.update(img)
        logger.info(f'画图耗时：{time.time() - s_time}')

        s_time = time.time()
        lines = get_lines(post_data)      # 计算百分位数，75%、90%、95%、99%
        res.update(lines)
        logger.info(f'计算百分位数耗时：{time.time() - s_time}')
        del connection, post_data, datas
        return res

    except Exception as err:
        del connection, post_data, datas
        logger.error(err)
        logger.error(traceback.format_exc())
        res['message'] = err
        res['code'] = 0
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
    # io_time = data['io_time']
    io = data['io']
    disk = data['disk']
    disk_r = data['disk_r']
    disk_w = data['disk_w']
    rec = data['rec']
    trans = data['trans']
    net = data['nic']
    tcp = data['tcp']
    close_wait = data['close_wait']
    time_wait = data['time_wait']
    retrans = data['retrans']

    length = len(cpu_time)
    # io_length = len(io_time)
    net_length = len(net)
    if min(length, net_length) < 7:  # 画图的最小刻度为7，故必须大于7个数据
        logger.error('数据太少，请稍后再试')
        raise Exception('当前数据太少，请稍等10秒再试')

    index = []        # x轴坐标
    labels = []       # x轴刻度
    delta = length / 6      # x轴每个坐标间隔
    # io_delta = io_length / 6    # x轴每个坐标间隔，IO
    for i in range(6):
        index.append(int(i * delta))
        labels.append(cpu_time[int(i * delta)])

    # 添加最后一个时刻的数据
    index.append(length - 1)
    labels.append(cpu_time[length - 1])

    # 数据的开始时间和结束时间，用于计算图中展示数据的总时长
    start_time = time.mktime(datetime.datetime.strptime(cpu_time[0].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())
    end_time = time.mktime(datetime.datetime.strptime(cpu_time[-1].split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple())

    if types == 'system':
        fig = plt.figure('figure', figsize=(20, 25))
        ax1 = plt.subplot(5, 1, 1)
        ax2 = plt.subplot(5, 1, 2)
        ax3 = plt.subplot(5, 1, 3)
        ax4 = plt.subplot(5, 1, 4)
        ax5 = plt.subplot(5, 1, 5)

        # 画CPU使用率
        plt.sca(ax1)
        plt.plot(cpu, color='red', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(cpu))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(cpu), sum(cpu) / len(cpu), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        # 画内存使用大小
        plt.sca(ax2)
        plt.plot(mem, color='red', linewidth=0.5, label='Memory')
        plt.title('Free Memory(G), min:{:.2f}G, duration:{:.1f}h'.format(
            min(mem), (end_time - start_time) / 3600), size=12)
        plt.grid()
        plt.xlim(0, len(mem))
        plt.ylim(0, max(mem) + 1)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        # 画磁盘IO
        plt.sca(ax3)
        plt.plot(disk_r, color='orange', linewidth=0.5, label='rMb/s')
        plt.plot(disk_w, color='blue', linewidth=0.5, label='wMb/s')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(io))
        plt.ylim(0, max(max(disk_r), max(disk_w)))
        plt.title('Disk({}), Rmax:{:.2f}Mb/s, Wmax:{:.2f}Mb/s, IO:{:.2f}%, duration:{:.1f}h'.format(
            disk, max(disk_r), max(disk_w), max(io), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        ax_twinx = ax3.twinx()
        plt.sca(ax_twinx)
        plt.plot(io, color='red', linewidth=0.5, label='%util')
        plt.legend(loc='upper right')
        plt.ylim(0, max(io))

        # 画带宽图
        plt.sca(ax4)
        plt.plot(rec, color='orange', linewidth=0.5, label='rMbs')
        plt.plot(trans, color='blue', linewidth=0.5, label='tMbs')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(rec))
        plt.ylim(0, max(max(rec), max(trans)))
        plt.title('NetWork, Rmax:{:.2f}Mb/s, Tmax:{:.2f}Mb/s, NetWork:{:.3f}%, duration:{:.1f}h'.format(
            max(rec), max(trans), max(net), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        ax_twinx = ax4.twinx()
        plt.sca(ax_twinx)
        plt.plot(net, color='red', linewidth=0.5, label='%net')
        plt.legend(loc='upper right')
        plt.ylim(0, max(net))

        # 画TCP
        plt.sca(ax5)
        plt.plot(tcp, color='red', linewidth=0.5, label='TCP')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(tcp))
        plt.ylim(0, max(tcp))
        plt.title('TCP, max:{}, Retrans:{:.3f}%, duration:{:.1f}h'.format(
            max(tcp), max(retrans), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        ax_twinx = ax5.twinx()
        plt.sca(ax_twinx)
        plt.plot(retrans, color='blue', linewidth=0.5, label='%Retrans')
        plt.legend(loc='upper right')
        plt.ylim(0, max(retrans))

    else:
        fig = plt.figure('figure', figsize=(20, 15))
        ax1 = plt.subplot(3, 1, 1)
        ax2 = plt.subplot(3, 1, 2)
        ax3 = plt.subplot(3, 1, 3)

        # 画CPU使用率
        plt.sca(ax1)
        plt.plot(cpu, color='red', linewidth=0.3, label='CPU')
        plt.grid()
        plt.xlim(0, len(cpu))
        plt.ylim(0, 100)
        plt.title('CPU(%), max:{:.2f}%, average:{:.2f}%, duration:{:.1f}h'.format(
            max(cpu), sum(cpu) / len(cpu), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        # 画内存使用大小和jvm
        plt.sca(ax2)
        plt.plot(mem, color='red', linewidth=0.5, label='Memory')

        if sum(jvm) == 0:   # 如果没有jvm数据，则不画jvm
            plt.title('Memory(G), max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem), (end_time - start_time) / 3600), size=12)
        else:
            plt.plot(jvm, color='blue', linewidth=0.5, label='JVM')
            plt.legend(loc='upper right')
            plt.title('Memory(G) max:{:.2f}G, JVM(G) max:{:.2f}G, duration:{:.1f}h'.format(
                max(mem), max(jvm), (end_time - start_time) / 3600), size=12)

        plt.grid()
        plt.xlim(0, len(mem))
        plt.ylim(0, max(max(mem), max(jvm)) + 1)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        # 画TCP
        plt.sca(ax3)
        plt.plot(time_wait, color='blue', linewidth=0.5, label='TIME_WAIT')
        plt.plot(close_wait, color='orange', linewidth=0.5, label='CLOSE_WAIT')
        plt.legend(loc='upper left')
        plt.grid()
        plt.xlim(0, len(tcp))
        plt.ylim(0, max(max(time_wait), max(close_wait)))
        plt.title('TCP max:{}, TIME_WAIT max:{}, CLOSE_WAIT max:{}, duration:{:.1f}h'.format(
            max(tcp), max(time_wait), max(close_wait), (end_time - start_time) / 3600), size=12)
        plt.xticks(index, labels)
        plt.margins(0, 0)

        ax_twinx = ax3.twinx()
        plt.sca(ax_twinx)
        plt.plot(tcp, color='red', linewidth=0.5, label='TCP')
        plt.legend(loc='upper right')
        plt.ylim(0, max(tcp))

    image_byte = BytesIO()
    fig.savefig(image_byte, format='png', bbox_inches='tight')     # 把图像保存成二进制
    img = base64.encodebytes(image_byte.getvalue()).decode()       # 二进制图片流转base64编码

    plt.close()
    return {'img': img}


def get_lines(datas):
    """
    计算cpu、磁盘、带宽的百分位数
    :param datas: CPU使用率(%)
    :return:
    """
    cpu = datas['cpu']
    disk_r = datas['disk_r'] if datas['disk_r'] else [-1]
    disk_w = datas['disk_w'] if datas['disk_w'] else [-1]
    io = datas['io']
    rec = datas['rec'] if datas['rec'] else [-1]
    trans = datas['trans'] if datas['trans'] else [-1]
    nic = datas['nic']

    cpu.sort()
    disk_r.sort()
    disk_w.sort()
    io.sort()
    rec.sort()
    trans.sort()
    nic.sort()

    line75 = [round(cpu[int(len(cpu) * 0.75)], 2), round(disk_r[int(len(disk_r) * 0.75)], 2),
              round(disk_w[int(len(disk_w) * 0.75)], 2), round(io[int(len(io) * 0.75)], 3),
              round(rec[int(len(rec) * 0.75)], 2), round(trans[int(len(trans) * 0.75)], 2),
              round(nic[int(len(nic) * 0.75)], 3)]
    line90 = [round(cpu[int(len(cpu) * 0.9)], 2), round(disk_r[int(len(disk_r) * 0.9)], 2),
              round(disk_w[int(len(disk_w) * 0.9)], 2), round(io[int(len(io) * 0.9)], 3),
              round(rec[int(len(rec) * 0.9)], 2), round(trans[int(len(trans) * 0.9)], 2),
              round(nic[int(len(nic) * 0.9)], 3)]
    line95 = [round(cpu[int(len(cpu) * 0.95)], 2), round(disk_r[int(len(disk_r) * 0.95)], 2),
              round(disk_w[int(len(disk_w) * 0.95)], 2), round(io[int(len(io) * 0.95)], 3),
              round(rec[int(len(rec) * 0.95)], 2), round(trans[int(len(trans) * 0.95)], 2),
              round(nic[int(len(nic) * 0.95)], 3)]
    line99 = [round(cpu[int(len(cpu) * 0.99)], 2), round(disk_r[int(len(disk_r) * 0.99)], 2),
              round(disk_w[int(len(disk_w) * 0.99)], 2), round(io[int(len(io) * 0.99)], 3),
              round(rec[int(len(rec) * 0.99)], 2), round(trans[int(len(trans) * 0.99)], 2),
              round(nic[int(len(nic) * 0.99)], 3)]

    return {'line': [line75, line90, line95, line99]}


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
