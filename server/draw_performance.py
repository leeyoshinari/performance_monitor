#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import time
import datetime
import traceback
import influxdb
from logger import logger, cfg


def draw_data_from_db(host, port=None, pid=None, startTime=None, endTime=None, system=None, disk=None):
    """
    从hbase数据库中读取数据并画图
    :param host: 客户端服务器IP，必传参数
    :param port: 端口号，即画该端口号的图；可选参数，和pid、system参数互斥，三选一
    :param pid: 进程号，即画该进程号的图；可选参数，和port、system参数互斥，三选一
    :param startTime: 画图数据开始时间；可选参数
    :param endTime: 画图数据截止时间；可选参数
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

        if startTime and endTime:     # 如果存在开始时间和结束时间
            pass
        elif startTime is None and endTime is None:   # 如果开始时间和结束时间都不存在，则使用默认时间，即查询所有数据
            startTime = '2020-05-20 20:20:20'
            endTime = time.strftime('%Y-%m-%d %H:%M:%S')
        else:   # 如果结束时间不存在，则使用当前时间
            endTime = time.strftime('%Y-%m-%d %H:%M:%S')

        s_time = time.time()
        if port:    # 读取和端口号相关的CPU使用率、内存使用大小和jvm变化数据
            sql = f"select cpu, mem, tcp, jvm, close_wait, time_wait from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='{port}' tz('Asia/Shanghai')"
            logger.info(f'执行sql：{sql}')
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'port'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'][:19].replace('T', ' '))
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
                sql = f"select {disk_n}, {disk_r}, {disk_w}, rec, trans, net from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system' tz('Asia/Shanghai')"
                logger.info(f'执行sql：{sql}')
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
            sql = f"select cpu, mem, {disk_n}, {disk_r}, {disk_w}, rec, trans, net, tcp, retrans from \"{host}\" where time>'{startTime}' and time<'{endTime}' and type='system' tz('Asia/Shanghai')"
            logger.info(f'执行sql：{sql}')
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'system'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'][:19].replace('T', ' '))
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

            else:
                res['message'] = '未查询到系统监控数据，请检查磁盘号，或者时间设置！'
                res['code'] = 0

        res.update({'post_data': post_data})
        logger.info(f'查询数据库耗时：{time.time() - s_time}')

        # s_time = time.time()
        # lines = get_lines(post_data)      # 计算百分位数，75%、90%、95%、99%
        # res.update(lines)
        # logger.info(f'计算百分位数耗时：{time.time() - s_time}')
        del connection, post_data
        return res

    except Exception as err:
        del connection, post_data
        logger.error(traceback.format_exc())
        res['message'] = err
        res['code'] = 0
        return res


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
