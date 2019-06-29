#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
from logger import logger


def ports_to_pids(port):
	pids = []
	ports = port.split(',')
	for p in ports:
		pid = port_to_pid(p)
		if pid:
			pids.append(pid)
		else:
			return str(p)

	return pids


def port_to_pid(port):
	"""
	Get PID by port. It uses `netstat`.
	"""
	pid = None
	try:
		result = os.popen('netstat -nlp|grep {} |tr -s " "'.format(port)).readlines()
		res = [line.strip() for line in result if str(port) in line]
		logger.logger.debug(res[0])
		p = res[0].split(' ')
		pp = p[3].split(':')[-1]
		if str(port) == pp:
			pid = p[-1].split('/')[0]
	except Exception as err:
		logger.logger.error(err)

	return pid


'''def port_to_pid(port):
	pid = None
	try:
		result = os.popen('lsof -i:{} |tr -s " "'.format(port)).readlines()[1]
		res = result.strip().split(' ')
		pid = res[1]
	except Exception as err:
		pass

	return pid
'''