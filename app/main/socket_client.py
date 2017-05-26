# -*- coding: utf-8 -*-
import socket
from threading import Thread
from flask import current_app
from ..models import CalBoard, StoreBoard, ControlBoard
from .. import db
from datetime import datetime


def parseCalBoardData(data):
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


def parseStoreBoardData(data):
    # data != None，表示连接主控板服务器成功，可以更新存储版数据
    if data is not None:
        # 根据 \n 符号分解存储版数据
        dataList = data.split('\n', 4)
        storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
        i = 0
        for d in dataList:
            try:
                # 利用 space 将每块存储版的数据分为
                # capacity: 总容量 used: 已用容量 两部分
                (capacity, used) = d.split(' ')
                storeBoards[i].capacity = int(capacity)
                storeBoards[i].used = int(used)
                storeBoards[i].left = storeBoards[i].capacity - storeBoards[i].used
                db.session.add(storeBoards[i])
            except:
                pass
            i = i + 1
        db.session.commit()


def parseControlBoardData(data):
    # data != None，表示连接主控板服务器成功，可以更新控制板数据
    if data is not None:
        # 根据 \n 符号分解存储版数据
        dataList = data.split('\n', 4)
        # 按照时间戳升序方式将控制板数据排序，也就是说最后一位数据时间最新
        controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()

        for i in range(0, len(controlBoards)):
            # 用后面一位较新的数据覆盖前面那个较老的数据，最后一位数据需要在接下来手动更新
            print('id: %s user: %s sys: %s idle: %s timestamp: %s' %(
                controlBoards[i].id,
                controlBoards[i].cpu_user_percent,
                controlBoards[i].cpu_sys_percent,
                controlBoards[i].cpu_idle_percent,
                controlBoards[i].timestamp))

        if len(controlBoards) != 0:
            for i in range(0, len(controlBoards)-1):
                try:
                    # 用后面一位较新的数据覆盖前面那个较老的数据，最后一位数据需要在接下来手动更新
                    controlBoards[i].cpu_user_percent = controlBoards[i+1].cpu_user_percent
                    controlBoards[i].cpu_sys_percent = controlBoards[i + 1].cpu_sys_percent
                    controlBoards[i].cpu_idle_percent = controlBoards[i + 1].cpu_idle_percent
                    controlBoards[i].timestamp = controlBoards[i + 1].timestamp
                    db.session.add(controlBoards[i])
                    db.session.commit()
                except Exception as err:
                    print('Modify data to ControlBoard model occurs error: %s' % err)
                    db.session.rollback()
            try:
                # 手动更新最后一位数据
                cpu_user_percent = dataList[0].split(':', 2)[-1]
                cpu_sys_percent = dataList[1].split(':', 2)[-1]
                cpu_idle_percent = dataList[2].split(':', 2)[-1]
                # 此处得到的是以小数表示的时间戳，但数据库只接受 Datetime 格式的时间戳，
                # 需要进行转换
                time = dataList[3].split(':', 2)[-1]
                i = len(controlBoards) - 1
                controlBoards[i].cpu_user_percent = float(cpu_user_percent)
                controlBoards[i].cpu_sys_percent = float(cpu_sys_percent)
                controlBoards[i].cpu_idle_percent = float(cpu_idle_percent)
                controlBoards[i].timestamp = datetime.fromtimestamp(float(time))
                db.session.add(controlBoards[i])
            except Exception as err:
                print('parseControlBoardData occurs error: %s', err)
            finally:
                db.session.commit()
        else:
            print('ControlBoard table is empty!')


cmd_search = {
    parseCalBoardData: 11,
    parseStoreBoardData: 12,
    parseControlBoardData: 13
}


def async_updateModel(app, parseDatafunc):
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
            cmd = cmd_search[parseDatafunc]
            s.send(chr(cmd).encode('utf-8'))
            # 读取返回的计算板数据
            data = s.recv(1024).decode('utf-8')
        except:
            pass
        finally:
            # 关闭连接
            s.close()
        # data != None，表示连接主控板服务器成功，可以更新查询的数据
        parseDatafunc(data)


def updateModel(parseDatafunc):
    # async_updateCalBoardModel 函数中，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    thr = Thread(target=async_updateModel, args=[app, parseDatafunc])
    thr.start()
    return thr

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


def async_updateStoreBoardModel(app):
    # 由于 server_ip, server_port 参数需要从当前应用的 config 字典中读取，
    # 而在不同线程中使用当前应用的代理对象 current_app，程序上下文要显示使用
    # app_context() 人工创建。从而该函数需要传入 current_app 代理对象背后
    # 潜在的被代理的对象。
    with app.app_context():
        # 创建一个 socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接到指定的服务器: IP + 端口号 指定
        server_ip = current_app.config['MAINBOARD_IP']
        server_port = current_app.config['MAINBOARD_PORT']
        data = None
        try:
            s.connect((server_ip, server_port))
            data = s.recv(1024).decode('utf-8')
            # 发送查询存储版资源命令
            cmd = 12
            s.send(chr(cmd).encode('utf-8'))
            # 读取返回的存储版数据
            data = s.recv(1024).decode('utf-8')
        except:
            pass
        finally:
            # 关闭连接
            s.close()
        # data != None，表示连接主控板服务器成功，可以更新存储版数据
        if data is not None:
            # 根据 \n 符号分解存储版数据
            dataList = data.split('\n', 4)
            storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
            i = 0
            for d in dataList:
                try:
                    # 利用 space 将每块存储版的数据分为
                    # capacity: 总容量 used: 已用容量 两部分
                    (capacity, used) = d.split(' ')
                    storeBoards[i].capacity = int(capacity)
                    storeBoards[i].used = int(used)
                    storeBoards[i].left = storeBoards[i].capacity - storeBoards[i].used
                    db.session.add(storeBoards[i])
                except:
                    pass
                i = i + 1
            db.session.commit()


def updateStoreBoardModel():
    # async_updateCalBoardModel 函数中，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    thr = Thread(target=async_updateStoreBoardModel, args=[app])
    thr.start()
    return thr