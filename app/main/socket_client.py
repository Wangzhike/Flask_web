# -*- coding: utf-8 -*-
import socket
from threading import Thread
from flask import current_app
from ..models import CalBoard, StoreBoard, ControlBoard, Task,\
                    Task_Status, User
from .. import db
from datetime import datetime
import hashlib
import os
import base64

# socket 接收数据的最大长度
SOCKET_SIZE = 1024


def parseCalBoardData(data, user_email=None):
    # len(data) != 0，表示连接主控板服务器成功，可以更新计算版数据
    if len(data) != 0:
        # 丢弃数据结尾的 '\0'
        data = data.rstrip('\0')
        idle_num, dsp_stat, fpga_extras = data.split(' ', 2)
        print('idle_num: %s' % int(idle_num))
        dsp_stat_base2 = int(dsp_stat, base=2)
        print('dsp_stat: %x' % dsp_stat_base2)
        # DSP 空闲 core 数计算
        idles = 0
        for i in range(0, 16):
            status = 0x01 - ( ((dsp_stat_base2 & (0x8000 >> i)) >> (15-i)) & 0x01 )
            print('current core status: %s' % status)
            idles += status
            print('idle core number: %s' % idles)
        # DSP 空闲 core 数检验成功
        if idles == int(idle_num):
            print('CalBoard dsp idle core numbers varification pass.')
            cal_list = []
            for i in range(0, 8):
                cal = {
                    'dsp1_status': ( ((int(dsp_stat, base=2) & (0x8000 >> i))) >> (15-i) ) & 0x01,
                    'dsp2_status': ( (int(dsp_stat, base=2) & (0x4000 >> (2*i))) >> (15-2*i) ) & 0x01,
                    'fpga_extra': int(fpga_extras.split(' ')[i])
                }
                print(cal)
                cal_list.append(cal)
            calBoards = CalBoard.query.order_by(CalBoard.name).all()
            i = 0
            for cal in cal_list:
                calBoards[i].dsp1_status = cal.get('dsp1_status')
                calBoards[i].dsp2_status = cal.get('dsp2_status')
                calBoards[i].fpga_extra = cal.get('fpga_extra')
                try:
                    db.session.add(calBoards[i])
                    db.session.commit()
                except Exception as err:
                    db.session.callback()
                    print('Update CalBoard model in socket communication occurs error: %s' % err)
                finally:
                    i = i + 1
            db.session.commit()
        else:
            print('CalBoard dsp idle core numbers varification failed!')


def parseStoreBoardData(data, user_email=None):
    # len(data) != 0，表示连接主控板服务器成功，可以更新存储版数据
    if len(data) != 0:
        # 丢弃数据结尾的 '\0'
        data = data.rstrip('\0')
        store_mem = data.split(' ', 3)
        storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
        i = 0
        for store in store_mem:
            # 利用 space 将每块存储版的数据分为
            # capacity: 总容量 used: 已用容量 两部分
            (capacity, used) = store.split('_', 1)
            storeBoards[i].capacity = int(capacity)
            storeBoards[i].used = int(used)
            storeBoards[i].left = storeBoards[i].capacity - storeBoards[i].used
            print("{'capacity: %s, 'used': %s, 'left': %s}"
                  % (storeBoards[i].capacity, storeBoards[i].used, storeBoards[i].left))
            try:
                db.session.add(storeBoards[i])
                db.session.commit()
            except Exception as err:
                db.session.callback()
                print('Update StoreBoard model in socket communication occurs error: %s' % err)
            finally:
                i = i + 1
        db.session.commit()


def parseControlBoardData(data, user_email=None):
    # len(data) != 0，表示连接主控板服务器成功，可以更新控制板数据
    if len(data) != 0:
        # 丢弃数据结尾的 '\0'
        data = data.rstrip('\0')
        cpu_user, cpu_system, cpu_idle, timestamp = data.split(' ', 3)
        # 按照时间戳升序方式将控制板数据排序，也就是说最后一位数据时间最新
        controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()
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
                i = len(controlBoards) - 1
                controlBoards[i].cpu_user_percent = float(int(cpu_user) / 10.0)
                controlBoards[i].cpu_sys_percent = float(int(cpu_system) / 10.0)
                controlBoards[i].cpu_idle_percent = float(int(cpu_idle) / 10.0)
                controlBoards[i].timestamp = datetime.strptime(timestamp, '%Y_%m_%d_%H_%M_%S')
                print("{'cpu_user': %s, 'cpu_system: %s, 'cpu_idle: %s''}" % ( float(int(cpu_user) / 10.0),
                                                                                float(int(cpu_system) / 10.0), float(int(cpu_idle) / 10.0)) )
                # 手动更新最后一位数据
                db.session.add(controlBoards[i])
            except Exception as err:
                print('Update ControlBoard Model in socket communication occurs error: %s' % err)
            finally:
                db.session.commit()
        else:
            print('ControlBoard table is empty!')


def parseDeployTaskData(data, user_email):
    # len(data) != 0，表示连接主控板服务器成功，可以更新任务池数据
    if len(data) != 0:
        # 丢弃数据结尾的 '\0'
        data = data.rstrip('\0')
        task_id, task_hwResource= data.split(' ', 1)
        # print('task_id=%s, task_hwResource=%s' % (task_id, task_hwResource))

        # 首先从 User 模型中获取当前用户
        user = User.query.filter_by(email=user_email).first()
        # 查询 Task 模型中当前用户的所有任务，按照 id 升序排序，
        # 因为 id 是递增的，所以 id 的大小代表了被插入数据库的先后顺序，
        # id 越小，越早被插入数据库
        tasks = Task.query.filter_by(user_task=user).order_by(Task.id).all()
        if tasks is not None:
            unreg_task = None
            # 从中找出第一个尚未注册的任务，即没有分配 task_id，此时 task_id 为默认值-1，
            # 此时该任务就对应 socket 通信主控板返回的数据指定的任务
            for task in tasks:
                if task.task_id == -1:
                    unreg_task = task
                    break
            if unreg_task is not None:
                # 填充返回的 task_id
                unreg_task.task_id = int(task_id)
                # 更改任务的状态为可执行
                unreg_task.task_status = Task_Status.EXECUTABLE
                # 填充返回的分配给任务的硬件资源
                unreg_task.task_hwResource = task_hwResource
                try:
                    db.session.add(unreg_task)
                    db.session.commit()
                    print("{task_id: %s, task_status: %s, task_hwResource: %s}" % (unreg_task.task_id,
                                                                                    unreg_task.task_status,
                                                                                    unreg_task.task_hwResource) )
                    print('parseDeployTaskData once success and finish!')
                except Exception as err:
                    db.session.rollback()
                    print('Update Task Model in socket communication occurs error: %s' % err)
                db.session.commit()
            else:
                print('Task model has no unregistered task belogned to user: %s' % user.username)
        else:
            print('Task model has no tasks belonged to user: %s' % user.username)


def checkFiles(data_file_name):
    # 获取数据文件的存储位置时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    fileList = os.listdir(app.config['UPLOADED_TASKDATAS_DEST'])
    # print('taskDatas directory has files: %s' % fileList)
    # print('The file: %s to be found whether other file has the same name with it.' % data_file_name)
    for file in fileList:
        # print('The searched file: %s to compared with' % file)
        if file == data_file_name:
            os.remove(os.path.join(app.config['UPLOADED_TASKDATAS_DEST'], file))
            print('Remove the file that has the same name with %s' % data_file_name)


def parseIssueTaskData(data, user_email=None):
    # 获取数据文件的存储位置时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    # len(data) != 0，表示连接主控板服务器成功，可以更新 Task 模型中正在执行任务的状态
    # 以及接收处理后的数据文件
    if len(data) != 0:
        # 丢弃数据结尾的 '\0'
        data = data.rstrip('\0')
        task_id, treated_file = data.split(' ', 1)
        # 从 Task 模型中找到由 task_id 指定的任务
        task_id = int(task_id)
        print('Received task: %s returned treated file data' % task_id)
        # 将数据文件(图片)字符串先转换为 bytes 字节流，然后利用 base64 解码为原图像对应的二进制数据
        treated_file = base64.b64decode(treated_file.encode('utf-8'))
        task = Task.query.filter_by(task_id=task_id).first()
        if task is not None:
            # 将其状态标记为执行完毕
            task.task_status = Task_Status.DONE
            # 存储处理后的数据文件
                # 为文件名追加 '_treated' 后缀
            data_file_name = task.data_file_name
            name, ext = data_file_name.rsplit('.', 1)
            name += '_treated'
            data_treated_file_name = name + '.' + ext
                # 在 Task 模型中存储处理后的文件的文件名
            task.data_treated_file_name = data_treated_file_name
                # 检查该文件是否已经存在，如果存在，则删除原来的文件
            print('Now checking the file: %s is existing or not existing...' % data_treated_file_name)
            checkFiles(data_treated_file_name)
                # 生成文件的完整存储路径
            save_path = os.path.join(app.config['UPLOADED_TASKDATAS_DEST'], data_treated_file_name)
                # 打开该路径文件写入数据
            with open(save_path, 'wb') as f:
                f.write(treated_file)
                print('Writing data to file...')
            print('Write data to file done!')
            try:
                db.session.add(task)
                db.session.commit()
            except Exception as err:
                print('modify task status by treated file occurs error: %s' % err)
                db.session.rollback()
        else:
            print('Task model has no that running task: %s' % task_id)


cmd_search = {
    parseCalBoardData: {
        'taskNum': 1,
        'taskAttr': ['t'],
        'taskCmd': 2,
        'taskSize': [],
        'taskDataPath': []
    },
    parseStoreBoardData: {
        'taskNum': 1,
        'taskAttr': ['t'],
        'taskCmd': 3,
        'taskSize': [],
        'taskDataPath': []
    },
    parseControlBoardData: {
        'taskNum': 1,
        'taskAttr': ['t'],
        'taskCmd': 1,
        'taskSize': [],
        'taskDataPath': []
    },
    parseDeployTaskData: {

    },
    parseIssueTaskData: {

    }
}


def parseTaskQueue(task_queue):
    print(task_queue)
    cmd_search[parseDeployTaskData] = {
        'taskNum': len(task_queue),
        # !!!目前还没有添加任务类型的处理!!!
        'taskType': [task['taskType'] for task in task_queue],
        'taskAttr': [(task['taskAttr'][0]) for task in task_queue],
        'taskCmd': 4,
        'taskSize': [task['taskSize'] for task in task_queue],
        'taskDataPath': []
    }
    print(cmd_search[parseDeployTaskData])


def parseIssueTaskQueue(issue_task_queue):
    print(issue_task_queue)
    cmd_search[parseIssueTaskData] = {
        'taskNum': len(issue_task_queue),
        # 这里借用 taskAttr 属性来存放 taskId
        'taskAttr': [task['taskId'] for task in issue_task_queue],
        'taskCmd': 5,
        'taskSize': [task['taskSize'] for task in issue_task_queue],
        'taskDataPath': [task['taskDataPath'] for task in issue_task_queue]
    }


def async_updateModel(app, parseDatafunc, user_email):
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
        # 发送数据
        cmd = ''
        # 构造发送数据：

            # 任务数量'
        taskNum = int(cmd_search[parseDatafunc].get('taskNum'))
        cmd += chr(taskNum) + ' '   # 利用 chr() 将数字转换为该数字对应的 ascii 码
            # 任务策略
        attrs = cmd_search[parseDatafunc].get('taskAttr')
        for attr in attrs:
            cmd += str(attr)
        cmd += ' '
            # 用户 id hashlib 映射
        # cmd += hashlib.md5('956318206@qq.com').hexdigest()[0:10] + '\n\0 '
        cmd += hashlib.md5(user_email).hexdigest()[0:10] + '\n\0 '
            # 任务号
        cmd += chr(cmd_search[parseDatafunc].get('taskCmd')) + ' '  # 利用 chr() 将数字转换为该数字对应的 ascii 码

        # 任务规模
        sizes = cmd_search[parseDatafunc].get('taskSize')
        # 任务数据文件路径
        paths = cmd_search[parseDatafunc].get('taskDataPath')
        print(sizes)
        for i in range(len(sizes)):
            cmd += '{:0>5}'.format(sizes[i])
            # 任务下发命令: 5，带有数据文件路径，如果对应的数据文件路径不为空，
            # 读取该数据文件，并附加到发送命令上
            if i < len(paths):
                # 先将数据文件内容读出
                file = ''
                with open(paths[i], 'rb') as f:
                    for data in f:
                        file += data
                # 将数据文件(图片)二进制数据先用 base64 编码为 bytes 字节流，然后通过解码为 字符串
                cmd += ' ' + base64.b64encode(file).decode('utf-8')
            if i != len(sizes) - 1:
                cmd += ' ' + chr(cmd_search[parseDatafunc].get('taskCmd')) + ' '
        # if len(sizes) != 0:
        #     for size in sizes[:-1]:
        #         cmd += '{:0>5}'.format(size) + ' ' + chr(cmd_search[parseDatafunc].get('taskCmd')) + ' '
        #     cmd += '{:0>5}'.format(sizes[-1])
            # 结束标志 '\0'
        cmd += '\0'

        # print('Cmd: %r' % cmd)

        try:
            s.connect((server_ip, server_port))
            # 接收欢迎信息
            recv = s.recv(SOCKET_SIZE).decode('utf-8')
            # print(recv)

            # 发送查询计算板数据命令
            s.send(cmd.encode('utf-8'))
            for i in range(taskNum):
                data = ''
                # 读取返回的计算板数据
                while True:
                    recv = s.recv(SOCKET_SIZE).decode('utf-8')
                    data += recv
                    # 接收完毕时 recv 的长度小于 SOCKET_SIZE
                    if len(recv) < SOCKET_SIZE:
                        print('Socket Receive file: Reach the end of file.')
                        break
                # len(data) != 0，表示连接主控板服务器成功，可以更新查询的数据
                if len(data) != 0:
                    # print('%r' % data)
                    parseDatafunc(data, user_email=user_email)
                else:
                    print('Socket recevie data is None.')

        except Exception as err:
            print('Socket communication occurs error in %s: %s' % (parseDatafunc, err))
        finally:
            # 关闭连接
            s.close()


def updateModel(parseDatafunc, user_email):
    # async_updateCalBoardModel 函数中，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    thr = Thread(target=async_updateModel, args=[app, parseDatafunc, user_email])
    thr.start()
    # thr.join()
    return thr