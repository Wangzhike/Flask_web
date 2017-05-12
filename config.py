# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # 为实现跨站请求伪造 CSRF 保护，Flask-WTF需要程序设置一个秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'qiuyu, 19940109'
    # 每次请求结束后自动提交数据库中的变动
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 连接到外部的qq邮箱服务器
    MAIL_SERVER = 'smtp.163.com'
    # SSL协议端口号
    MAIL_PORT = 994
    # 启用传输层安全协议
    # MAIL_USE_TLS = True
    # 启用安全套接层协议
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # 邮件主题的前缀
    FLASKY_MAIL_SUBJECT_PREFIX = '[FLASKY]'
    # 发件人的地址
    FLASKY_MAIL_SENDER = 'FLASKY Admin <m15090870975@163.com>'
    # 系统管理员
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    # 主控板 IP 地址
    MAINBOARD_IP = '127.0.0.1'  # '10.170.42.243'
    # 主控板 端口
    MAINBOARD_PORT = 9999  # 3333

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URI') or
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite'))


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('TEST_DATABASE_URI') or
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URI') or
        'sqlite:///' + os.path.join(basedir, 'data.sqlite'))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}