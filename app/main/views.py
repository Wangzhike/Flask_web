# -*- coding: utf-8 -*-
from flask import request, render_template, redirect,\
                url_for, abort, flash, jsonify, current_app,\
                send_from_directory
from flask_login import current_user
from . import main
from .. import db
from ..models import CalBoard, StoreBoard, ControlBoard, Task, TaskTemp
from socket_client import updateModel
from socket_client import parseCalBoardData, parseStoreBoardData,\
                        parseControlBoardData
from forms import AddtaskForm, SubmitTaskForm
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import json
from collections import OrderedDict


def parseControlBoards(controlBoards):
    controlBoardsSplit = []
    ctrlbDatas = {
        'cpu_user': [],
        'cpu_system': [],
        'cpu_idle': []
    }
    categories = []
    for ctrlb in controlBoards:
        ctrlbDatas['cpu_user'].append(ctrlb.cpu_user_percent)
        ctrlbDatas['cpu_system'].append(ctrlb.cpu_sys_percent)
        ctrlbDatas['cpu_idle'].append(ctrlb.cpu_idle_percent)
        # categories.append(ctrlb.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        categories.append(ctrlb.timestamp.strftime('%H:%M:%S'))
    controlBoardsSplit.append(ctrlbDatas)
    controlBoardsSplit.append(categories)
    print(categories)
    return controlBoardsSplit


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/controlBoard_deal_2', methods=['GET'])
def controlBoard_deal_2():
    # 首先与主控板通信更新 ControlBoard 模型中数据
    updateModel(parseControlBoardData)
    # 查询数据库获取当前的主控板数据
    controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()
    # 解析主控板数据并生成对应的 json 格式
    ctrlbDatas = {
        'datas': [
            {
                'name': 'cpu_user',
                'data': []
            },
            {
                'name': 'cpu_system',
                'data': []
            },
            {
                'name': 'cpu_idle',
                'data': []
            }
        ],
        'categories': []
    }
    for ctrlb in controlBoards:
        ctrlbDatas['datas'][0]['data'].append(ctrlb.cpu_user_percent)
        ctrlbDatas['datas'][1]['data'].append(ctrlb.cpu_sys_percent)
        ctrlbDatas['datas'][2]['data'].append(ctrlb.cpu_idle_percent)
        # 按 '09:32:35' 格式格式化时间戳
        ctrlbDatas['categories'].append(ctrlb.timestamp.strftime('%H:%M:%S'))
    return jsonify(ctrlbDatas)


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/storeBoard_deal', methods=['GET'])
def storeBoard_deal():
    # 首先与主控板通信更新 StoreBoard 模型中的数据
    updateModel(parseStoreBoardData)
    # 查询数据库获取当前的存储版数据
    storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
    # 解析存储版数据并生成对应的 json 格式
    strbDatas = []
    center_X = 14
    for strb in storeBoards:
        strbData = {
            'name': '',
            'type': 'pie',
            'radius': '24%',
            'center': [str(center_X) + '%', '57%'],
            'data': [
                {'value': round(strb.used / 1024.0, 1), 'name': '已用'},
                {'value': round(strb.left / 1024.0, 1), 'name': '未用'},
            ],
            'label': {
                'normal': {
                    'position': 'inner',
                    'formatter': '{c}T',
                    'textStyle': {
                        'color': '#ffffff',
                        'fontSize': 14
                    }
                }
            },
            'itemStyle': {
                'emphasis': {
                    'shadowBlur': 10,
                    'shadowOffsetX': 0,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            },
        }
        strbDatas.append(strbData)
        center_X += 24
    return jsonify(strbDatas)


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/controlBoard_deal_1', methods=['GET'])
def controlBoard_deal_1():
    # 首先与主控板通信更新 ControlBoard 模型中数据
    updateModel(parseControlBoardData)
    # 查询数据库获取当前的主控板数据
    controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()
    # 解析主控板数据并生成对应的 json 格式
    ctrlbDatas = {
        'series': [
            {
                'name': 'cpu_user',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            },
            {
                'name': 'cpu_system',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            },
            {
                'name': 'cpu_idle',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            }
        ],
        'categories': []
    }
    for ctrlb in controlBoards:
        ctrlbDatas['series'][0]['data'].append(ctrlb.cpu_user_percent)
        ctrlbDatas['series'][1]['data'].append(ctrlb.cpu_sys_percent)
        ctrlbDatas['series'][2]['data'].append(ctrlb.cpu_idle_percent)
        # 按 '09:32:35' 格式格式化时间戳
        ctrlbDatas['categories'].append(ctrlb.timestamp.strftime('%H:%M:%S'))
    return jsonify(ctrlbDatas)


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/controlBoard_deal_1_1', methods=['GET'])
def controlBoard_deal_1_1():
    # 首先与主控板通信更新 ControlBoard 模型中数据
    updateModel(parseControlBoardData)
    # 查询数据库获取当前的主控板数据
    # 按照时间戳升序方式将控制板数据排序，也就是说最后一位数据时间最新
    controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp)[-1]
    # 解析主控板数据并生成对应的 json 格式
    ctrlbDatas = {
        'series': [
            {
                'name': 'cpu_user',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            },
            {
                'name': 'cpu_system',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            },
            {
                'name': 'cpu_idle',
                'type': 'line',
                'stack': '总量',
                'areaStyle': '{normal: {}}',
                'data': []
            }
        ],
        'categories': []
    }
    # 这里就只有一个数据了
    # for ctrlb in controlBoards:
    #     ctrlbDatas['series'][0]['data'].append(ctrlb.cpu_user_percent)
    #     ctrlbDatas['series'][1]['data'].append(ctrlb.cpu_sys_percent)
    #     ctrlbDatas['series'][2]['data'].append(ctrlb.cpu_idle_percent)
    #     # 按 '09:32:35' 格式格式化时间戳
    #     ctrlbDatas['categories'].append(ctrlb.timestamp.strftime('%H:%M:%S'))
    ctrlbDatas['series'][0]['data'].append(controlBoards.cpu_user_percent)
    ctrlbDatas['series'][1]['data'].append(controlBoards.cpu_sys_percent)
    ctrlbDatas['series'][2]['data'].append(controlBoards.cpu_idle_percent)
    # 按 '09:32:35' 格式格式化时间戳
    ctrlbDatas['categories'].append(controlBoards.timestamp.strftime('%H:%M:%S'))
    return jsonify(ctrlbDatas)


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        flash(u'欢迎使用！')
        updateModel(parseCalBoardData)
        updateModel(parseStoreBoardData)
        updateModel(parseControlBoardData)
        # updateCalBoardModel()
        # updateStoreBoardModel()
        calBoards = CalBoard.query.order_by(CalBoard.name).all()
        storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
        controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()
        return render_template('index.html',
                               calBoards=calBoards,
                               storeBoards=storeBoards,
                               controlBoardsSplit=parseControlBoards(controlBoards))


@main.route('/deploy-task', methods=['GET', 'POST'])
def deploy_task():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        # flash(u'欢迎！')
        addTaskForm = AddtaskForm()
        submitTaskForm = SubmitTaskForm()
        if submitTaskForm.validate_on_submit():
            print(u'收到了提交的任务表单!')
            # print(submitTaskForm.flag.render_kw.get('value'))
            # print(request.form)
            if request.form.get('flag') == '1':
                print(u'表单验证通过!')
                # 用户点击任务提交按钮后，需要将 TaskTemp 模型中的数据转移到 Task 模型中，
                # 删除 TaskTemp 中的数据
                # 从 TaskTemp 模型取出该用户的所有任务数据
                taskTemps = TaskTemp.query.filter_by(user_taskTemp=current_user).all()
                for ttmp in taskTemps:
                    task = Task(type=ttmp.type,
                                attr=ttmp.attr,
                                data_file_name=ttmp.data_file_name,
                                user_task=ttmp.user_taskTemp,
                                timestamp=ttmp.timestamp)
                    try:
                        db.session.add(task)
                        db.session.delete(ttmp)
                        db.session.commit()
                    except Exception as err:
                        print('move TaskTemp datas to Task occurs error: %s' % err)
                        db.session.rollback()
                        flash(u'任务提交失败!')
                flash(u'任务提交成功!')
                return redirect(url_for('main.deploy_task'))
        return render_template('deploy_task.html',
                               addTaskForm=addTaskForm,
                               submitTaskForm=submitTaskForm)


# 生成上传的数据文件的 url
@main.route('/uploads_taskdatas/<filename>')
def uploads_taskdatas(filename):
    # 获取用于保存数据文件的目录时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    return send_from_directory(app.config['UPLOADED_TASKDATAS_DEST'], filename)


# 检查文件扩展名
def allowed_file(filename):
    # 获取指定的数据文件的扩展名时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_TASKDATAS_EXTENSIONS']


# 文件名处理
def deal_filename(filename):
    (name, ext) = filename.rsplit('.', 1)
    # 给文件名加上当前用户名
    name = current_user.username + '_' + name
    # 给文件名加上 datetime 时间戳，比如: 2017_06_03_10_19_32
    name += '_' + datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S')
    # 最后使用 secure_filename 方法去掉文件名中非 ASCII 字符(比如中文)
    name = secure_filename(name)
    filename = name + '.' + ext
    return filename


@main.route('/addTask_deal', methods=['POST'])
def addTask_deal():
    # 保存由 bootstrap fileinput 插件上传的文件时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()
    taskData_file_url = ''
    taskPools = []
    fileinput_response = {}
    try:
        print('Now we are in addTask_deal!')

        # dict 字典的 get 方法如果键值不存在，默认返回 None
        taskType = request.form.get('taskType')
        taskAttr = request.form.get('taskAttr')
        taskData = request.files.get('taskData')
        # 往数据库添加本次任务的数据
        if taskType and taskAttr:
            if taskData is None:
                taskData_file_url = ''
            taskTemp = TaskTemp(type=taskType,
                        attr=taskAttr,
                        data_file_name=taskData_file_url,
                        user_taskTemp=current_user)
            # 如果数据文件非空而且文件扩展名合法
            if taskData and allowed_file(taskData.filename):
                taskData_file_name = deal_filename(taskData.filename)
                # 此时修改 task 的 data_file_name 属性，使其是修改后的文件名
                taskTemp.data_file_name = taskData_file_name
                taskData.save(os.path.join(app.config['UPLOADED_TASKDATAS_DEST'],
                                           taskData_file_name))
                print(taskData_file_name)
                # 为文件生成 url 地址
                taskData_file_url = url_for('main.uploads_taskdatas', filename=taskData_file_name)
            db.session.add(taskTemp)
            db.session.commit()
        # 从数据库取出该用户所有任务数据
        tasks = TaskTemp.query.filter_by(user_taskTemp=current_user).all()
        for t in tasks:
            task_dict = {}
            # 任务名称
            taskName = t.user_taskTemp.username + '_' + t.type + '_' + \
                       t.timestamp.strftime('%Y_%m_%d_%H_%M_%S')
            task_dict['taskName'] = taskName
            task_dict['taskAttr'] = t.attr
            if len(t.data_file_name) != 0:
                task_dict['taskDataURL'] = url_for('main.uploads_taskdatas', filename=t.data_file_name)
            else:
                task_dict['taskDataURL'] = ''
            taskPools.append(task_dict)
        fileinput_response['status'] = 0
        fileinput_response['tasks'] = taskPools
        return jsonify(fileinput_response)
    except KeyError as keyerr:
        print('KeyError: %s' % keyerr)
        fileinput_response['status'] = -1
        return jsonify(fileinput_response)


@main.route('/submitTask_deal', methods=['POST'])
def submitTask_deal():
    # 用户点击任务注册按钮后，需要将 TaskTemp 模型中的数据转移到 Task 模型中，
    # 删除 TaskTemp 中的数据
        # 从 TaskTemp 模型取出该用户的所有任务数据
    taskTemps = TaskTemp.query.filter_by(user_taskTemp=current_user).all()
    for ttmp in taskTemps:
        task = Task(type=ttmp.type,
                    attr=ttmp.attr,
                    data_file_name=ttmp.data_file_name,
                    user_task=ttmp.user_taskTemp,
                    timestamp=ttmp.timestamp)
        try:
            db.session.add(task)
            db.session.delete(ttmp)
            db.session.commit()
        except Exception as err:
            print('move TaskTemp datas to Task occurs error: %s' % err)
            db.session.rollback()
            return jsonify({'status': -1})
    return jsonify({'status': 0})


@main.route('/issue-task')
def issue_task():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        return render_template('issue_task.html')


@main.route('/view-results')
def view_results():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        return render_template('view_results.html')


@main.route('/system-log')
def syslog():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        return render_template('syslog.html')