#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import requests
import happybase
import config as cfg
from logger import logger
from request import Request


families = {"cpu": dict(), "mem": dict(), "jvm": dict(), "io": dict()}


class Master(object):
	def __init__(self):
		self.request = Request()
		self._slaves = []

		# self.pool = happybase.ConnectionPool(size=1, host=cfg.HBASE_IP, port=cfg.HBASE_PORT)

	@property
	def slaves(self):
		return self._slaves

	@slaves.setter
	def slaves(self, value):
		host = value.split('+')[0]
		starttime = value.split('+')[1]
		ip = host.split(':')[0]
		connection = happybase.Connection(host=cfg.HBASE_IP, port=cfg.HBASE_PORT)
		try:
			connection.open()
			connection.create_table(ip.replace('.', ''), families=families)
			self._slaves.append([host, starttime])
			connection.close()
		except Exception as err:
			logger.error(err)
			connection.close()

	def check_status(self):
		while True:
			time.sleep(3)
			for i in range(len(self._slaves)):
				times = 0
				try:
					res = self.request.request('get', self._slaves[i], 'checkStatus')
					if res.status_code == 200:
						break
					else:
						times += 1
						time.sleep(1)
				except Exception as err:
					logger.error(err)
					times += 1
					time.sleep(1)

				if times > 2:
					self._slaves.pop(i)
					break
