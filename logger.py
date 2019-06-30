#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import os
import datetime
import logging.handlers
import config as cfg


class logger(object):
	LEVEL = cfg.LEVEL
	log_path = 'logs'

	if not os.path.exists(log_path):
		os.mkdir(log_path)

	"""
	mode=1: 日志按文件大小切分，默认大小为10M，默认保存最近10个日志；
	mode=2: 日志按时间切分，默认为按天切分，默认保存最近10个日志；
	mode=3: 日志输出到控制台；
	"""
	mode = 1

	log_level = {
		'DEBUG': logging.DEBUG,
		'INFO': logging.INFO,
		'WARNING': logging.WARNING,
		'ERROR': logging.ERROR,
		'CRITICAL': logging.CRITICAL
	}

	logger = logging.getLogger()
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d] - %(message)s')
	logger.setLevel(level=log_level.get(LEVEL))

	if mode == 1:
		current_day = datetime.datetime.now().strftime('%Y-%m-%d')
		log_name = os.path.join(log_path, current_day + '.log')
		file_handler = logging.handlers.RotatingFileHandler(filename=log_name, maxBytes=10*1024*1024, backupCount=10)

	if mode == 2:
		file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_path, 'monitor.log'), when='D', interval=1, backupCount=10)
		file_handler.suffix = '%Y-%m-%d.log'

	if mode == 3:
		file_handler = logging.StreamHandler()

	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
