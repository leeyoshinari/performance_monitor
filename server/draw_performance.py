#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import time
import traceback
import influxdb_client
from logger import logger, cfg


def draw_data_from_db(host, port=None, pid=None, startTime=None, endTime=None, system=None, disk=None):
    """
    Get data from InfluxDB, and visualize
    :param host: client IP, required
    :param port: port, visualize port data; optional, choose one from port, pid and system
    :param pid: pid, visualize pid data; optional, choose one from port, pid and system
    :param startTime: Start time; optional
    :param endTime: end time; optional
    :param system: visualize system data; optional, choose one from port, pid and system
    :param disk: disk number; optional
    :return:
    """
    post_data = {
        'types': 'system',
        'cpu_time': [],
        'cpu': [],
        'iowait': [],
        'usr_cpu': [],
        'mem': [],
        'mem_available': [],
        'jvm': [],
        'io_time': [],
        'io': [],
        'disk_r': [],
        'disk_w': [],
        'disk_d': [],
        'rec': [],
        'trans': [],
        'nic': [],
        'tcp': [],
        'close_wait': [],
        'time_wait': [],
        'retrans': [],
        'disk': disk}

    res = {'code': 1, 'flag': 1, 'message': 'Successful!'}

    connection = influxdb_client.InfluxDBClient(url=cfg.getInflux('url'), token=cfg.getInflux('token'), org=cfg.getInflux('org'))

    try:
        if startTime and endTime:     # If there is a start time and an end time
            pass
        elif startTime is None and endTime is None:  # If the start time and end time do not exist, use the default time.
            startTime = '2020-05-20 20:20:20'
            endTime = time.strftime('%Y-%m-%d %H:%M:%S')
        else:   # If the end time does not exist, the current time is used
            endTime = time.strftime('%Y-%m-%d %H:%M:%S')

        s_time = time.time()
        if port:
            sql = f"select cpu, wait_cpu, mem, tcp, jvm, rKbs, wKbs, iodelay, close_wait, time_wait from \"{host}\" " \
                  f"where time>'{startTime}' and time<'{endTime}' and type='{port}' tz('Asia/Shanghai')"
            logger.info(f'Execute sql: {sql}')
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'port'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'][:19].replace('T', ' '))
                    post_data['cpu'].append(data['cpu'])
                    post_data['iowait'].append(data['wait_cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['tcp'].append(data['tcp'])
                    post_data['jvm'].append(data['jvm'])
                    post_data['io'].append(data['iodelay'])
                    post_data['disk_r'].append(data['rKbs'])
                    post_data['disk_w'].append(data['wKbs'])
                    post_data['close_wait'].append(data['close_wait'])
                    post_data['time_wait'].append(data['time_wait'])
            else:
                res['message'] = f'No monitoring data of the port {port} is found, ' \
                                 f'please check the port or time setting.'
                res['code'] = 0

            if disk:
                sql = f"select rec, trans, net from \"{host}\" where time>'{startTime}' and time<'{endTime}' and " \
                      f"type='system' tz('Asia/Shanghai')"
                logger.info(f'Execute sql: {sql}')
                datas = connection.query(sql)
                if datas:
                    for data in datas.get_points():
                        post_data['nic'].append(data['net'])
                        post_data['rec'].append(data['rec'])
                        post_data['trans'].append(data['trans'])
                else:
                    res['message'] = 'No monitoring data is found, please check the disk number or time setting.'
                    res['code'] = 0

        if pid:
            pass

        if system and disk:
            disk_n = disk.replace('-', '')
            disk_r = disk_n + '_r'
            disk_w = disk_n + '_w'
            disk_d = disk_n + '_d'
            sql = f"select cpu, iowait, usr_cpu, mem, mem_available, {disk_n}, {disk_r}, {disk_w}, {disk_d}, rec, trans, " \
                  f"net, tcp, retrans from \"{host}\" where time>'{startTime}' and time<'{endTime}' and " \
                  f"type='system' tz('Asia/Shanghai')"
            logger.info(f'Execute sql: {sql}')
            datas = connection.query(sql)
            if datas:
                post_data['types'] = 'system'
                for data in datas.get_points():
                    post_data['cpu_time'].append(data['time'][:19].replace('T', ' '))
                    post_data['cpu'].append(data['cpu'])
                    post_data['iowait'].append(data['iowait'])
                    post_data['usr_cpu'].append(data['usr_cpu'])
                    post_data['mem'].append(data['mem'])
                    post_data['mem_available'].append(data['mem_available'])
                    post_data['rec'].append(data['rec'])
                    post_data['trans'].append(data['trans'])
                    post_data['nic'].append(data['net'])
                    post_data['io'].append(data[disk_n])
                    post_data['disk_r'].append(data[disk_r])
                    post_data['disk_w'].append(data[disk_w])
                    post_data['disk_d'].append(data[disk_d])
                    post_data['tcp'].append(data['tcp'])
                    post_data['retrans'].append(data['retrans'])

            else:
                res['message'] = 'No monitoring data is found, please check the disk number or time setting.'
                res['code'] = 0

        res.update({'post_data': post_data})
        logger.info(f'Time consuming to query is {time.time() - s_time}')

        # lines = get_lines(post_data)      # Calculate percentile, 75%, 90%, 95%, 99%
        # res.update(lines)

    except Exception as err:
        logger.error(traceback.format_exc())
        res['message'] = str(err)
        res['code'] = 0

    del connection, post_data
    return res


def get_lines(datas):
    """
    Calculate percentile
    :param datas
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
