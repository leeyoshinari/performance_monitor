#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
"""
password为你的邮箱登陆密码，输入后，运行该程序，生成加密后的密码，然后将加密后的密码赋值到config.py文件中的PASSWORD。
例如：密码为123456，加密后为UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09，config.py中的PASSWORD='UjBWYVJFZE9RbFpIV1QwOVBUMDlQUT09'
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
