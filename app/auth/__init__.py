# -*- coding: utf-8 -*-
from flask import Blueprint

# 创建用于用户认证系统相关路由的auth蓝本
auth = Blueprint('auth', __name__)

# 导入包含用户认证系统路由程序的 views 模块，把路由和蓝本相关联
from . import views