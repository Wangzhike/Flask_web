# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, EqualTo
from wtforms import ValidationError
from ..models import User, Task, Task_Status
from flask_login import current_user


class AddtaskForm(FlaskForm):
    taskType = SelectField(u'任务模板', choices=[
            ('GrayTrans',u'灰度变换')
        ], validators=[DataRequired()])
    taskData = FileField(u'数据文件', validators=[
            FileRequired(u'文件未选择!')
        ])
    taskAttr = SelectField(u'任务属性', choices=[
            ('time', u'时间'), ('performance', u'性能')
        ], validators=[DataRequired()])


class SubmitTaskForm(FlaskForm):
    # hidden_tag = HiddenField()
    flag = HiddenField(render_kw={'id': 'tag', 'value': 0}, validators=[DataRequired()])
    submitTask = SubmitField(u'任务提交')


class ViewResultsForm(FlaskForm):
    completedTasks = SelectField(u'已完成任务', coerce=int)

    def __init__(self, *args, **kwargs):
        super(ViewResultsForm, self).__init__(*args, **kwargs)
        # 首先从 User 模型中获取当前用户
        user = User.query.filter_by(email=kwargs.get('user_email')).first()
        # print('user_email: %s in ViewResultsForm' % kwargs.get('user_email'))
        # print('completed_task_des_queue: %s in ViewResultsForm' % kwargs.get('completed_task_des_queue'))
        self.completedTasks.label.text = user.username + u' 已经完成的任务'
        self.completedTasks.choices = kwargs.get('completed_task_des_queue')

