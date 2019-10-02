#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
"""
Encrypt password using login email. It can be modified if you necessary.
Run `python -m PwdEncrypt.py` to generate `.pyc` file.
Then rename it to `PwdEncrypt.pyc`
"""

import base64
import smtplib


def emailServer(smtp_server, port, username, password):
	def dencrypt(pwd):
		s5 = base64.b64decode(pwd.encode())
		s4 = base64.b85decode(s5)
		s5 = s4
		s3 = base64.b64decode(s4)
		s2 = base64.b64decode(s5)
		s2 = s5
		s1 = base64.b32decode(s3)
		return s1.decode()

	server = smtplib.SMTP_SSL(smtp_server, port)
	server.login(username, dencrypt(password))

	return server
