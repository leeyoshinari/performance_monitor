#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import json
import threading
import happybase
import config as cfg
from logger import logger
from request import Request


families = {"cpu": dict(), "mem": dict(), "jvm": dict(), "io": dict()}  # hbase


class Master(object):
	def __init__(self):
		self.request = Request()
		self._slaves = {'ip': ['127.0.0.1', 'localhost'], 'port': [], 'time': [], 'disk': [['sda1', 'sda2']]}

		t = threading.Thread(target=self.check_status, args=())     # 开启线程，检查已经注册的客户端是否在线
		t.start()

	@property
	def slaves(self):
		return self._slaves

	@slaves.setter
	def slaves(self, value):
		hosts = value.split('+')
		ip = hosts[0].split(':')[0]
		port = hosts[0].split(':')[1]
		disks = hosts[2].split('-')
		if ip in self._slaves['ip']:
			index = self._slaves['ip'].index(ip)
			self._slaves['port'][index] = port
			self._slaves['time'][index] = hosts[1]
			self._slaves['disk'][index] = disks
		else:
			self._slaves['ip'].append(ip)
			self._slaves['port'].append(port)
			self._slaves['time'].append(hosts[1])
			self._slaves['disk'].append(disks)

		connection = happybase.Connection(host=cfg.HBASE_IP, port=cfg.HBASE_PORT)
		try:
			connection.open()
			connection.create_table(ip.replace('.', ''), families=families)
			connection.close()
		except Exception as err:
			logger.error(err)
			connection.close()

	def check_status(self):
		"""
		检查客户端是否在线，不在线则剔除
		:return:
		"""
		while True:
			time.sleep(3)
			for i in range(len(self._slaves['ip'])):
				try:
					res = self.request.request('get', self._slaves['ip'][i], self._slaves['port'][i], 'checkStatus')
					if res.status_code == 200:
						break
					else:
						self._slaves['ip'].pop(i)
						self._slaves['port'].pop(i)
						self._slaves['time'].pop(i)
						self._slaves['disk'].pop(i)

				except Exception as err:
					logger.error(err)

					self._slaves['ip'].pop(i)
					self._slaves['port'].pop(i)
					self._slaves['time'].pop(i)
					self._slaves['disk'].pop(i)

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
				if response['code'] == 0:
					return response['data']
				else:
					logger.error(response['msg'])
					return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}
			else:
				logger.error(f'接口响应状态码为{res.status_code}')
				return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}
		except Exception as err:
			logger.error(err)
			return {'ygc': -1, 'ygct': -1, 'fgc': -1, 'fgct': -1, 'fygc': -1, 'ffgc': -1}
