# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, EqualTo
from wtforms import ValidationError


class AddtaskForm(FlaskForm):
    taskType = SelectField(u'任务模板', choices=[
            ('FFT',u'快速傅里叶变换'), ('Unknow', u'未知模板')
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
