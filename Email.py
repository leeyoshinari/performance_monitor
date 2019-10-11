#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import traceback
from email.mime.text import MIMEText
from email.header import Header

from PwdEncrypt import emailServer
from logger import logger
import config as cfg


def sendMsg(msg):
	SMTP_SERVER = cfg.SMTP_SERVER
	SENDER_NAME = cfg.SENDER_NAME
	SENDER_EMAIL = cfg.SENDER_EMAIL
	PASSWORD = cfg.PASSWORD
	RECEIVER_NAME = cfg.RECEIVER_NAME
	RECEIVER_EMAIL = cfg.RECEIVER_EMAIL
	text = f"{cfg.IP} \n {msg['msg']}，attention！"
	message = MIMEText(text, 'plain', 'utf-8')
	if SMTP_SERVER == 'smtp.sina.com':   # sina can't use `utf-8` in `Header`.
		message['From'] = Header(SENDER_NAME)    # sender name
	else:
		message['From'] = Header(SENDER_NAME, 'utf-8')
	message['To'] = Header(RECEIVER_NAME, 'utf-8')       # receiver name
	message['Subject'] = Header('Warning', 'utf-8')        # subject

	try:
		# server = smtplib.SMTP_SSL(msg['smtp_server'], 465)
		# server.login(msg['sender'], msg['password'])      # login
		server = emailServer(SMTP_SERVER, 465, SENDER_EMAIL, PASSWORD)
		server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())     # send email
		server.quit()
		logger.info('Send email successfully.')
	except Exception as err:
		logger.error(traceback.format_exc())
		sendMsg(msg)
