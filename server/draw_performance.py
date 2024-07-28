#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import time
import traceback
import influxdb_client
from logger import logger, cfg


date_format = "%Y-%m-%d %H:%M:%S"
UTC_format = "%Y-%m-%dT%H:%M:%SZ"


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
        'load1': [],
        'load5': [],
        'load15': [],
        'disk': disk}

    res = {'code': 1, 'flag': 1, 'message': 'Successful!'}

    connection = influxdb_client.InfluxDBClient(url=cfg.getInflux('url'), token=cfg.getInflux('token'), org=cfg.getInflux('org'))
    query_api = connection.query_api()

    try:
        if startTime and endTime:     # If there is a start time and an end time
            startTime = local_date2utc_date(startTime)
            endTime = local_date2utc_date(endTime)
        elif startTime is None and endTime is None:  # If the start time and end time do not exist, use the default time.
            startTime = local_date2utc_date('2024-05-20 20:20:20')
            endTime = local_date2utc_date(time.strftime(date_format))
        else:   # If the end time does not exist, the current time is used
            endTime = local_date2utc_date(time.strftime(date_format))

        s_time = time.time()
        if port:
            sql = f'''
            from (bucket: "{cfg.getInflux('bucket')}")
                |> range(start: {startTime}, stop: {endTime})
                |> filter(fn: (r) => r._measurement == "{host}" and r.type == "{port}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> map(fn: (r) => ({{ r with _time: uint(v: r._time) }}))
                |> keep(columns: ["_time", "cpu", "wait_cpu", "mem", "tcp", "jvm", "iodelay", "rKbs", "wKbs", "net", "rec", "trans", "close_wait", "time_wait"])
            '''
            datas = query_api.query(org=cfg.getInflux('org'), query=sql)
            if datas:
                post_data['types'] = 'port'
                for data in datas:
                    for record in data.records:
                        post_data['cpu_time'].append(time.strftime(date_format, time.localtime(int(record.values['_time']/1000000000))))
                        post_data['cpu'].append(record.values['cpu'])
                        post_data['iowait'].append(record.values['wait_cpu'])
                        post_data['mem'].append(record.values['mem'])
                        post_data['tcp'].append(record.values['tcp'])
                        post_data['jvm'].append(record.values['jvm'])
                        post_data['io'].append(record.values['iodelay'])
                        post_data['disk_r'].append(record.values['rKbs'])
                        post_data['disk_w'].append(record.values['wKbs'])
                        post_data['nic'].append(record.values['net'])
                        post_data['rec'].append(record.values['rec'])
                        post_data['trans'].append(record.values['trans'])
                        post_data['close_wait'].append(record.values['close_wait'])
                        post_data['time_wait'].append(record.values['time_wait'])
            else:
                res['message'] = f'No monitoring data of the port {port} is found, ' \
                                 f'please check the port or time setting.'
                res['code'] = 0
        if pid:
            pass

        if system and disk:
            disk_n = disk.replace('-', '')
            disk_r = disk_n + '_r'
            disk_w = disk_n + '_w'
            disk_d = disk_n + '_d'
            sql = f'''
                from(bucket: "{cfg.getInflux('bucket')}")
                    |> range(start: {startTime}, stop: {endTime})
                    |> filter(fn: (r) => r._measurement == "{host}" and r["type"] == "system")
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                    |> map(fn: (r) => ({{ r with _time: uint(v: r._time) }}))
                    |> keep(columns: ["_time", "cpu", "iowait", "usr_cpu", "mem", "mem_available", "{disk_n}", "{disk_r}", "{disk_w}", "{disk_d}", "rec", "trans", "net", "tcp", "retrans", "load1", "load5", "load15"])
                '''
            datas = query_api.query(org=cfg.getInflux('org'), query=sql)
            if datas:
                post_data['types'] = 'system'
                for data in datas:
                    for record in data.records:
                        post_data['cpu_time'].append(time.strftime(date_format, time.localtime(int(record.values['_time']/1000000000))))
                        post_data['cpu'].append(record.values['cpu'])
                        post_data['iowait'].append(record.values['iowait'])
                        post_data['usr_cpu'].append(record.values['usr_cpu'])
                        post_data['mem'].append(record.values['mem'])
                        post_data['mem_available'].append(record.values['mem_available'])
                        post_data['rec'].append(record.values['rec'])
                        post_data['trans'].append(record.values['trans'])
                        post_data['nic'].append(record.values['net'])
                        post_data['io'].append(record.values[disk_n])
                        post_data['disk_r'].append(record.values[disk_r])
                        post_data['disk_w'].append(record.values[disk_w])
                        post_data['disk_d'].append(record.values[disk_d])
                        post_data['tcp'].append(record.values['tcp'])
                        post_data['retrans'].append(record.values['retrans'])
                        post_data['load1'].append(record.values['load1'])
                        post_data['load5'].append(record.values['load5'])
                        post_data['load15'].append(record.values['load15'])

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


def local_date2utc_date(date_str):
    time_struct = time.strptime(date_str, date_format)
    timestamp = time.mktime(time_struct)
    return time.strftime(UTC_format, time.gmtime(timestamp))
