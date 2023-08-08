#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import os
import traceback
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
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(filename)s[line:%(lineno)d] - %(message)s')
logger.setLevel(level=log_level.get(LEVEL))

file_handler = logging.handlers.TimedRotatingFileHandler(
    os.path.join(log_path, 'monitor.log'), when='midnight', interval=1, backupCount=backupcount)
file_handler.suffix = '%Y-%m-%d.log'
# file_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def handle_exception(errors=(Exception, ), is_return=False, is_return_error_msg=False, default_value=None):
    """
    Handle exception, throw an exception, or return a value.
    :param errors: Exception type
    :param is_return: Whether to return a value. Default False, if exception, don't throw an exception,
    but return a value.
    :param is_return_error_msg: Whether to return an error-msg. Default False, return a 'default_value'.
    If True, return an error-msg.
    :param default_value: If 'is_return' is True, return 'default_value'.
    :return: 'default_value' or error-msg
    """
    def decorator(func):
        def decorator1(*args, **kwargs):
            if is_return:
                try:
                    return func(*args, **kwargs)
                except errors:
                    logger.error(traceback.format_exc())
                    if is_return_error_msg:
                        return traceback.format_exc()
                    else:
                        return default_value
            else:
                try:
                    return func(*args, **kwargs)
                except errors:
                    raise

        return decorator1
    return decorator
