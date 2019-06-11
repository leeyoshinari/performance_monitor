#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os


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
	pid = None
	try:
		result = os.popen('lsof -i:{} |tr -s " "'.format(port)).readlines()[1]
		res = result.strip().split(' ')
		pid = res[1]
	except Exception as err:
		pass

	return pid
