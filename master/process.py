#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import json
import threading
import influxdb
from logger import logger, cfg
from request import Request


class Process(object):
	def __init__(self):
		self.request = Request()
		self._slaves = {'ip': [], 'port': [], 'system': [], 'cpu': [], 'mem': [], 'time': [], 'disk': [], 'nic': []}

		# 设置数据库过期时间
		conn = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
		                               cfg.getInflux('password'), cfg.getInflux('database'))
		conn.query(f'alter retention policy "autogen" on "{cfg.getInflux("database")}" duration {cfg.getInflux("expiryTime")}w default;')
		logger.info(f'设置数据过期时间为{cfg.getInflux("expiryTime")}周。')

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
			logger.info(f'{ip}服务器已注册')
			pass
		else:
			self._slaves['ip'].append(value['host'])
			self._slaves['port'].append(value['port'])
			self._slaves['system'].append(value['system'])
			self._slaves['cpu'].append(value['cpu'])
			self._slaves['mem'].append(value['mem'])
			self._slaves['time'].append(value['time'])
			self._slaves['disk'].append(value['disk'].split(','))
			self._slaves['nic'].append(value['nic'])
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
						self._slaves['system'].pop(i)
						self._slaves['cpu'].pop(i)
						self._slaves['mem'].pop(i)
						self._slaves['time'].pop(i)
						self._slaves['disk'].pop(i)
						self._slaves['nic'].pop(i)
						logger.warning(f"客户端{ip}服务器状态异常，已下线")
						break

				except Exception as err:
					logger.error(err)
					ip = self._slaves['ip'].pop(i)
					self._slaves['port'].pop(i)
					self._slaves['system'].pop(i)
					self._slaves['cpu'].pop(i)
					self._slaves['mem'].pop(i)
					self._slaves['time'].pop(i)
					self._slaves['disk'].pop(i)
					self._slaves['nic'].pop(i)
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

	def get_monitor(self, host=None):
		"""
		获取监控端口列表接口
		:return:
		"""
		monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
		try:
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
