#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import time
import requests
from logger import logger
from request import Request


class Master(object):
	def __init__(self):
		self.request = Request()
		self._slaves = [['127.0.0.1:5556', '2020-01-01 08:08:08']]

	@property
	def slaves(self):
		return self._slaves

	@slaves.setter
	def slaves(self, value):
		self._slaves.append(value.split('+'))

	def check_status(self):
		for i in range(len(self._slaves)):
			times = 0
			while True:
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

				if times > 5:
					self._slaves.pop(i)
					break
