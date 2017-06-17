# -*- coding: utf-8 -*-
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

# Flask-Login 管理用户认证系统中的认证状态
login_manager = LoginManager()
# LoginManager 对象的 session_protection 属性可以设为 None、'basic' 或 'strong'，
# 已提供不同的安全等级防止用户会话遭篡改。设为 'strong' 时，Flask-Login 会记录客户端 IP
# 地址和浏览器的用户代理信息，如果发现异常就登出用户
login_manager.session_protection = 'strong'
# login_view 属性设置登录页面的端点
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    # 使用 Flask app.config 配置对象提供的 from_object()方法利用 config_name 从 config 字典中导入指定的配置类
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # 将蓝本注册到程序上，以使蓝本中定义的出于休眠状态的路由，成为程序的一部分
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    # 可选参数 url_prefix 为蓝本定义的所有路由都加上指定的前缀，即 /auth
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

