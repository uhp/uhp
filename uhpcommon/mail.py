#!/usr/bin/env python 
# -*- coding: UTF-8 -*- 

import smtplib
import config
from email.mime.text import MIMEText

def send_mail(to_list, sub, content,type = 'plain'):
    '''
    使用config中配置的邮箱用户发送邮件
    type 可以为plain或者html
    '''
    if config.mail_host == None or config.mail_user == None or config.mail_passwd == None or config.mail_from == None:
        return False
    msg = MIMEText(content,_subtype=type,_charset='gb2312')
    msg['Subject'] = sub
    msg['From'] = config.mail_from
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP() 
        server.connect(config.mail_host)
        server.login(config.mail_user, config.mail_passwd)
        server.sendmail(config.mail_from, to_list, msg.as_string())
        server.close()
        return True
    except:
        return False

def send_ssl_mail(to_list, sub, content,type = 'plain'):
    '''
    使用config中配置的邮箱用户发送ssl邮件
    '''
    if config.mail_host == None or config.mail_user == None or config.mail_passwd == None or config.mail_from == None:
        return False
    msg = MIMEText(content,_subtype=type,_charset='gb2312')
    msg['Subject'] = sub
    msg['From'] = config.mail_from
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP_SSL() 
        server.connect(config.mail_host)
        server.login(config.mail_user, config.mail_passwd)
        server.sendmail(config.mail_from, to_list, msg.as_string())
        server.close()
        return True
    except:
        return False
 
if __name__ == '__main__': 
    if send_ssl_mail(['qiujw@ucweb.com'],'hello','<h1>haha</h1>','html'):
        print "ok"
    else:
        print "error"
