# -*- coding: utf-8 -*-
import socket
from threading import Thread
from flask import current_app
from ..models import CalBoard
from .. import db


def async_updateCalBoardModle(app):
    # 由于 server_ip, server_port 参数需要从当前应用的 config 字典中读取，
    # 而在不同线程中使用当前应用的代理对象 current_app，程序上下文要显示使用
    # app_context() 人工创建。从而该函数需要传入 current_app 代理对象背后
    # 潜在的被代理的对象。
    with app.app_context():
        # 创建一个socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接到指定的服务器：IP + 端口号 指定
        server_ip = current_app.config['MAINBOARD_IP']
        server_port = current_app.config['MAINBOARD_PORT']
        data = None
        try:
            s.connect((server_ip, server_port))
            data = s.recv(1024).decode('utf-8')
            # 发送查询计算板数据命令
            cmd = 11
            s.send(chr(cmd).encode('utf-8'))
            # 读取返回的计算板数据
            data = s.recv(1024).decode('utf-8')
        except:
            pass
        finally:
            # 关闭连接
            s.close()
        # data != None，表示连接主控板服务器成功，可以更新计算板数据
        if data is not None:
            dataList = data.split('\n')
            calBoards = CalBoard.query.order_by(CalBoard.name).all()
            i = 0
            for d in dataList:
                try:
                    (dsp1_status, dsp2_status, fpga_extra) = d.split(' ', 3)
                    calBoards[i].dsp1_status = dsp1_status
                    calBoards[i].dsp2_status = dsp2_status
                    calBoards[i].fpga_extra = fpga_extra
                    db.session.add(calBoards[i])
                except:
                    pass
                i = i + 1
            db.session.commit()


def updateCalBoardModel():
    # async_updateCalBoardModel 函数中，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    thr = Thread(target=async_updateCalBoardModle, args=[app])
    thr.start()
    return thr