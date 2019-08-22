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
	logger.logger.info(msg)
	message = MIMEMultipart()
	if msg['smtp_server'] == 'smtp.sina.com':   # 新浪邮箱的Header不能使用utf-8的编码方式
		message['From'] = Header(cfg.SENDER_NAME)    # 发件人名字
	else:
		message['From'] = Header(cfg.SENDER_NAME, 'utf-8')
	message['To'] = Header(cfg.RECEIVER_NAME, 'utf-8')       # 收件人名字
	message['Subject'] = Header(msg['subject'], 'utf-8')        # 邮件主题

	email_text = MIMEText(msg['fail_test'], 'html', 'utf-8')
	message.attach(email_text)      # 添加邮件正文

	try:
		# server = smtplib.SMTP_SSL(msg['smtp_server'], 465)
		# server.login(msg['sender'], msg['password'])      # 登陆邮箱
		server = emailServer(cfg.SMTP_SERVER, 465, cfg.SENDER_EMAIL, cfg.PASSWORD)
		server.sendmail(cfg.SENDER_EMAIL, cfg.RECEIVER_EMAIL, message.as_string())     # 发送邮件
		server.quit()
		logger.logger.info('Send email successfully.')
	except Exception as err:
		logger.logger.error(traceback.format_exc())
		sendMsg(msg)
