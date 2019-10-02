#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from PwdEncrypt import emailServer
from logger import logger
import config as cfg


def sendMsg(msg):
	logger.info(msg)
	message = MIMEMultipart()
	if cfg.SMTP_SERVER == 'smtp.sina.com':   # sina can't use `utf-8` in `Header`.
		message['From'] = Header(cfg.SENDER_NAME)    # sender name
	else:
		message['From'] = Header(cfg.SENDER_NAME, 'utf-8')
	message['To'] = Header(cfg.RECEIVER_NAME, 'utf-8')       # receiver name
	message['Subject'] = Header('Warning', 'utf-8')        # subject

	text = f"{cfg.IP} \n {msg['msg']}，attention！"
	email_text = MIMEText(text, 'plain', 'utf-8')
	message.attach(email_text)      # text

	try:
		# server = smtplib.SMTP_SSL(msg['smtp_server'], 465)
		# server.login(msg['sender'], msg['password'])      # login
		server = emailServer(cfg.SMTP_SERVER, 465, cfg.SENDER_EMAIL, cfg.PASSWORD)
		server.sendmail(cfg.SENDER_EMAIL, cfg.RECEIVER_EMAIL, message.as_string())     # send email
		server.quit()
		logger.info('Send email successfully.')
	except Exception as err:
		logger.error(traceback.format_exc())
		sendMsg(msg)
