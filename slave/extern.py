#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import time
import requests

import config as cfg
from logger import logger


def port_to_pid(port):
	"""
		port to pid useing `netstat`.
	"""
	pid = None
	try:
		result = os.popen(f'netstat -nlp|grep {port} |tr -s " "').readlines()
		flag = f':{port}'
		res = [line.strip() for line in result if flag in line]
		logger.debug(res[0])
		p = res[0].split(' ')
		pp = p[3].split(':')[-1]
		if str(port) == pp:
			pid = p[p.index('LISTEN') + 1].split('/')[0]
	except Exception as err:
		logger.error(err)

	return pid


def register():
	url = f'http://{cfg.SERVER_IP}:{cfg.SERVER_PORT}/Register'

	header = {
		"Accept": "application/json, text/plain, */*",
		"Accept-Encoding": "gzip, deflate",
		"Content-Type": "application/json; charset=UTF-8"}

	post_data = {
		'host': cfg.IP,
		'port': cfg.PORT
	}

	try:
		res = requests.post(url=url, data=post_data, headers=header)
		return res.status_code
	except Exception as err:
		logger.error(err)
		time.sleep(5)
		return register()


def notification(port=None, msg=None):
	url = f'http://{cfg.SERVER_IP}:{cfg.SERVER_PORT}/Notification'

	header = {
		"Accept": "application/json, text/plain, */*",
		"Accept-Encoding": "gzip, deflate",
		"Content-Type": "application/json; charset=UTF-8"}

	post_data = {
		'host': cfg.IP,
		'port': port,
		'msg': msg
	}

	try:
		res = requests.post(url=url, data=post_data, headers=header)
	except Exception as err:
		logger.error(err)
