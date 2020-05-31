#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import smtplib
import socket
from email.header import Header
from email.mime.text import MIMEText
from logger import logger, cfg


def sendEmail(msg):
    """
    邮件通知
    :param msg: email content
    :return:
    """
    try:
        sender_name = cfg.getEmail('senderNmae')
        sender_email = cfg.getEmail('senderEmail')
        receiver_name = cfg.getEmail('receiverName')
        receiver_email = cfg.getEmail('receiverEmail')
        password = cfg.getEmail('password')
        host = cfg.getEmail('SMTP')

        subject = cfg.getEmail('subject')
        s = "{0}".format(msg)

        msg = MIMEText(s, 'plain', 'utf-8')  # 中文参数需要‘utf-8’
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_name
        msg['To'] = receiver_name

        try:
            smtp = smtplib.SMTP_SSL(host, 465)
        except socket.error:
            smtp = smtplib.SMTP(host, 25)

        smtp.login(sender_email, password)
        smtp.sendmail(sender_email, receiver_email, msg.as_string())
        smtp.quit()
        logger.info('邮件发送成功, 请查收')
    except Exception as err:
        logger.error(f'邮件配置有误{err}')


if __name__ == '__main__':
    sendEmail(1)
