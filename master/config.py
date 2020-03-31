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
		return self.cfg.get('server', key)

	def getInflux(self, key):
		if key == 'expiryTime':
			return self.cfg.getint('influx', key)
		else:
			return self.cfg.get('influx', key)

	def getLogging(self, key):
		if key == 'backupCount':
			return self.cfg.getint('logging', key)
		else:
			return self.cfg.get('logging', key)

	def getEmail(self, key):
		if key == 'receiverEmail':
			emails = self.cfg.get('email', key)
			return [a.strip() for a in emails.split(',')]
		else:
			return self.cfg.get('email', key)

	def __del__(self):
		pass


if __name__ == '__main__':
	c = Config()
	print(c.getEmail('smtp'))
