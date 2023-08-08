#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari

import os
import traceback
from logger import logger, cfg


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


@handle_exception(is_return=True, default_value='127.0.0.1')
def get_ip():
    """
    Get server's IP address
    :return: IP address
    """
    if cfg.getAgent('host'):
        IP = cfg.getAgent('host')
    else:
        with os.popen("hostname -I |awk '{print $1}'") as p:
            result = p.readlines()
        logger.debug(result)
        if result:
            IP = result[0].strip()
            logger.info(f'The IP address is: {IP}')
        else:
            logger.warning('Server IP address not found!')
            IP = '127.0.0.1'
    return IP
