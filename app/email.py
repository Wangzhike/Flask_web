# -*- coding: utf-8 -*-
from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from . import mail


def send_async_email(app, msg):
    # Flask-Mail 中的 send() 函数要使用 current_app，因此要使用 with 语句激活程序上下文
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    # current_app._get_current_object() 方法得到当前应用上下文的被代理对象
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    # 指定模板时不能包含扩展名，这样才能使用两个模板分别渲染纯文本正文和富文本正文
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    # 为了避免处理发送邮件请求过程中不必要的延迟，把发送电子邮件的函数移到后台线程中
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
