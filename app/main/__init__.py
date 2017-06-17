# -*- coding: utf-8 -*-
from flask import Blueprint

# 创建用于路由程序和错误页面处理程序的main蓝本
main = Blueprint('main', __name__)

# 导入包含路由程序的 views 模块和包含错误处理程序的 errors 模块，将路由和错误处理程序与蓝本关联起来
# 同时这两个模块在该脚本的末尾导入，这是为了避免循环导入依赖，因为在 views.py 和 errors.py 中还要导入蓝本 main
from . import views, errors
