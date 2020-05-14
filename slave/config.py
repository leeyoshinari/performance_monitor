#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari

import os
import configparser


class Config(object):
	def __init__(self):
		self.cfg = configparser.ConfigParser()
		path = os.path.dirname(os.path.abspath(__file__))
		config_path = os.path.join(path, 'config.ini')
		self.cfg.read(config_path, encoding='utf-8')

	def getServer(self, key):
		if key == 'threadPool':
			return self.cfg.getint('server', key, fallback=None)
		else:
			return self.cfg.get('server', key, fallback=None)

	def getInflux(self, key):
		return self.cfg.get('influx', key, fallback=None)

	def getMaster(self, key):
		return self.cfg.get('master', key, fallback=None)

	def getLogging(self, key):
		if key == 'backupCount':
			return self.cfg.getint('logging', key, fallback=None)
		else:
			return self.cfg.get('logging', key, fallback=None)

	def getMonitor(self, key):
		if key == 'isJvmAlert' or key == 'isMemAlert':
			return self.cfg.getboolean('monitor', key, fallback=None)
		elif key == 'minMem':
			return self.cfg.getfloat('monitor', key, fallback=None)
		else:
			return self.cfg.getint('monitor', key, fallback=None)

	def __del__(self):
		pass
