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
	result = os.popen('ps -ef|grep {}'.format(port)).readlines()[0]

	return result
