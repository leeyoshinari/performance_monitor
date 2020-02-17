#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import json
import threading
import influxdb
import config as cfg
from logger import logger
from request import Request


class Master(object):
	def __init__(self):
		self.request = Request()
		self._slaves = {'ip': [], 'port': [], 'time': [], 'disk': []}

		# 设置数据库过期时间
		conn = influxdb.InfluxDBClient(cfg.INFLUX_IP, cfg.INFLUX_PORT, cfg.INFLUX_USERNAME,
		                               cfg.INFLUX_PASSWORD, cfg.INFLUX_DATABASE)
		conn.query(f'alter retention policy "autogen" on "{cfg.INFLUX_DATABASE}" duration {cfg.EXPIRY_TIME}w default;')
		logger.info(f'设置数据过期时间为{cfg.EXPIRY_TIME}周。')

		t = threading.Thread(target=self.check_status, args=())  # 开启线程，检查已经注册的客户端是否在线
		t.start()

	@property
	def slaves(self):
		return self._slaves

	@slaves.setter
	def slaves(self, value):
		logger.debug(f'客户端注册数据为{value}')
		hosts = value.split('+')
		ip = hosts[0].split(':')[0]
		port = hosts[0].split(':')[1]
		disks = hosts[2].split('-')
		if ip in self._slaves['ip']:
			logger.info(f'{ip}服务器已注册')
			pass
		else:
			self._slaves['ip'].append(ip)
			self._slaves['port'].append(port)
			self._slaves['time'].append(hosts[1])
			self._slaves['disk'].append(disks)
			logger.info(f'{ip}服务器注册成功')

	def check_status(self):
		"""
		检查客户端是否在线，不在线则剔除
		:return:
		"""
		while True:
			time.sleep(5)
			for i in range(len(self._slaves['ip'])):
				try:
					res = self.request.request('get', self._slaves['ip'][i], self._slaves['port'][i], 'checkStatus')
					if res.status_code == 200:
						logger.info(f"客户端{self._slaves['ip'][i]}服务器状态正常")
						continue
					else:
						ip = self._slaves['ip'].pop(i)
						self._slaves['port'].pop(i)
						self._slaves['time'].pop(i)
						self._slaves['disk'].pop(i)
						logger.warning(f"客户端{ip}服务器状态异常，已下线")
						break

				except Exception as err:
					logger.error(err)
					ip = self._slaves['ip'].pop(i)
					self._slaves['port'].pop(i)
					self._slaves['time'].pop(i)
					self._slaves['disk'].pop(i)
					logger.warning(f"客户端{ip}服务器状态异常，已下线")
					break

	def get_gc(self, ip, port, interface):
		"""
		获取端口的垃圾回收数据，访问地址 http://ip:port/interface
		:param ip: 客户端服务器IP
		:param port: 客户端启用端口
		:param interface: 访问接口名称
		:return:
		"""
		try:
			res = self.request.request('get', ip, port, interface)
			if res.status_code == 200:
				response = json.loads(res.content.decode())
				logger.debug(f'获取{ip}服务器的{port}端口的gc数据为{response}')
				if response['code'] == 0:
					return response['data']
				else:
					logger.error(response['msg'])
					return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}
			else:
				logger.error(f'获取{ip}服务器的{port}端口的gc数据的接口响应状态码为{res.status_code}')
				return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}
		except Exception as err:
			logger.error(err)
			return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}

	def get_monitor(self):
		"""
		获取监控端口列表接口
		:return:
		"""
		monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
		try:
			for ip, port in zip(self._slaves['ip'], self._slaves['port']):  # 遍历所有客户端IP地址，获取端口监控列表
				post_data = {
					'host': ip,
				}
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

		return monitor_list
