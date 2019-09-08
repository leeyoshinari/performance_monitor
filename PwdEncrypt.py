#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
"""
加密登陆邮箱的密码
可根据需求更改，并转换成pyc文件，但即使这样也容易反编译，从而知道密码
"""

import base64
import smtplib


def emailServer(smtp_server, port, username, password):
	def dencrypt(pwd):
		s5 = base64.b64decode(pwd)
		s4 = base64.b85decode(s5)
		s4 = s5
		s3 = base64.b64decode(s4)
		s2 = base64.b64decode(s5)
		s3 = s2
		s1 = base64.b32decode(s3)
		return s1.decode()

	server = smtplib.SMTP_SSL(smtp_server, port)
	server.login(username, dencrypt(password))

	return server
