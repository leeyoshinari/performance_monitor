#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari

import configparser


class Config(object):
	def __init__(self):
		self.cfg = configparser.ConfigParser()
		self.cfg.read('config.ini', encoding='utf-8')

	def getServer(self, key):
		return self.cfg.get('server', key, fallback=None)

	def getInflux(self, key):
		if key == 'expiryTime':
			return self.cfg.getint('influx', key, fallback=15)
		else:
			return self.cfg.get('influx', key, fallback=None)

	def getLogging(self, key):
		if key == 'backupCount':
			return self.cfg.getint('logging', key, fallback=None)
		else:
			return self.cfg.get('logging', key, fallback=None)

	def getEmail(self, key):
		if key == 'receiverEmail':
			emails = self.cfg.get('email', key, fallback='')
			return [a.strip() for a in emails.split(',')]
		else:
			return self.cfg.get('email', key, fallback=None)

	def __del__(self):
		pass


if __name__ == '__main__':
	c = Config()
	print(c.getEmail('smtp'))
