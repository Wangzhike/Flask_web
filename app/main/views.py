# -*- coding: utf-8 -*-
from flask import request, render_template, redirect,\
                url_for, abort, flash, jsonify, current_app,\
                send_from_directory
from flask_login import current_user
from . import main
from .. import db
from ..models import CalBoard, StoreBoard, ControlBoard, User,\
                    Task, TaskTemp, Task_Status
from socket_client import updateModel, parseTaskQueue
from socket_client import parseCalBoardData, parseStoreBoardData,\
                        parseControlBoardData, parseDeployTaskData,\
                        parseIssueTaskData, parseIssueTaskQueue
from forms import AddtaskForm, SubmitTaskForm, ViewResultsForm
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
    return controlBoardsSplit


@main.route('/calBoard_deal', methods=['GET'])
def calBoard_deal():
    updateModel(parseCalBoardData, user_email=current_user.email)
    calBoards = CalBoard.query.order_by(CalBoard.name).all()
    calbDatas = []
    for calb in calBoards:
        calbData = {
            'name': calb.name,
            'dsp1_idle': calb.dsp1_isIdle(),
            'dsp2_idle': calb.dsp2_isIdle(),
            'fpga_extra': calb.fpga_extra
        }
        calbDatas.append(calbData)
    # return jsonify(calbDatas)
    return calbDatas


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/storeBoard_deal', methods=['GET'])
def storeBoard_deal():
    # 首先与主控板通信更新 StoreBoard 模型中的数据
    updateModel(parseStoreBoardData, user_email=current_user.email)
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
    # return jsonify(strbDatas)
    return strbDatas


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/controlBoard_deal_1', methods=['GET'])
def controlBoard_deal_1():
    # 首先与主控板通信更新 ControlBoard 模型中数据
    updateModel(parseControlBoardData, user_email=current_user.email)
    # 查询数据库获取当前的主控板数据
    # 按照时间戳降序方式将控制板数据排序，也就是说第一位数据时间最新
    controlBoard = ControlBoard.query.order_by(ControlBoard.timestamp.desc()).first()
    # 解析主控板数据并生成对应的 json 格式
    ctrlbDatas = {
        'cpu_user': controlBoard.cpu_user_percent,
        'cpu_system': controlBoard.cpu_sys_percent,
        'cpu_idle': controlBoard.cpu_idle_percent,
        # 按 '09:32:35' 格式格式化时间戳
        'category': controlBoard.timestamp.strftime('%H:%M:%S')
    }
    # return jsonify(ctrlbDatas)
    return ctrlbDatas


# 执行对于主控板数据刷新的 Ajax 请求
@main.route('/controlBoard_deal_2', methods=['GET'])
def controlBoard_deal_2():
    # 首先与主控板通信更新 ControlBoard 模型中数据
    updateModel(parseControlBoardData, user_email=current_user.email)
    # 查询数据库获取当前的主控板数据
    # 按照时间戳降序方式将控制板数据排序，也就是说第一位数据时间最新
    controlBoard = ControlBoard.query.order_by(ControlBoard.timestamp.desc()).first()
    # 解析主控板数据并生成对应的 json 格式
    ctrlbDatas = {
        'cpu_user': controlBoard.cpu_user_percent,
        'cpu_system': controlBoard.cpu_sys_percent,
        'cpu_idle': controlBoard.cpu_idle_percent,
        # 按 '09:32:35' 格式格式化时间戳
        'category': controlBoard.timestamp.strftime('%H:%M:%S')
    }
    # return jsonify(ctrlbDatas)
    return ctrlbDatas


@main.route('/index_deal', methods=['GET'])
def index_deal():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        index_data = {
            'calbDatas': calBoard_deal(),
            'strbDatas': storeBoard_deal(),
            'ctrlbDatas_1': controlBoard_deal_1(),
            'ctrlbDatas_2': controlBoard_deal_2()
        }
        # print(index_data['strbDatas'])
        # print(index_data['ctrlbDatas_1'])
        # print(index_data['ctrlbDatas_2'])
        return jsonify(index_data)


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        flash(u'欢迎使用！')
        updateModel(parseCalBoardData, user_email=current_user.email)
        updateModel(parseStoreBoardData, user_email=current_user.email)
        updateModel(parseControlBoardData, user_email=current_user.email)
        calBoards = CalBoard.query.order_by(CalBoard.name).all()
        storeBoards = StoreBoard.query.order_by(StoreBoard.name).all()
        controlBoards = ControlBoard.query.order_by(ControlBoard.timestamp).all()
        return render_template('index.html',
                               calBoards=calBoards,
                               storeBoards=storeBoards,
                               controlBoardsSplit=parseControlBoards(controlBoards))


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
        print('taskType: %s, taskAttr: %s, taskData: %s' % (taskType, taskAttr, taskData))
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
                print('Deal with and save uploaded file!')
                taskData_file_name = deal_filename(taskData.filename)
                # 此时修改 task 的 data_file_name 属性，使其是修改后的文件名
                    # 修改后的文件名: 用户名 + '_' + 去掉非 ASCII 字符(如中文)的文件名 + '_' + 时间戳
                taskTemp.data_file_name = taskData_file_name
                taskData.save(os.path.join(app.config['UPLOADED_TASKDATAS_DEST'],
                                           taskData_file_name))
                print(taskData_file_name)
                # 为文件生成 url 地址
                taskData_file_url = url_for('main.uploads_taskdatas', filename=taskData_file_name)
            db.session.add(taskTemp)
            db.session.commit()

        add_task_to_taskPool, add_task_to_Task = query_construct_taskTemp()
        fileinput_response['status'] = 0
        fileinput_response['tasks'] = add_task_to_taskPool
        return jsonify(fileinput_response)
    except KeyError as keyerr:
        print('KeyError: %s' % keyerr)
        fileinput_response['status'] = -1
        return jsonify(fileinput_response)


def query_construct_taskTemp():
    # 获取数据文件的存储位置时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()

    add_task_to_Task = []   # 用于提交到 task 模型
    add_task_to_taskPool = []   # 用于显示到任务池
    # 从 TaskTemp 模型取出该用户的所有任务数据
    taskTemps = TaskTemp.query.filter_by(user_taskTemp=current_user).all()
    print('Query TaskTemp get %d tasks' % len(taskTemps))
    for ttmp in taskTemps:
        task_elem = {
            'id': ttmp.id,
            'type': ttmp.type,
            'attr': ttmp.attr,
            'data_file_name': ttmp.data_file_name,
            'user_task': ttmp.user_taskTemp,
            'timestamp': ttmp.timestamp
        }
        add_task_to_Task.append(task_elem)
        # 将 TaskTemp 模型中的任务添加到任务队列，并通过 socket_client 处理发送给主控板
        # 任务名称
        # 格式： 任务类型 + '_' +  任务属性 + '_' + 任务数据文件名
        # 而任务数据文件名: 用户名 + '_' + 去掉非 ASCII 字符(如中文)的文件名 + '_' + 时间戳
        taskName = ttmp.type + '_' + ttmp.attr + ' ' + \
                   ttmp.data_file_name
        # 获取任务数据文件的存储位置
        if ttmp.data_file_name != '':
            taskDataFilePath = os.path.join(app.config['UPLOADED_TASKDATAS_DEST'], ttmp.data_file_name)
            taskSize = os.path.getsize(taskDataFilePath) >> 10  # 大小以 kb 为单位
        else:
            taskSize = 0
        taskData_file_url = ''
        if ttmp.data_file_name != '':
            # 为文件生成 url 地址
            taskData_file_url = url_for('main.uploads_taskdatas', filename=ttmp.data_file_name)
        task_pool_elem = {
            'taskName': taskName,
            'taskType': ttmp.type,
            'taskAttr': ttmp.attr,
            'taskSize': taskSize,
            'taskDataURL': taskData_file_url
        }
        add_task_to_taskPool.append(task_pool_elem)
    return add_task_to_taskPool, add_task_to_Task


@main.route('/deploy-task', methods=['GET', 'POST'])
def deploy_task():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        # 获取数据文件的存储位置时，需要使用当前应用实例 app 来创建
        # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
        # 可以用 _get_current_object() 方法获取 app。
        app = current_app._get_current_object()

        # flash(u'欢迎！')
        addTaskForm = AddtaskForm()
        submitTaskForm = SubmitTaskForm()
        add_task_to_taskPool, add_task_to_Task = query_construct_taskTemp()
        if submitTaskForm.validate_on_submit():
            print(u'收到了提交的任务表单!')
            # print(submitTaskForm.flag.render_kw.get('value'))
            # print(request.form)
            if request.form.get('flag') == '1':
                print(u'表单验证通过!')

                for add_task in add_task_to_Task:
                    # 任务的执行状态默认为等待
                    task = Task(type=add_task.get('type'),
                                attr=add_task.get('attr'),
                                data_file_name=add_task.get('data_file_name'),
                                user_task=add_task.get('user_task'),
                                timestamp=add_task.get('timestamp'))
                    # 查询 TaskTemp 中对应的任务
                    ttmp = TaskTemp.query.filter_by(id=add_task.get('id')).first()
                    try:
                        db.session.add(task)
                        if ttmp is not None:
                            db.session.delete(ttmp)
                        db.session.commit()
                    except Exception as err:
                        print('move TaskTemp datas to Task occurs error: %s' % err)
                        db.session.rollback()
                        flash(u'任务提交失败!')

                # 调用处理函数改变 socket_client 中 cmd_search 中的 parseDeployTaskData 对应的数据
                parseTaskQueue(add_task_to_taskPool)
                # 通过 socket 与主控板通信，进行任务注册及注册状态处理
                updateModel(parseDeployTaskData, user_email=current_user.email)

                flash(u'任务提交成功!')
                # return redirect(url_for('main.deploy_task'))
                return redirect(url_for('main.issue_task'))
        return render_template('deploy_task.html',
                               addTaskForm=addTaskForm,
                               submitTaskForm=submitTaskForm,
                               add_task_to_taskPool=add_task_to_taskPool)


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


def query_construct_aliveTasks(user):
    tasks = Task.query.filter_by(user_task=user).order_by(Task.id.desc()).all()
    # 从中找出所有执行状态为等待和可执行的任务
    alive_tasks = []
    for task in tasks:
        if task.task_status == Task_Status.WAITING or \
                        task.task_status == Task_Status.EXECUTABLE or \
                        task.task_status == Task_Status.RUNNING:
            alive_tasks.append(task)
    alive_tasks_queue = []
    executable_len = 0
    running_len = 0
    for alive_task in alive_tasks:
        # 任务名称
        # 格式： 任务类型 + '_' +  任务属性 + '_' + 任务数据文件名
        # 而任务数据文件名: 用户名 + '_' + 去掉非 ASCII 字符(如中文)的文件名 + '_' + 时间戳
        taskName = alive_task.type + '_' + alive_task.attr + ' ' + \
                   alive_task.data_file_name
        task_elem = {
            'taskName': taskName,
            'taskId': alive_task.task_id,
            'taskAttr': alive_task.attr,
            'taskURL': url_for('main.uploads_taskdatas', filename=alive_task.data_file_name),
            'taskStatus': alive_task.task_status,
            'taskHWResource': []
        }
        if alive_task.task_status == Task_Status.EXECUTABLE:
            executable_len += 1
            task_hwResource = alive_task.task_hwResource.split(' ')
            task_elem['taskHWResource'] = [int(hwResource) for hwResource in task_hwResource]
        if alive_task.task_status == Task_Status.RUNNING:
            running_len += 1
        alive_tasks_queue.append(task_elem)
    # print(alive_tasks_queue)
    print('executable_len: %s' % executable_len)
    print('running_len: %s' % running_len)
    return (alive_tasks_queue, executable_len, running_len)


@main.route('/issue-task')
def issue_task():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        alive_tasks_queue, executable_len, running_len = query_construct_aliveTasks(current_user)

        # 从 CalBoard 模型中取出 dsp 的状态
        calBoards = CalBoard.query.order_by(CalBoard.name).all()
        core_status = []
        for calb in calBoards:
            core_status.append(calb.dsp1_isIdle())
            core_status.append(calb.dsp2_isIdle())

        return render_template('issue_task.html', alive_tasks_queue=alive_tasks_queue,
                               Task_Status=Task_Status, executable_len=executable_len, running_len=running_len,
                               core_status=core_status)


@main.route('/issueTask_deal', methods=['POST'])
def issueTask_deal():
    # 获取数据文件的存储位置时，需要使用当前应用实例 app 来创建
    # 应用上下文，所以需要获取 current_app 代理对象背后潜在的被代理的当前应用实例 app，
    # 可以用 _get_current_object() 方法获取 app。
    app = current_app._get_current_object()

    taskIds = request.values.get('taskIds')
    taskIds = taskIds.strip('[]')
    taskIds = taskIds.split(',')
    print(taskIds)
    issue_task_queue = []
    for taskId in taskIds:
        taskId = int(taskId)
        # 从 Task 模型中找到由 taskId 指定的任务
        task = Task.query.filter_by(task_id=taskId).first()
        if task is not None:
            # 如果当前任务的状态是可以执行 EXECUTABLE，表示确实需要执行，
            # 这里加上这个判断是由于先按下单个执行按钮再按下全部执行按钮之后，
            # 之前当个执行按钮已经下发执行的那个任务会再次被下发执行，而此时
            # 该任务的状态已经是正在执行而不是可执行了，所以通过判断这个任务状态，
            # 可以将这个已经提交的任务不再提交
            if task.task_status == Task_Status.EXECUTABLE:
                print('task_id: %s' % task.task_id)
                # 将其状态标记为正在执行
                task.task_status = Task_Status.RUNNING

                # 将每一个需要下发的任务解析并添加到下发任务队列
                    # 获取任务数据文件的存储位置
                taskDataPath = ''
                if (task.data_file_name != ''):
                    taskDataPath = os.path.join(app.config['UPLOADED_TASKDATAS_DEST'], task.data_file_name)
                    print('taskDataPath: %s' % taskDataPath)
                    taskSize = os.path.getsize(taskDataPath) >> 10  # 大小以 kb 为单位
                else:
                    taskSize = 0
                issue_task = {
                    'taskId': chr(task.task_id),
                    'taskSize': taskSize,
                    'taskDataPath': taskDataPath,
                }
                issue_task_queue.append(issue_task)

                try:
                    db.session.add(task)
                    db.session.commit()
                except Exception as err:
                    print('Modify task: %s status occurs error: %s' % (taskId, err))
                    db.session.rollback()
                    return jsonify({'status': -1})
    print('issueTask_deal: %s' % issue_task_queue)
    # 调用处理函数改变 socket_client 中 cmd_search 中 parseIssueTaskData 对应的数据
    parseIssueTaskQueue(issue_task_queue)
    # 通过 socket 与主控板通信，进行任务下发及结果接收
    updateModel(parseIssueTaskData, user_email=current_user.email)

    alive_tasks_queue, executable_len, running_len = query_construct_aliveTasks(current_user)
    alive_tasks_info  = {
        'alive_tasks_queue': alive_tasks_queue,
        'executable_len': executable_len,
        'running_len': running_len,
        'status': 0
    }

    return jsonify(alive_tasks_info)


def query_completed_tasks():
    # 首先从 User 模型中获取当前用户
    user = User.query.filter_by(email=current_user.email).first()
    # 从 Task 模型中找出当前用户所有已经执行完毕的任务
    tasks = Task.query.filter_by(user_task=user).order_by(Task.task_id.desc()).all()
    completed_tasks = []
    for task in tasks:
        if task.task_status == Task_Status.DONE:
            completed_tasks.append(task)
    completed_task_des_queue = []
    for completed_task in completed_tasks:
        # 任务名称
        # 格式： 任务类型 + '_' +  任务属性 + '_' + 任务数据文件名
        # 而任务数据文件名: 用户名 + '_' + 去掉非 ASCII 字符(如中文)的文件名 + '_' + 时间戳
        taskName = completed_task.type + '_' + completed_task.attr + ' ' + \
                   completed_task.data_file_name
        taskId = completed_task.task_id
        des = str(taskId) + '  : ' + taskName
        completed_task_des_queue.append((taskId, des))
    print('all completed tasks: %s' % completed_task_des_queue)
    return completed_task_des_queue


@main.route('/view-results')
def view_results():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        completed_task_des_queue = query_completed_tasks()
        viewResultsForm = ViewResultsForm(completed_task_des_queue=completed_task_des_queue,
                                          user_email=current_user.email)
        return render_template('view_results.html', viewResultsForm=viewResultsForm,
                               completed_tasks_len=len(completed_task_des_queue))


@main.route('/viewResults_deal', methods=['POST'])
def viewResutls_deal():
    task_id = request.values.get('task_id')
    task_id = int(task_id)
    print('Get task_id: %s in viewResults_deal function' % task_id)
    # 获取 task_id 指定的任务的原始数据文件和处理后的数据文件的 url，以便在用户界面展示
        # 从 Task 模型中找到由 taskId 指定的任务
    task = Task.query.filter_by(task_id=task_id).first()
    if task is not None and task.task_status == Task_Status.DONE:
        # 获取原始数据文件的文件名
        data_file_name = task.data_file_name
        # 生成原始数据文件的 url
        data_file_url = url_for('main.uploads_taskdatas', filename=data_file_name)
        print('origin_file_url: %s' % data_file_url)
        # 获取处理后的数据文件的文件名
        data_treated_file_name = task.data_treated_file_name
        # 生成处理后数据文件的 url
        data_treated_file_url = url_for('main.uploads_taskdatas', filename=data_treated_file_name)
        print('treated_file_url: %s' % data_treated_file_url)
        data_file_urls = {
            'file': data_file_url,
            'treated_file': data_treated_file_url,
            'status': 0
        }
        return jsonify(data_file_urls)
    else:
        return jsonify({'status': -1})


@main.route('/system-log')
def system_log():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        # 如果当前用户是管理员角色，则从 Task 模型中取出全部的任务(包括所有用户的)
        if current_user.is_Administrator():
            tasks = Task.query.order_by(Task.timestamp.desc()).all()
        # 否则只取出当前用户的所有任务
        else:
            tasks = Task.query.filter_by(user_task=current_user).order_by(Task.timestamp.desc()).all()
        # 构造系统日志队列
        system_log_queue = []
        for task in tasks:
            # 任务名称
            # 格式： 任务类型 + '_' +  任务属性 + '_' + 任务数据文件名
            # 而任务数据文件名: 用户名 + '_' + 去掉非 ASCII 字符(如中文)的文件名 + '_' + 时间戳
            taskName = task.type + '_' + task.attr + ' ' + \
                       task.data_file_name
            taskStatus = u'等待'
            if task.task_status == Task_Status.WAITING:
                taskStatus = u'等待'
            elif task.task_status == Task_Status.EXECUTABLE:
                taskStatus = u'可执行'
            elif task.task_status == Task_Status.RUNNING:
                taskStatus = u'正在执行'
            elif task.task_status == Task_Status.DONE:
                taskStatus = u'执行完毕'
            log = {
                'time': task.timestamp.strftime('%Y_%m_%d  %H:%M:%S'),
                'user': task.user_task.username,
                'task': taskName,
                'taskStatus': taskStatus
            }
            system_log_queue.append(log)
        return render_template('system_log.html', system_log_queue=system_log_queue, Task_Status=Task_Status)