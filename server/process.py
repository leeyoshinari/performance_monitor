#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import json
import threading
import influxdb
from logger import logger, cfg, handle_exception
from request import Request


class Process(object):
    def __init__(self):
        self.request = Request()
        self._slaves = {'ip': [], 'port': [], 'system': [], 'cpu': [], 'mem': [], 'time': [], 'disk': [], 'nic': [],
                        'network_speed': [], 'disk_size': [], 'mem_usage': [], 'cpu_usage': [], 'disk_usage': []}

        # data expiration time
        conn = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
                                       cfg.getInflux('password'), cfg.getInflux('database'))
        conn.query(f'alter retention policy "autogen" on "{cfg.getInflux("database")}" duration '
                   f'{cfg.getInflux("expiryTime")}d REPLICATION 1 SHARD DURATION {cfg.getInflux("shardDuration")} default;')
        logger.info(f'Data expiration time is {cfg.getInflux("expiryTime")} days')

        t = threading.Thread(target=self.check_status, args=())  # Check the online status of the clients.
        t.start()

    @property
    def slaves(self):
        return self._slaves

    @slaves.setter
    def slaves(self, value):
        logger.debug(f'The client registration data is {value}')
        ip = value['host']
        if ip in self._slaves['ip']:
            ind = self._slaves['ip'].index(ip)
            self._slaves['cpu_usage'][ind] = value['cpu_usage']
            self._slaves['mem_usage'][ind] = value['mem_usage']
            self._slaves['disk_usage'][ind] = value['disk_usage']
            self._slaves['time'][ind] = time.time()
            logger.info(f'{ip} server has been registered.')
        else:
            self._slaves['ip'].append(value['host'])
            self._slaves['port'].append(value['port'])
            self._slaves['system'].append(value['system'])
            self._slaves['cpu'].append(value['cpu'])
            self._slaves['mem'].append(value['mem'])
            self._slaves['time'].append(time.time())
            self._slaves['disk'].append(value['disks'].split(','))
            self._slaves['nic'].append(value['nic'])
            self._slaves['disk_size'].append(value['disk_size'])
            self._slaves['network_speed'].append(value['network_speed'])
            self._slaves['cpu_usage'].append((value['cpu_usage']))
            self._slaves['mem_usage'].append((value['mem_usage']))
            self._slaves['disk_usage'].append((value['disk_usage']))
            logger.info(f'{ip} server registered successfully!')

    def check_status(self):
        """
         Check the online status of the clients, and remove it when offline.
        :return:
        """
        while True:
            time.sleep(5)
            for i in range(len(self._slaves['ip'])):
                if time.time() - self._slaves['time'][i] > 12:
                    ip = self._slaves['ip'].pop(i)
                    self._slaves['port'].pop(i)
                    self._slaves['system'].pop(i)
                    self._slaves['cpu'].pop(i)
                    self._slaves['mem'].pop(i)
                    self._slaves['time'].pop(i)
                    self._slaves['disk'].pop(i)
                    self._slaves['nic'].pop(i)
                    self._slaves['network_speed'].pop(i)
                    self._slaves['disk_size'].pop(i)
                    self._slaves['cpu_usage'].pop(i)
                    self._slaves['mem_usage'].pop(i)
                    self._slaves['disk_usage'].pop(i)
                    logger.warning(f"The client server {ip} is in an abnormal state, and has been offline.")
                    break

    @handle_exception(is_return=True, default_value=[-1, -1, -1, -1, '-', -1])
    def get_gc(self, ip, port, interface):
        """
        Get GC data of port
        :param ip: clent IP
        :param port: client monitoring port
        :param interface: interface
        :return:
        """
        res = self.request.request('get', ip, port, interface)
        if res.status_code == 200:
            response = json.loads(res.content.decode())
            logger.debug(f'The GC data of the port {port} of the server {ip} is {response}')
            if response['code'] == 0:
                return response['data']
            else:
                logger.error(response['msg'])
                return [-1, -1, -1, -1, '-', -1]
        else:
            logger.error(f'The response status code of getting GC data of the '
                         f'port {port} of the server {ip} is {res.status_code}.')
            return [-1, -1, -1, -1, '-', -1]

    @handle_exception(is_return=True, default_value={'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []})
    def get_monitor(self, host=None):
        """
         Get the list of monitoring ports.
        :return:
        """
        monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
        if host:
            post_data = {
                'host': host,
            }
            port = self._slaves['port'][self._slaves['ip'].index(host)]
            res = self.request.request('post', host, port, 'getMonitor', json=post_data)
            if res.status_code == 200:
                response = json.loads(res.content.decode())
                logger.debug(f'The return value of server {host} of getting monitoring list is {response}.')
                if response['code'] == 0:
                    monitor_list['host'] += response['data']['host']
                    monitor_list['port'] += response['data']['port']
                    monitor_list['pid'] += response['data']['pid']
                    monitor_list['isRun'] += response['data']['isRun']
                    monitor_list['startTime'] += response['data']['startTime']
        else:
            for ip, port in zip(self._slaves['ip'], self._slaves['port']):  # Traverse all clients IP addresses
                post_data = {
                    'host': ip,
                }
                try:
                    res = self.request.request('post', ip, port, 'getMonitor', json=post_data)
                    if res.status_code == 200:
                        response = json.loads(res.content.decode())
                        logger.debug(f'The return value of server {ip} of getting monitoring list is {response}')
                        if response['code'] == 0:
                            monitor_list['host'] += response['data']['host']
                            monitor_list['port'] += response['data']['port']
                            monitor_list['pid'] += response['data']['pid']
                            monitor_list['isRun'] += response['data']['isRun']
                            monitor_list['startTime'] += response['data']['startTime']
                except Exception as err:
                    logger.error(err)
                    continue

        return monitor_list
