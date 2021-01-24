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

        # 设置数据库过期时间
        conn = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
                                       cfg.getInflux('password'), cfg.getInflux('database'))
        conn.query(f'alter retention policy "autogen" on "{cfg.getInflux("database")}" duration '
                   f'{cfg.getInflux("expiryTime")}d REPLICATION 1 SHARD DURATION {cfg.getInflux("shardDuration")} default;')
        logger.info(f'设置数据过期时间为{cfg.getInflux("expiryTime")}天。')

        t = threading.Thread(target=self.check_status, args=())  # 开启线程，检查已经注册的客户端是否在线
        t.start()

    @property
    def slaves(self):
        return self._slaves

    @slaves.setter
    def slaves(self, value):
        logger.debug(f'客户端注册数据为{value}')
        ip = value['host']
        if ip in self._slaves['ip']:
            ind = self._slaves['ip'].index(ip)
            self._slaves['cpu_usage'][ind] = value['cpu_usage']
            self._slaves['mem_usage'][ind] = value['mem_usage']
            self._slaves['disk_usage'][ind] = value['disk_usage']
            self._slaves['time'][ind] = time.time()
            logger.info(f'{ip}服务器已注册')
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
            logger.info(f'{ip}服务器注册成功')

    def check_status(self):
        """
        检查客户端是否在线，不在线则剔除
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
                    logger.warning(f"客户端{ip}服务器状态异常，已下线")
                    break

    @handle_exception(is_return=True, default_value=[-1, -1, -1, -1, '-', -1])
    def get_gc(self, ip, port, interface):
        """
        获取端口的垃圾回收数据，访问地址 http://ip:port/interface
        :param ip: 客户端服务器IP
        :param port: 客户端启用端口
        :param interface: 访问接口名称
        :return:
        """
        res = self.request.request('get', ip, port, interface)
        if res.status_code == 200:
            response = json.loads(res.content.decode())
            logger.debug(f'获取{ip}服务器的{port}端口的gc数据为{response}')
            if response['code'] == 0:
                return response['data']
            else:
                logger.error(response['msg'])
                return [-1, -1, -1, -1, '-', -1]
        else:
            logger.error(f'获取{ip}服务器的{port}端口的gc数据的接口响应状态码为{res.status_code}')
            return [-1, -1, -1, -1, '-', -1]

    @handle_exception(is_return=True, default_value={'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []})
    def get_monitor(self, host=None):
        """
        获取监控端口列表接口
        :return:
        """
        monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
        if host:
            post_data = {
                'host': host,
            }
            port = self._slaves['port'][self._slaves['ip'].index(host)]
            res = self.request.request('post', host, port, 'getMonitor', json=post_data)  # 通过url获取
            if res.status_code == 200:
                response = json.loads(res.content.decode())
                logger.debug(f'{host}服务器获取监控列表接口返回值为{response}')
                if response['code'] == 0:
                    # 拼接端口监控列表
                    monitor_list['host'] += response['data']['host']
                    monitor_list['port'] += response['data']['port']
                    monitor_list['pid'] += response['data']['pid']
                    monitor_list['isRun'] += response['data']['isRun']
                    monitor_list['startTime'] += response['data']['startTime']
        else:
            for ip, port in zip(self._slaves['ip'], self._slaves['port']):  # 遍历所有客户端IP地址，获取端口监控列表
                post_data = {
                    'host': ip,
                }
                try:
                    res = self.request.request('post', ip, port, 'getMonitor', json=post_data)  # 通过url获取
                    if res.status_code == 200:
                        response = json.loads(res.content.decode())
                        logger.debug(f'{ip}服务器获取监控列表接口返回值为{response}')
                        if response['code'] == 0:
                            # 拼接端口监控列表
                            monitor_list['host'] += response['data']['host']
                            monitor_list['port'] += response['data']['port']
                            monitor_list['pid'] += response['data']['pid']
                            monitor_list['isRun'] += response['data']['isRun']
                            monitor_list['startTime'] += response['data']['startTime']
                except Exception as err:
                    logger.error(err)
                    continue

        return monitor_list
