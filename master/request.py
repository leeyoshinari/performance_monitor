#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import json
import requests
import config as cfg
from logger import logger


class Request(object):
	def __init__(self):
		pass

	def get(self, host, interface, timeout):
		"""get请求"""
		url = 'http://{}:/{}'.format(host, interface)
		res = requests.get(url=url, timeout=timeout)
		return res

	def post(self, host, interface, data, headers, timeout):
		"""post请求"""
		if headers is None:
			headers = {
				"Accept": "application/json, text/plain, */*",
				"Accept-Encoding": "gzip, deflate",
				"Content-Type": "application/json; charset=UTF-8"}

		url = 'http://{}:/{}'.format(host, interface)
		res = requests.post(url=url, data=data, headers=headers, timeout=timeout)
		return res

	def request(self, method, host, interface, data=None, headers=None, timeout=None):
		"""请求入口，目前仅支持get和post请求，其他请求可自行添加"""
		if timeout is None:
			timeout = 3

		try:
			if method == 'get':
				res = self.get(host, interface, timeout)
			elif method == 'post':
				res = self.post(host, interface, data, headers, timeout)
			else:
				logger.error('暂不支持其他请求方式')
				raise Exception('暂不支持其他请求方式')

			return res

		except Exception as err:
			logger.error(err)
			raise Exception(err)

	def __del__(self):
		pass
