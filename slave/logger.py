#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import os
import logging.handlers
from config import Config


cfg = Config()
LEVEL = cfg.getLogging('level')
backupcount = cfg.getLogging('backupCount')
log_path = cfg.getLogging('logPath')

if not os.path.exists(log_path):
	os.mkdir(log_path)

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

file_handler = logging.handlers.TimedRotatingFileHandler(
	os.path.join(log_path, 'monitor.log'), when='midnight', interval=1, backupCount=backupcount)
file_handler.suffix = '%Y-%m-%d.log'

# file_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
