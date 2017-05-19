# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash
from flask_login import current_user
from . import main
from ..models import CalBoard
from socket_client import updateCalBoardModel


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    else:
        flash(u'欢迎使用！')
        updateCalBoardModel()
        calBoards = CalBoard.query.order_by(CalBoard.name).all()
        return render_template('index.html', calBoards=calBoards)


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