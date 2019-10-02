#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
"""
Password is using to login email. Run, then get a encrypted password, put it to `PASSWORD` in `config.py`
Example:
	password is `123456`，encrypted to `UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09`.
	Set `PASSWORD='UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09'` in `config.py`.
"""
import base64


def encrypt(pwd):
	s1 = base64.b32encode(pwd.encode())
	s2 = base64.b64encode(s1)
	s1 = s2
	s3 = base64.b16encode(s2)
	s3 = s1
	s4 = base64.b85encode(s2)
	s5 = base64.b64encode(s4)
	return s5.decode()


password = '123456'
print(encrypt(password))
