# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash
from flask_login import current_user
from . import main
from ..models import CalBoard, StoreBoard, ControlBoard
from socket_client import updateModel
from socket_client import parseCalBoardData, parseStoreBoardData, parseControlBoardData


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
        categories.append(ctrlb.timestamp.strftime('%H:%M'))
    controlBoardsSplit.append(ctrlbDatas)
    controlBoardsSplit.append(categories)
    print(categories)
    return controlBoardsSplit


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


# @main.route('/monitoring-store')
# def monitoring_store():
#     if not current_user.is_authenticated:
#         return redirect(url_for('auth.login'))
#     else:
#         return render_template('monitoring_store.html')
#
#
# @main.route('/monitoring-control')
# def monitoring_control():
#     if not current_user.is_authenticated:
#         return redirect(url_for('auth.login'))
#     else:
#         return render_template('monitoring_control.html')


@main.route('/deploy-task')
def deploy_task():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        flash(u'欢迎！')
        return render_template('deploy_task.html')


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