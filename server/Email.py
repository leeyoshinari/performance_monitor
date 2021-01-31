#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import smtplib
import socket
from email.header import Header
from email.mime.text import MIMEText
from logger import logger, cfg, handle_exception


@handle_exception()
def sendEmail(msg):
    """
     Send email
    :param msg: email content
    :return:
    """
    sender_name = cfg.getEmail('senderNmae')
    sender_email = cfg.getEmail('senderEmail')
    receiver_name = cfg.getEmail('receiverName')
    receiver_email = cfg.getEmail('receiverEmail')
    password = cfg.getEmail('password')
    host = cfg.getEmail('SMTP')

    subject = cfg.getEmail('subject')
    s = "{0}".format(msg)

    message = MIMEText(s, 'plain', 'utf-8')  # Chinese required 'utf-8'
    message['Subject'] = Header(subject, 'utf-8')
    message['From'] = Header(sender_name)
    message['To'] = Header(receiver_name, 'utf-8')

    try:
        smtp = smtplib.SMTP_SSL(host, 465)
    except socket.error:
        smtp = smtplib.SMTP(host, 25)

    smtp.login(sender_email, password)  # If you need to hide the password, you can modify "password", and then package it.
    smtp.sendmail(sender_email, receiver_email, message.as_string())
    smtp.quit()
    logger.info('Send email successfully!')


if __name__ == '__main__':
    sendEmail(1)
