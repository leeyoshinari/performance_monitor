#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import requests
from logger import logger, handle_exception


class Request(object):
    def __init__(self):
        pass

    def get(self, ip, port, interface, timeout):
        """get请求"""
        url = 'http://{}:{}/{}'.format(ip, port, interface)
        res = requests.get(url=url, timeout=timeout)
        return res

    def post(self, ip, port, interface, json, headers, timeout):
        """post请求"""
        if headers is None:
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json; charset=UTF-8"}

        url = 'http://{}:{}/{}'.format(ip, port, interface)
        res = requests.post(url=url, json=json, headers=headers, timeout=timeout)
        return res

    @handle_exception()
    def request(self, method, ip, port, interface, json=None, headers=None, timeout=None):
        """请求入口，目前仅支持get和post请求，其他请求可自行添加"""
        if timeout is None:
            timeout = 3

        if method == 'get':
            res = self.get(ip, port, interface, timeout)
        elif method == 'post':
            res = self.post(ip, port, interface, json, headers, timeout)
        else:
            logger.error('暂不支持其他请求方式')
            raise Exception('暂不支持其他请求方式')

        return res

    def __del__(self):
        pass
