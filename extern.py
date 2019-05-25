#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os


def ports_to_pids(port):
	pids = []
	ports = port.split(',')
	for p in ports:
		pids.append(port_to_pid(p))

	return pids


def port_to_pid(port):
	pid = None
	result = os.popen('ps -ef|grep {} |tr -s " "'.format(port)).readlines()
	res = [line for line in result if 'grep' not in line]
	if str(port) in res[0]:
		pid = res[0].split(' ')[1]

	return pid
